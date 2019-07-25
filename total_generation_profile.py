# HASPR - High-Altitude Solar Power Research
# Script to calculate total generation profile per % of SA
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt
import sys

# PARAMETERS #
# path to .csv file containing Site ID in column 1, Surface Area (m2) in column 2:
surfaceAreaPath = "D:\\00_Results\\01_Water Body Selection\\Surface Areas.csv"
# directory containing individual site generation profiles (column 2) to sum (without leap days):
inputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 1 - Flat\\00 Total Profile Test In"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 1 - Flat\\01 Total Profile Test Out"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# desired output title:
outputTitle = "Total Expected Generation Profile"

# extract surface area data:
surface_areas = []  # index = Site ID - 1 (e.g. surface_areas[0] corresponds to Site 1)
sa_dataset = Dataset("SA")
haspr.get_csv_data(surfaceAreaPath, sa_dataset)
for p in sa_dataset.payload:
    surface_areas.append(float(p[1]))

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# cycle through files and create new result objects to dump to output directory:
times = []
total_output = []
times_set = False
for f in file_names:
    # get site ID:
    split = str.split(f, ' ')
    site_id = int(split[1])

    file_path = inputDirectory + haspr.osPathDelimiter + f

    # set time column:
    if not times_set:
        loaded_dataset = Dataset("temp")
        haspr.get_csv_data(file_path, loaded_dataset)
        for p in loaded_dataset.payload:
            times.append(str(p[0]))
        times_set = True

    # get site's generation:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    gen_values = extracted_array[:, 1]  # we only want generation values, not

    to_add = (gen_values * surface_areas[site_id - 1]) / 100

    for x in to_add:
        print(x)

    sys.exit(0)

    for p in loaded_dataset.payload:
        timestamp = str(p[0])
        if not timestamp.__contains__("-02-29T"):
            str_to_append = str(p[0]) + ", " + str(p[1])
            current_result.payload.append(str_to_append)  # only append if day != 29th of February
    results.append(current_result)

result = Result(outputTitle)
result.payload.append("Time, Generation [Wh]")