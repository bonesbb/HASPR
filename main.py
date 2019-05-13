# HASPR - High-Altitude Solar Power Research
# Main script - set parameters, run models, and dump data
# Version 0.1
# Author: neyring

import datetime
import pytz
import haspr

# PARAMETERS #

modelsToRun = ["SIS"]
haspr.set_coordinates("D:\\coordinates of interest.csv")  # .csv file path of coordinates
haspr.sisDataPath = "D:\\00_SIS_merged.nc"  # path to SIS dataset
haspr.sisdDataPath = ""  # path to SIS direct dataset
haspr.salDataPath = ""  # path to surface albedo dataset
haspr.temporalResolution = 30  # model resolution in minutes
haspr.spatialResolution = 0.05  # resolution of datasets in degrees

# solar development pipeline parameters:
haspr.sdp_developmentPhases = ["Proposal", "Term Sheet", "Negotiation", "PPA"]
haspr.sdp_transitionProbabilities = [0.05, 0.3, 0.5, 0.75]

generateOutputReport = False
haspr.outputDirectory = "D:\\HASPR Output"  # results and output directory
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

print("-> Output of length {} generated.".format(len(haspr.results)))

# dump output to disk
print("Dumping data to local disk...")
haspr.dump_results()

print("Data dump complete.")

# create output report
print("Writing output report to disk...")

haspr.write_output_report()

print("-> Output report of length {} generated.".format(len(haspr.reportText)))
print(consoleBreak)

dateFinish = datetime.datetime.now(pytz.utc)

print("HASPR successfully terminated at {} UTC".format(dateFinish))
print(consoleBreak)
