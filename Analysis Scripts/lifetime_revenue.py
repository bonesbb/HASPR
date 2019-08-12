# HASPR - High-Altitude Solar Power Research
# Calculates yearly and cumulative revenue for system lifetime given a directory of revenue profiles
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
import numpy as np
from numpy import genfromtxt
import sys

# PARAMETERS #
# directory containing individual revenue profiles (1h, CHF):
inputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE\\2 2018 Revenue"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE\\3 Lifetime Revenues"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# revenue to sum -> "bid" for bid revenue, "potential" for total potential revenue:
revenueToSum = "potential"
# system lifetime in years:
lifetime = 25
# yearly panel degradation in percentage:
degradationPercent = 0.5

# get all file names in inputDirectory:
file_names = []
for (dirpath, dirnames, filenames) in walk(inputDirectory):
    file_names.extend(filenames)

# cycle through files and create new result objects to dump to output directory:
results = []
for f in file_names:
    file_path = inputDirectory + haspr.osPathDelimiter + f

    # extract revenue data:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    revenue_values = []
    if revenueToSum == "bid":
        revenue_values = extracted_array[:, 1]
    elif revenueToSum == "potential":
        revenue_values = extracted_array[:, 3]
    else:
        print("[ERROR] Revenue to sum parameter is invalid...")
        sys.exit(-1)

    # get lifetime revenue:
    yearly_revenue = np.sum(revenue_values)
    lifetime_yearly_revenue = [0]  # year 0 is assumed to be the construction year (only capital costs)
    temp_revenue = yearly_revenue
    for y in range(lifetime):
        temp_revenue = (1 - (degradationPercent / 100)) * temp_revenue
        lifetime_yearly_revenue.append(temp_revenue)

    # get cumulative revenue per year:
    lifetime_cumulative_revenue = []
    total_revenue = 0
    for r in lifetime_yearly_revenue:
        total_revenue = total_revenue + r
        lifetime_cumulative_revenue.append(total_revenue)

    # build current result object:
    result_title = f[0:len(f) - 4] + " - lifetime revenue"
    current_result = Result(result_title)
    current_result.payload.append("Year, Revenue [CHF], Cumulative Revenue [CHF]")
    for i in range(len(lifetime_yearly_revenue)):
        str_to_append = str(i) + ", " + str(lifetime_yearly_revenue[i]) + ", " + str(lifetime_cumulative_revenue[i])
        current_result.payload.append(str_to_append)

    results.append(current_result)

# dump all results:
for res in results:
    res.dump()
