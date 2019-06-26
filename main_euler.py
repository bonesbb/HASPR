# HASPR - High-Altitude Solar Power Research
# Main script for Euler - set parameters, run models, and dump data
# Version 0.3
# Author: neyring

import datetime
import pytz
import haspr

# PARAMETERS #

modelsToRun = ["POA_fixed"]
haspr.osPathDelimiter = "/"
haspr.usableSurface = 0.4  # fraction of water body surface area which can be used
haspr.fixedPanelSweepIncrement = 90  # in degrees
haspr.set_coordinates("/cluster/home/neyring/coordinates of interest2.csv")  # .csv file path of coordinates
#haspr.set_sites("D:\\sites.csv")  # .csv file path of sites (incl. surface area)
haspr.sisDataPath = "/cluster/home/neyring/00_2017_SIS_merged.nc"  # path to SIS dataset
haspr.sisdDataPath = "/cluster/home/neyring/01_2017_SIS_direct_merged.nc"  # path to SIS direct dataset
haspr.salDataPath = "/cluster/home/neyring/02_SAL_merged.nc"  # path to surface albedo dataset
#haspr.sisnDataPath = "D:\\POA Datasets\\03_2017_SIS_normal_merged.nc"  # path to SIS normal dataset
#haspr.demDataPath = "D:\\swiss_dem_2018.csv"  # path to SwissGrid demand data
#haspr.generationProfilesDirectory = "D:\\HASPR Flat Output\\Flat Generation Profiles"  # path to gen. profiles directory

# solar development pipeline parameters:
haspr.sdp_developmentPhases = ["Proposal", "Term Sheet", "Negotiation", "PPA"]
haspr.sdp_transitionProbabilities = [0.05, 0.3, 0.5, 0.75]

generateOutputReport = False
haspr.outputDirectory = "/cluster/home/neyring/HASPR Output"  # results and output directory
outputTime = "UTC"  # set to "UTC" or "LOCAL" (limited functionality for local time)
consoleBreak = "\n***************************************************************************\n"

# --SCRIPT BEGINS-- #

# to use the tool on a global scale, all times are converted to UTC
dateStart = datetime.datetime.now(pytz.utc)

print(consoleBreak)
print("--- Launching HASPR | High-Altitude Solar Power Research ---\n")
haspr.initialize()
print("-> {} models available\n".format(len(haspr.models)))
print("Script started at {} UTC".format(dateStart))
print(consoleBreak)

print("\nCoordinates set -> {} sites of interest".format(len(haspr.coordinates)))

# get model objects to run
modelObjects = []
for m in haspr.models:
    for um in modelsToRun:
        if um == m.name:
            modelObjects.append(m)
            break

# load necessary data
haspr.get_data(modelObjects)
print("-> All datasets loaded.")

# run models
print("Preparing batch models...")
print("Executing:")

haspr.run_models(modelObjects)

print("Models successfully executed.")
print("Preparing output...")

# dump output to disk
print("Dumping data to local disk...")
haspr.dump_results(modelObjects)

print("Data dump complete.")

# create output report
print("Writing output report to disk...")

haspr.write_output_report()

print(consoleBreak)

dateFinish = datetime.datetime.now(pytz.utc)

print("HASPR successfully terminated at {} UTC".format(dateFinish))

run_time = dateFinish - dateStart

print(" -> total runtime = {}".format(run_time))

print(consoleBreak)
