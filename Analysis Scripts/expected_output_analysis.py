# HASPR - High-Altitude Solar Power Research
# Script to calculate aggregate lower bounds and historic variance given a directory of individual expected output
# Version 0.1
# Author: neyring

import numpy as np
from numpy import genfromtxt
from os import walk
import haspr
from haspr import Result

# Parameters #
# directory containing individual expected outputs:
inputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 1 - Flat\\0 Individual Expected Output"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\Out"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# sum lower bound and historic variance at each timestep
lower_bound = np.zeros(17520)
historic_variance = np.zeros(17520)
normalized_variance = np.zeros(17520)
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    lb_values = extracted_array[:, 2]
    hist_var_values = extracted_array[:, 3]
    norm_var_values = extracted_array[:, 4]

    lower_bound = np.add(lower_bound, lb_values)
    historic_variance = np.add(historic_variance, hist_var_values)
    normalized_variance = np.add(normalized_variance, norm_var_values)

# dump results
result = Result("Lower Bound & Variances")
result.payload.append("Lower Bound, Historic Variance, Normalized Variance")
for i in range(17520):
    str_to_append = str(lower_bound[i]) + ", " + str(historic_variance[i]) + ", " + str(normalized_variance[i])
    result.payload.append(str_to_append)
result.dump()
