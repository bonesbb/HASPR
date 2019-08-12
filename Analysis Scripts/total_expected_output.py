# HASPR - High-Altitude Solar Power Research
# Script to calculate generation profiles in Wh from a directory of generation profiles in [Wh/m2]
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt

# PARAMETERS #
# directory containing generation profiles in [Wh/m2]:
inputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE\\0 Individual Expected Output - per m2"
# path to .csv file containing site ID (column 1), panel surface area [m2] (column 2):
surfaceAreaPath = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE\\Surface Area CSV - 1 percent SA.csv"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE" \
                        "\\1 Individual Total Expected Output"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# extract surface area data:
extracted = genfromtxt(surfaceAreaPath, delimiter=',', skip_header=1)
surface_area_dict = {}
for x in extracted:
    s_id = int(x[0])
    s_SA = float(x[1])
    surface_area_dict[s_id] = s_SA

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# cycle through files and create new result objects to dump to output directory:
results = []
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f

    # extract timestamps:
    file_dataset = Dataset("temp")
    haspr.get_csv_data(file_path, file_dataset)
    timestamps = []
    for p in file_dataset.payload:
        timestamps.append(str(p[0]))

    # extract generation profile:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    gen_values = extracted_array[:, 1]

    # get panel surface area:
    split = f.split(" ")
    site_id = int(split[1])
    site_SA = surface_area_dict.get(site_id)

    gen_values = np.multiply(gen_values, site_SA)

    # build current result object:
    result_title = f[0:len(f) - 4] + " - [Wh]"
    current_result = Result(result_title)
    current_result.payload.append(" Time (UTC), Generation [Wh]")
    for i in range(len(extracted_array)):
        str_to_append = str(timestamps[i]) + ", " + str(gen_values[i])
        current_result.payload.append(str_to_append)

    results.append(current_result)

# dump all results:
for r in results:
    r.dump()
