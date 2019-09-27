# HASPR - High-Altitude Solar Power Research
# Script to calculate total generation profile given surface areas
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt

# PARAMETERS #
# path to .csv file containing Site ID in column 1, Surface Area (m2) in column 2:
surfaceAreaPath = "D:\\00_Results\\01_Water Body Selection\\Surface Areas\\Surface Areas - 100 percent.csv"
# directory containing individual site generation profiles (column 2) to sum (without leap days):
inputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 5 - 30 to 65 deg winter opt" \
                 "\\0 Individual Expected Output - per m2"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 5 - 30 to 65 deg winter opt" \
                        "\\1 Total Expected Output"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# desired output title:
outputTitle = "Total Expected Generation Profile - 100 percent SA"

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

# cycle through file and iteratively add output to total:
times = []
total_output = np.zeros(17520)  # temporal resolution = 30 minutes
times_set = False
total_files = len(file_names)
counter = 0
for f in file_names:
    counter = counter + 1
    print("Processing file {} of {}...".format(counter, total_files))
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
    gen_values = extracted_array[:, 1]  # we only want generation values

    to_add = (gen_values * surface_areas[site_id - 1])

    total_output = total_output + to_add  # element-wise addition of numpy arrays

# build result:
result = Result(outputTitle)
result.payload.append("Time, Generation [Wh]")
for i in range(17520):
    str_to_append = str(times[i]) + ", " + str(total_output[i])
    result.payload.append(str_to_append)

# dump result:
result.dump()
