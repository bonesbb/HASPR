# HASPR - High-Altitude Solar Power Research
# Script to determine optimum fixed-tilt positions given directories of brute force output
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset

# PARAMETERS #
# directory containing all batch output folders for a given optimization:
inputDirectory = "E:\\O2 Results"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\Out"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# maximum site ID (we assume they start at 1 and with unit increments):
maxId = 82
# title of output:
outputTitle = "O2 Position Results"

# get all batch output folders:
dir_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    dir_names.extend(dirnames)

# cycle through all files and extract overview files:
overview_file_paths = []
for d in dir_names:
    inner_directory_path = inputDirectory + haspr.osPathDelimiter + d
    file_names = []
    for (dirpath, dirnames, filenames) in walk(inner_directory_path):
        file_names.extend(filenames)

    for f in file_names:
        if "Fixed Generation Overview" in f:
            path_to_append = inner_directory_path + haspr.osPathDelimiter + f
            overview_file_paths.append(path_to_append)

# dict to collect maximum values:
max_values = {}  # format: key = site ID, value = [total opt position, total value, winter opt position, winter value]

# initialize max_values:
for i in range(1, maxId + 1):
    max_values[i] = ["", 0, "", 0]

for f in overview_file_paths:
    # get tilt position:
    split = f.split("\\")
    file_name = split[len(split) - 1]
    position = file_name.split(" ")
    position = position[0]

    # read data from CSV:
    overview_data = Dataset("overview")
    haspr.get_csv_data(f, overview_data)
    site_id = int(overview_data.payload[0][0])
    total_production = float(overview_data.payload[0][3])
    winter_production = float(overview_data.payload[0][4])

    # update maximum values:
    current_max = max_values[site_id]
    if total_production > current_max[1]:
        current_max[0] = position
        current_max[1] = total_production
        max_values[site_id] = current_max
    if winter_production > current_max[3]:
        current_max[2] = position
        current_max[3] = winter_production
        max_values[site_id] = current_max

# build result:
result = Result(outputTitle)
result.payload.append("Site ID, Opt Az Total, Opt Tilt Total, Opt Az Winter, Opt Tilt Winter")
for i in range(1, maxId + 1):
    site_values = max_values[i]
    total_opt_pos = site_values[0]
    total_opt_pos = total_opt_pos.split("-")
    winter_opt_pos = site_values[2]
    winter_opt_pos = winter_opt_pos.split("-")
    str_to_append = str(i) + "," + str(total_opt_pos[0]) + "," + str(total_opt_pos[1]) + ","
    str_to_append = str_to_append + str(winter_opt_pos[0]) + "," + str(winter_opt_pos[1])
    result.payload.append(str_to_append)

result.dump()
