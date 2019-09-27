# HASPR - High-Altitude Solar Power Research
# Script for setting up batch jobs for fixed-tilt calculations on Euler
# Version 0.1
# Author: neyring

import subprocess
import haspr
from haspr import Dataset
import sys

# PARAMETERS #
# path to CSV file containing definition of batch jobs:
pathToBatchCSV = "/cluster/home/neyring/euler_batches.csv"
# first batch index to run:
firstIndex = -1
# last batch index to run:
lastIndex = -1

# command line functionality for batch indices:
if len(sys.argv) > 1:
    # Arg1 = first index
    firstIndex = int(sys.argv[1])

if len(sys.argv) > 2:
    # Arg2 = second index
    lastIndex = int(sys.argv[2])

# boolean to run all batches:
run_all = False

# exit if batch indices are out of range:
if firstIndex < 1 or lastIndex < 1:
    run_all = True

batch_dataset = Dataset("batches")
haspr.get_csv_data(pathToBatchCSV, batch_dataset)

# cycle through batch data and execute if index is within range:
for p in batch_dataset.payload:
    batch_index = int(p[0])

    if batch_index < firstIndex and not run_all:
        continue

    if batch_index > lastIndex and not run_all:
        break

    batch_type = str(p[1]).strip()
    batch_coords = str(p[2])

    coords_suffix = ""
    if "O1 Total" in batch_coords:
        coords_suffix = "_O1_total.csv"
    elif "O1 Winter" in batch_coords:
        coords_suffix = "_O1_winter.csv"
    elif "O2 Winter" in batch_coords:
        coords_suffix = "_O2_winter.csv"
    else:
        print("[ERROR] coords suffix not found...")
        sys.exit(-1)

    coords_prefix = ""
    if "1 to 20" in batch_coords:
        coords_prefix = "coords1_to_20"
    elif "21 to 40" in batch_coords:
        coords_prefix = "coords21_to_40"
    elif "41 to 60" in batch_coords:
        coords_prefix = "coords41_to_60"
    elif "61 to 80" in batch_coords:
        coords_prefix = "coords61_to_80"
    elif "81 to 82" in batch_coords:
        coords_prefix = "coords81_to_82"
    else:
        print("[ERROR] coords prefix not found...")
        sys.exit(-1)

    year = str(p[3])

    output_folder = str(p[4])
    output_folder = output_folder.split(" -> ")
    output_folder = output_folder[1]

    # construct command:
    command = ["bsub", "python", "./main_euler_fixed.py"]
    coords_option = "coords/" + coords_prefix + coords_suffix
    command.append(coords_option)
    output_option = "output/" + output_folder
    command.append(output_option)
    sis_dataset_option = "datasets/" + year + "/00_" + year + "_SIS_merged.nc"
    command.append(sis_dataset_option)
    sid_dataset_option = "datasets/" + year + "/01_" + year + "_SID_merged.nc"
    command.append(sid_dataset_option)

    # create output folder for current batch:
    subprocess.run(["mkdir", output_option])

    # run the command:
    subprocess.run(command)

    # print the command which was run:
    command_string = ""
    for c in command:
        command_string = command_string + c + " "

    print("Executed: {}".format(command_string))

print("All batches submitted!")
