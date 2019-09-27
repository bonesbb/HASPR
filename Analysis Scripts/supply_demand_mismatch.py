# HASPR - High-Altitude Solar Power Research
# Script to get alleviation of supply/demand mismatch given generation profiles
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
from numpy import genfromtxt

# PARAMETERS #
# path to .csv file of supply/demand mismatch data (Wh, UTC, 30min res, no leap days):
mismatchPath = "D:\\00_Results\\03_Supply Demand Mismatch\\5_2018 Mismatch - 30min res - UTC time.csv"
# directory containing generation profiles (30min res, Wh) to run our analyses on (without leap days):
inputDirectory = "D:\\00_Results\\03_Supply Demand Mismatch\\In"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\03_Supply Demand Mismatch\\Case 5 - 30 to 65 deg winter opt"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# extract mismatch data:
mismatch = Dataset("mismatch")
haspr.get_csv_data(mismatchPath, mismatch)
timestamps = []
mismatch_values = []
for p in mismatch.payload:
    timestamps.append(str(p[0]))
    mismatch_values.append(float(p[1]))

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

    # calculate import offset:
    current_import_offset = []
    for i in range(17520):
        total_import = (-1) * mismatch_values[i]  # -ve value for mismatch => import
        generation = gen_values[i]
        import_offset = 0.0
        if total_import > 0:
            import_offset = min(generation, total_import)  # can't offset more than total imports
        current_import_offset.append(import_offset)

    # build current result object:
    result_title = f[0:len(f) - 4] + " - import offset"
    current_result = Result(result_title)
    current_result.payload.append("Time (UTC), Reduction in Imports [Wh]")
    for j in range(17520):
        str_to_append = str(timestamps[j]) + ", " + str(current_import_offset[j])
        current_result.payload.append(str_to_append)

    results.append(current_result)

# dump all results:
for r in results:
    r.dump()
