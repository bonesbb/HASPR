# HASPR - High-Altitude Solar Power Research
# Script to calculate revenue profiles for all generation profiles in a given directory
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
from haspr import Dataset
import numpy as np
from numpy import genfromtxt

# PARAMETERS #
# path to .csv file of day-ahead prices (EUR/MWh, 1 year, UTC, 1h res, no leap days):
prices_path = "D:\\00_Results\\05_Revenue\\Processed Day-Ahead Price Datasets - no leap days\\1h" \
              "\\2018 Day-ahead Prices UTC - no leap days.csv"
# directory containing generation profiles (Wh, 1h res) to run our analyses on (without leap days):
inputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE" \
                 "\\1_1 Individual Total Expected Output - hourly"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE\\2 2018 Revenue"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
chf_eur_rate = 1.09  # CHF/EUR exchange rate (CHF per EUR)

# extract day-ahead price data (EUR/MWh):
prices = Dataset("prices")
haspr.get_csv_data(prices_path, prices)
timestamps = []
price_values = []
for p in prices.payload:
    timestamps.append(str(p[0]))
    price_values.append(float(p[1]))

price_values = np.array(price_values)  # use numpy for efficient element-wise calculations
price_values = np.multiply(price_values, chf_eur_rate)  # convert EUR to CHF

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# cycle through files and build result objects:
results = []
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f

    # get generation profile:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    gen_values = extracted_array[:, 1]  # we only want generation values

    # convert generation profile to MWh:
    gen_values = np.divide(gen_values, 1000000)

    # get bid revenue profile:
    remainder = np.mod(gen_values, 0.1)  # we want to round down to nearest 0.1 MW
    biddable_generation = gen_values - remainder
    biddable_generation = np.around(biddable_generation, decimals=1)  # correct for numerical errors

    bid_revenue = np.multiply(price_values, biddable_generation)

    # get potential revenue profile assuming no bid increment:
    potential_revenue = np.multiply(price_values, gen_values)

    # build current result object:
    result_title = f[0:len(f) - 4] + " - revenue"
    current_result = Result(result_title)
    current_result.payload.append("Time [UTC], Bid Revenue (0.1 MW Increment) [CHF],"
                                  " Unsold Power [MWh], Potential Revenue (no increment) [CHF]")
    for i in range(8760):
        str_to_append = str(timestamps[i]) + ", "
        str_to_append = str_to_append + str(bid_revenue[i]) + ", "
        str_to_append = str_to_append + str(remainder[i]) + ", "
        str_to_append = str_to_append + str(potential_revenue[i])
        current_result.payload.append(str_to_append)

    results.append(current_result)

# dump all results:
for r in results:
    r.dump()
