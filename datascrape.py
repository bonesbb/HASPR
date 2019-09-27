# HASPR - High-Altitude Solar Power Research
# Script to extract light-weight data sets and merge files from large NETCDF4 directories
# Version 0.3
# Author: neyring

import haspr
import datetime
import sys

# PARAMETERS #
mode = "merge"  # "extract" for tar extraction, "merge" for merging directory
haspr.osPathDelimiter = "\\"  # "/" for unix, "\\" for windows
varName = "sal"  # NETCDF name of the variable of interest. Note: CMSAF names = "SIS", "SID", "sal"
inputTarDirectory = "D:\\SIS Test"  # Directory of .tar files to extract from (only for "extract" mode)
outputDirectory = "D:\\Datascrape"  # Directory to write output files to (only for "extract" mode)
mergeDirectory = "D:\\POA Datasets\\SAL 2006-2015"  # Directory of files to merge (only for "merge" mode)
minLongitude = 5.85  # Swiss min=5.9 (Note: only for "extract" mode)
maxLongitude = 10.6  # Swiss max=10.55 (Note: only for "extract" mode)
minLatitude = 45.75  # Swiss min=45.8 (Note: only for "extract" mode)
maxLatitude = 47.9  # Swiss max=47.85 (Note: only for "extract" mode)

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
