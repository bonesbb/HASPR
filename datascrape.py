# HASPR - High-Altitude Solar Power Research
# Datascrape script - extract light-weight dataset for haspr input
# Version 0.1
# Author: neyring

import haspr
import datetime
import sys

# PARAMETERS #
varName = "SIS"
inputTarDirectory = "D:\\SIS Test"
outputDirectory = "D:\\Datascrape"
mergeDirectory = "D:\\Merge"
minLongitude = 5.85  # Swiss min=5.9
maxLongitude = 10.6  # Swiss max=10.55
minLatitude = 45.75  # Swiss min=45.8
maxLatitude = 47.9  # Swiss max=47.85
mode = "merge"  # "extract" for tar extraction, "merge" for merging directory

# --SCRIPT BEGINS-- #
dateStart = datetime.datetime.now()

if mode == "extract":
    print("\nLaunching HASPR datascrape extraction for {} variable...".format(varName))
    print(" -> script started at {}".format(dateStart))
    haspr.extract_from_tar(inputTarDirectory, outputDirectory, varName,
                           minLongitude, maxLongitude, minLatitude, maxLatitude)
elif mode == "merge":
    print("\nLaunching HASPR datascrape merge on {} directory.".format(mergeDirectory))
    print(" -> script started at {}".format(dateStart))
    haspr.merge_netcdf(mergeDirectory, varName)
else:
    print("[ERROR] {} is not a valid datascrape mode...".format(mode))
    sys.exit(-1)

dateFinish = datetime.datetime.now()

print("\nDatascrape successfully terminated at {}".format(dateFinish))
