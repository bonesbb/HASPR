# HASPR - High-Altitude Solar Power Research
# Script to calculate costs given a .csv of sites, panel surface areas, and tilt angles
# Version 0.1
# Author: neyring

import haspr
from haspr import Result
from numpy import genfromtxt

# PARAMETERS #
# path to .csv file containing Site ID (column 1), panel surface area [m2] (column 2), and tilt angle [deg] (column 3):
inputPath = "D:\\00_Results\\06_Costs & Investment Profiles\\Input CSV - Flat Panels - 1 percent SA.csv"
# directory to write output to:
haspr.outputDirectory = "D:\\00_Results\\06_Costs & Investment Profiles\\Output"
# OS path delimiter ("\\" for windows, "/" for unix)"
haspr.osPathDelimiter = "\\"
# desired output title:
outputTitle = "Costs - Flat Panels - 1 percent SA"
# system lifetime in years:
lifetime = 25
# base price for capital costs [CHF/Wp]:
basePrice = 1.43
# angle cost factor for capital costs [CHF/Wp/deg]:
angleCostFactor = 0.0187
# O&M as percentage of capital costs per year [%]:
opsPercent = 2


# function to calculate cost per year for one site:
# @surface_area: surface area covered in panels [m2]
# @tilt_angle: panel tilt angle [deg]
# @return: list of costs for each year in lifetime
def get_yearly_costs(surface_area, tilt_angle):
    # get Wp rating of the site:
    watt_peak = 150 * surface_area

    # get initial capital costs:
    capital_costs = (basePrice + (angleCostFactor * tilt_angle)) * watt_peak
    yearly_o_and_m_costs = capital_costs * (opsPercent / 100)

    cost_per_year = [capital_costs]  # year 0

    # add O&M costs for each year in the system's lifetime:
    for j in range(lifetime):
        cost_per_year.append(yearly_o_and_m_costs)

    return cost_per_year


# get data from input CSV:
extracted_array = genfromtxt(inputPath, delimiter=',', skip_header=1)
site_ids = extracted_array[:, 0]
site_ids = site_ids.astype(int)  # convert float values to integers
panel_surface_areas = extracted_array[:, 1]
tilt_angles = extracted_array[:, 2]

yearly_costs = []
cumulative_costs = []

for i in range(len(site_ids)):
    # get costs per year:
    current_yearly_costs = get_yearly_costs(panel_surface_areas[i], tilt_angles[i])

    # get cumulative costs per year:
    current_cumulative_costs = []
    total_cost = 0
    for c in current_yearly_costs:
        total_cost = total_cost + c
        current_cumulative_costs.append(total_cost)

    # add costs to global lists:
    yearly_costs.append(current_yearly_costs)
    cumulative_costs.append(current_cumulative_costs)

# build result:
result = Result(outputTitle)
header = "Year"
for identifier in site_ids:
    header_to_append = ", Site {} - Cost [CHF], Site {} - Cumulative Cost [CHF]".format(identifier, identifier)
    header = header + header_to_append
result.payload.append(header)
for y in range(lifetime + 1):
    str_to_append = str(y)

    # add values for each site:
    for k in site_ids:
        yearly_costs_k = yearly_costs[k - 1]
        cumulative_costs_k = cumulative_costs[k - 1]

        str_to_append = str_to_append + ", " + str(yearly_costs_k[y])
        str_to_append = str_to_append + ", " + str(cumulative_costs_k[y])

    result.payload.append(str_to_append)

# dump result:
result.dump()
