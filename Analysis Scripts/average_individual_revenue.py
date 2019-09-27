# HASPR - High-Altitude Solar Power Research
# Script which averages individual revenue profiles from historic data
# Note: also outputs aggregated revenue
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt

# PARAMETERS #
# directory containing yearly folders to average from:
inputDirectory = "D:\\00_Results\\05_Revenue\\Case 5 - 30 to 65 deg winter opt\\1 - Import Offset\\Hist"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\05_Revenue\\Case 5 - 30 to 65 deg winter opt\\1 - Import Offset\\Averages"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"

# get historic yearly directories:
years = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    years.extend(dirnames)

first_year_path = inputDirectory + haspr.osPathDelimiter + years[0]
file_names = []
for (dirpath, dirnames, filenames) in walk(first_year_path):
    file_names.extend(filenames)

# set timestamps:
path_for_ds = first_year_path + haspr.osPathDelimiter + file_names[0]
ds = Dataset("timestamps")
haspr.get_csv_data(path_for_ds, ds)
timestamps = []
for p in ds.payload:
    timestamps.append(str(p[0]))

# initialize average arrays:
file_dict = {}
for f in file_names:
    file_dict[f] = [np.zeros(8760), np.zeros(8760), np.zeros(8760)]  # [bid, unsold, potential]

# cycle through years and add value to arrays:
for y in years:
    for fn in file_names:
        file_path = inputDirectory + haspr.osPathDelimiter + y + haspr.osPathDelimiter + fn

        # extract data:
        extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
        bid_revenue = extracted_array[:, 1]
        unsold_power = extracted_array[:, 2]
        potential_revenue = extracted_array[:, 3]

        current_values = file_dict[fn]
        current_bid_sum = current_values[0]
        current_unsold_sum = current_values[1]
        current_potential_sum = current_values[2]

        # element-wise addition:
        current_bid_sum = np.add(current_bid_sum, bid_revenue)
        current_unsold_sum = np.add(current_unsold_sum, unsold_power)
        current_potential_sum = np.add(current_potential_sum, potential_revenue)

        # update global values:
        file_dict[fn] = [current_bid_sum, current_unsold_sum, current_potential_sum]

# divide by number of years and set results:
results = []
total_bid_revenue = np.zeros(8760)
total_unsold_power = np.zeros(8760)
total_potential_revenue = np.zeros(8760)
for fi in file_names:
    summed_values = file_dict[fi]
    summed_bid = summed_values[0]
    summed_unsold = summed_values[1]
    summed_potential = summed_values[2]

    # element-wise division:
    average_bid = np.true_divide(summed_bid, len(years))
    average_unsold = np.true_divide(summed_unsold, len(years))
    average_potential = np.true_divide(summed_potential, len(years))

    # add averages to total values:
    total_bid_revenue = np.add(total_bid_revenue, average_bid)
    total_unsold_power = np.add(total_unsold_power, average_unsold)
    total_potential_revenue = np.add(total_potential_revenue, average_potential)

    # build result:
    current_result = Result(fi)
    current_result.payload.append("Time, Average Bid Revenue (CHF), Unsold Power (MWh),"
                                  " Average Potential Revenue (CHF)")
    for i in range(8760):
        str_to_append = str(timestamps[i]) + "," + str(average_bid[i]) + ","
        str_to_append = str_to_append + str(average_unsold[i]) + ","
        str_to_append = str_to_append + str(average_potential[i])
        current_result.payload.append(str_to_append)

    results.append(current_result)

# build total result:
total_result = Result("0 - Aggregated Revenue Values")
total_result.payload.append("Time, Total Bid Revenue (CHF), Total Unsold Power (MWh), Total Potential Revenue (CHF)")
for j in range(8760):
    str_to_append = str(timestamps[j]) + "," + str(total_bid_revenue[j]) + ","
    str_to_append = str_to_append + str(total_unsold_power[j]) + ","
    str_to_append = str_to_append + str(total_potential_revenue[j])
    total_result.payload.append(str_to_append)

results.append(total_result)

# dump all results:
for r in results:
    r.dump()
