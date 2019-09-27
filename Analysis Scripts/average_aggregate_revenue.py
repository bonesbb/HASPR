# HASPR - High-Altitude Solar Power Research
# Script which outputs the average bid and potential revenue given a directory of aggregate revenue profiles
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt

# PARAMETERS #
# directory containing all time series to average:
inputDirectory = "D:\\00_Results\\05_Revenue\\Case 2 - Tracking - Old\\To Average"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\05_Revenue\\Case 2 - Tracking - Old\\Averages"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# title of output file:
outputTitle = "100 percent SA - import offset"

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# set timestamps:
path_for_ds = inputDirectory + haspr.osPathDelimiter + file_names[0]
ds = Dataset("timestamps")
haspr.get_csv_data(path_for_ds, ds)
timestamps = []
for p in ds.payload:
    timestamps.append(str(p[0]))

# cycle through files and sum values:
average_bid_revenue = np.zeros(8760)
average_potential_revenue = np.zeros(8760)
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f

    # extract revenue values:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    bid_revenue = extracted_array[:, 1]
    potential_revenue = extracted_array[:, 3]

    average_bid_revenue = np.add(average_bid_revenue, bid_revenue)
    average_potential_revenue = np.add(average_potential_revenue, potential_revenue)

# element-wise division to determine average:
average_bid_revenue = np.true_divide(average_bid_revenue, len(file_names))
average_potential_revenue = np.true_divide(average_potential_revenue, len(file_names))

# build and dump result
result = Result(outputTitle)
result.payload.append("Time, Average Bid Revenue (CHF), Average Potential Revenue (CHF)")
for i in range(8760):
    str_to_append = str(timestamps[i]) + "," + str(average_bid_revenue[i]) + "," + str(average_potential_revenue[i])
    result.payload.append(str_to_append)

result.dump()
