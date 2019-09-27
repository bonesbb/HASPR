# HASPR - High-Altitude Solar Power Research
# Script to calculate annual sums given generation profiles
# Version 0.1
# Author: neyring

import haspr
from haspr import Result
from numpy import genfromtxt
from os import walk
import numpy as np

# PARAMETERS #
# path to directory containing generation profiles to sum individually:
inputDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 1 - Flat" \
                 "\\0 Individual Expected Output - per m2"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\Out"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# cycle through files and build result array:
result_array = []
generation_file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    generation_file_names.extend(filenames)

for f in generation_file_names:
    path = inputDirectory + haspr.osPathDelimiter + f
    extracted_data = genfromtxt(path, delimiter=',', skip_header=1)
    gen_values = extracted_data[:, 1]
    summed = np.sum(gen_values)
    split = f.split(" ")
    result_str = split[1] + "," + str(summed)
    result_array.append(result_str)

# build result:
result = Result("Individual Sums")
result.payload.append("Profile,Total Output per m2")
for r in result_array:
    result.payload.append(r)
result.dump()
