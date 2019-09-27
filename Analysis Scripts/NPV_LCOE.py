# HASPR - High-Altitude Solar Power Research
# Calculates the NPV and LCOE given lifetime costs/revenues and expected generation profiles
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Result
import numpy as np
from numpy import genfromtxt
import sys

# PARAMETERS #
# path to .csv file containing lifetime costs [CHF]:
costsPath = "D:\\00_Results\\06_Costs & Investment Profiles\\a_Lifetime Costs\\Break Even Test" \
            "\\Tracking - Break-even costs.csv"
# directory containing lifetime revenues [CHF]:
revenuesDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\b_Lifetime Revenue" \
                    "\\Case 2 - Tracking\\Lifetime Potential Revenue\\Individual Sites\\100 percent"
# directory containing yearly generation profiles [Wh]:
generationProfilesDirectory = "D:\\00_Results\\02_Generation Profiles\\Case 2 - Tracking" \
                              "\\0 Individual Expected Output - 100 percent SA"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\c_NPV & LCOE\\Break Even Test"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# desired output title:
outputTitle = "Break Even - Tracking"
# list of discount rates [%] to use for NPV and LCOE:
discountRates = [7, 8, 10]
# residual value of system as % of capital costs:
residualValuePercent = 10
# yearly panel degradation in percentage:
degradationPercent = 0.5


# function to get NPV and NPV break-even point given costs and revenue data
# @costs_array: = [capital costs, O&M costs year 1, O&M costs year 2, ...] in CHF
# @revenues_array: = [0 (construction year), revenue in year 1, revenue in year 2, ...] in CHF
# @discount_rate: discount rate to use [percentage]
# @return: [NPV in CHF, year of NPV break-even] -> note: if NPV does not break-even within lifetime, set to -1
def get_npv(costs_array, revenues_array, discount_rate):
    # get lifetime from costs_array:
    lifetime = len(costs_array) - 1

    capital_costs = costs_array[0]
    residual_value = (residualValuePercent / 100) * capital_costs

    # calculate discounted residual value:
    residual_discount_factor = (1 + (discount_rate / 100)) ** lifetime
    residual_term = residual_value / residual_discount_factor

    # calculate sum of discounted cash flows and year of NPV break-even:
    cash_flow_term = 0
    net_present_value = 0
    break_even_found = False
    break_even_year = -1
    for i in range(lifetime):
        # extract costs and revenues for the period in question (year = i+1 since i=0 is construction year):
        costs_i = costs_array[i + 1]
        revenues_i = revenues_array[i + 1]
        cash_flow_i = revenues_i - costs_i
        discount_factor_i = (1 + (discount_rate / 100)) ** (i + 1)
        cash_flow_term = cash_flow_term + (cash_flow_i / discount_factor_i)
        net_present_value = cash_flow_term - capital_costs
        # add residual value if we are in the last year of lifetime:
        if i == (lifetime - 1):
            net_present_value = net_present_value + residual_term
        # set break-even year if positive threshold has been crossed:
        if (not break_even_found) and (net_present_value > 0):
            break_even_found = True
            break_even_year = i + 1

    return [net_present_value, break_even_year]


# function to get LCOE for one site given costs and production data
# @yearly_production: total production in one year [kWh]
# @costs_array: = [capital costs, O&M costs year 1, O&M costs year 2, ...] in CHF
# @discount_rate: discount rate to use [percentage]
# @return: LCOE for the site in question [CHF/kWh]
def get_lcoe(yearly_production, costs_array, discount_rate):
    # get lifetime from costs_array:
    lifetime = len(costs_array) - 1

    # get discount factor:
    discount_factor = 1 + (discount_rate / 100)

    # get degradation factor:
    degradation_factor = 1 - (degradationPercent / 100)

    # calculate lifetime energy production [kWh]:
    lifetime_production = 0
    for i in range(lifetime):
        n = i + 1
        to_sum = yearly_production * (degradation_factor ** n) / (discount_factor ** n)
        lifetime_production = lifetime_production + to_sum

    # calculate lifetime costs [CHF]:
    capital_costs = costs_array[0]
    residual_value = capital_costs * (residualValuePercent / 100)
    yearly_o_and_m = costs_array[1]
    lifetime_costs = capital_costs
    for j in range(lifetime):
        m = j + 1
        discounted_o_and_m = yearly_o_and_m / (discount_factor ** m)
        discounted_residual_value = residual_value / (discount_factor ** m)
        to_sum = discounted_o_and_m - discounted_residual_value  # subtract discounted residual value!
        lifetime_costs = lifetime_costs + to_sum

    to_return = lifetime_costs / lifetime_production
    return to_return


# get all file names in generation profiles directory:
generation_file_names = []
for (dirpath, dirnames, filenames) in walk(generationProfilesDirectory):
    generation_file_names.extend(filenames)

# get all file names in revenues directory:
revenues_file_names = []
for (dirpath, dirnames, filenames) in walk(revenuesDirectory):
    revenues_file_names.extend(filenames)

# initialize result header and rows:
result_header = "Site ID"
for d in discountRates:
    result_header = result_header + ", NPV (CHF) [discount = " + str(d) + "%]"
    result_header = result_header + ", NPV break-even year [discount = " + str(d) + "%]"
for r in discountRates:
    result_header = result_header + ", LCOE (CHF/kWh) [discount = " + str(r) + "%]"

result_rows = []

extracted_costs = genfromtxt(costsPath, delimiter=',', skip_header=1)  # matrix of all cost data

# cycle through files (1 per ID) and calculate results:
for f in generation_file_names:
    file_path = generationProfilesDirectory + haspr.osPathDelimiter + f

    # get site ID:
    split = f.split(" ")
    site_id = int(split[1])

    # get yearly generation in kWh:
    extracted_array = genfromtxt(file_path, delimiter=',', skip_header=1)
    gen_values = extracted_array[:, 1]
    yearly_generation = np.sum(gen_values) / 1000  # in kWh

    # extract yearly costs for site in question:
    column_number = (2 * (site_id - 1)) + 1  # based on our Site ID convention
    site_costs = extracted_costs[:, column_number]  # = [capital cost, O&M cost year 1, O%M cost year 2, ...]

    # extract yearly revenues for site in question:
    # cycle through revenues files to find the corresponding data:
    site_revenues = []
    for rev in revenues_file_names:
        # get ID:
        rev_split = rev.split(" ")
        rev_id = int(rev_split[1])
        if rev_id == site_id:
            rev_file_path = revenuesDirectory + haspr.osPathDelimiter + rev
            # extract revenue data:
            extracted_rev = genfromtxt(rev_file_path, delimiter=',', skip_header=1)
            site_revenues = extracted_rev[:, 1]
            break

    # make sure data was extracted:
    if len(site_revenues) == 0:
        print("[ERROR] Failed to extract revenue data...")
        sys.exit(-2)

    # get NPV for each discount rate:
    npv_list = []
    for r in discountRates:
        npv = get_npv(site_costs, site_revenues, r)
        npv_list.append(npv)

    # get LCOE for each discount rate:
    lcoe_list = []
    for d in discountRates:
        lcoe = get_lcoe(yearly_generation, site_costs, d)
        lcoe_list.append(lcoe)

    # build result row for current site ID:
    current_row = str(site_id)
    for n_i in npv_list:
        current_row = current_row + ", " + str(n_i[0]) + ", " + str(n_i[1])
    for l in lcoe_list:
        current_row = current_row + ", " + str(l)

    # add current row to overview result:
    result_rows.append(current_row)

# build & dump result object:
result = Result(outputTitle)
result.payload.append(result_header)
for r in result_rows:
    result.payload.append(r)
result.dump()
