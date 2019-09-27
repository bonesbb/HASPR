# HASPR - High-Altitude Solar Power Research
# Script to calculate CO2-equivalent offset given generation profiles
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt

# PARAMETERS #
# path to .csv file of grid CI data (Wh, UTC, 1h res, no leap days):
ciPath = "D:\\00_Results\\04_CO2 Offset\\1_Swiss Grid CI - 1h - UTC.csv"
# directory containing generation profiles (1h res, Wh) to run our analyses on (without leap days):
inputDirectory = "D:\\00_Results\\Out"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\04_CO2 Offset\\Case 5 - 30 to 65 deg winter opt"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# extract carbon intensity data:
ci = Dataset("ci")
haspr.get_csv_data(ciPath, ci)
timestamps = []
ci_values = []
for p in ci.payload:
    timestamps.append(str(p[0]))
    ci_values.append(float(p[1]))

ci_values = np.array(ci_values)  # use numpy for efficient element-wise calculations

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# cycle through files and build result objects:
results = []
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f

    # get generation profile:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    gen_values = extracted_array[:, 1]  # we only want generation values

    # get carbon offset for current generation profile:
    carbon_offset = np.multiply(ci_values, gen_values)

    # build current result object:
    result_title = f[0:len(f) - 4] + " - CO2-eq offset"
    current_result = Result(result_title)
    current_result.payload.append("Time [UTC], CO2-eq offset [g]")
    for i in range(8760):
        str_to_append = str(timestamps[i]) + ", " + str(carbon_offset[i])
        current_result.payload.append(str_to_append)

    results.append(current_result)

# dump all results:
for r in results:
    r.dump()
