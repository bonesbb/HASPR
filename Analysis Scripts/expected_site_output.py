# HASPR - High-Altitude Solar Power Research
# Script to calculate expected output for a given site
# Version 0.1
# Author: neyring

import numpy as np
from numpy import genfromtxt
from os import walk
from scipy import stats
import datetime
import haspr
from haspr import Result
import sys

# Parameters #
# directory containing historic .csv generation profiles (without leap days):
inputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 1 - Flat\\Site 82 - Historic Profiles wo leap"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 1 - Flat"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# title for result group:
resultGroupTitle = "Site 82 - Flat"

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# get all generation profiles as numpy arrays:
profiles = []
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    gen_values = extracted_array[:, 1]  # we only want generation values, not timestamp
    # check for duplicates:
    for p in profiles:
        if np.array_equal(gen_values, p):
            print("Duplicate found: {}".format(f))
            sys.exit(-1)
    profiles.append(gen_values)

# Calculate expected value (average):
average = np.average(profiles, axis=0)

# Calculate variance and standard deviation:
variance = np.var(profiles, axis=0)
std = np.sqrt(variance)

# Calculate normalized variance (variance/expected output):
normalized_variance = []
for i in range(17520):
    to_append = 0
    if average[i] > 0:  # make sure we don't divide by zero!
        to_append = variance[i] / average[i]
    normalized_variance.append(to_append)

# Get noise lower bound at 95% confidence:
noise_lower_bound = []
for s in std:
    lower_bound = 0
    if s > 0:
        bounds = stats.norm.interval(0.95, loc=0, scale=s)
        lower_bound = bounds[0]
    noise_lower_bound.append(lower_bound)

# Generate CSV output #
# establish timestamps:
start_date = datetime.datetime(2017, 1, 1, 0)  # we use 2017 as a generic non-leap year for output & plots
datetime_axis = [start_date + datetime.timedelta(minutes=(x*30)) for x in range(17520)]

# create Result object to dump:
expected_output_result = Result(resultGroupTitle + " Expected Output")
expected_output_result.payload.append("Time, Expected Generation [Wh/m2], Min. Output at 95% Confidence [Wh/m2], "
                                      "Historic Variance, Historic Normalized Variance")
for i in range(17520):
    str_to_write = str(datetime_axis[i]) + ", " + str(average[i]) + ", "
    lower_bound = max(average[i] + noise_lower_bound[i], 0)  # addition since lower bound is negative, min = 0
    str_to_write = str_to_write + str(lower_bound) + ", "
    str_to_write = str_to_write + str(variance[i]) + ", "
    str_to_write = str_to_write + str(normalized_variance[i])
    expected_output_result.payload.append(str_to_write)
expected_output_result.dump()
