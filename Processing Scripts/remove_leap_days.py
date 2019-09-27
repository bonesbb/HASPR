# HASPR - High-Altitude Solar Power Research
# Script to remove leap days from a directory of generation profiles
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset

# Parameters #
# directory containing generation profiles to remove leap days from:
inputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 3 - 12 deg tilt total opt\\Site 28 - Historic Profiles"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 3 - 12 deg tilt total opt" \
                        "\\Site 28 - Historic Profiles wo leap"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# cycle through files and create new result objects to dump to output directory:
results = []
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f
    loaded_dataset = Dataset("temp")
    haspr.get_csv_data(file_path, loaded_dataset)
    result_title = f[0:len(f)-4]  # remove the ".csv" since this gets added by the Result class
    current_result = Result(result_title)
    current_result.payload.append("Time, Generation [Wh/m2]")
    for p in loaded_dataset.payload:
        timestamp = str(p[0])
        if not timestamp.__contains__("-02-29T"):
            str_to_append = str(p[0]) + ", " + str(p[1])
            current_result.payload.append(str_to_append)  # only append if day != 29th of February
    results.append(current_result)

# dump data to output directory:
for r in results:
    r.dump()
