# HASPR - High-Altitude Solar Power Research
# Script to get hourly, daily, or monthly resolution data series
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Dataset
import sys

# Parameters #
# directory containing data series to convert to lower resolution:
inputDirectory = "D:\\00_Results\\In"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\Out"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# desired temporal resolution of output ("H" - hourly, "D" - daily, "M" - monthly):
desiredResolution = "M"

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
    if desiredResolution == "H":
        res = haspr.get_hourly_profile(result_title, loaded_dataset)
    elif desiredResolution == "D":
        res = haspr.get_daily_profile(result_title, loaded_dataset)
    elif desiredResolution == "M":
        res = haspr.get_monthly_profile(result_title, loaded_dataset)
    else:
        print("[ERROR] desired resolution '{}' not found...".format(desiredResolution))
        sys.exit(-1)
    results.append(res)

# dump data to output directory:
for r in results:
    r.dump()
