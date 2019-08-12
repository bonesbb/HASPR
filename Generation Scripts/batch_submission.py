# HASPR - High-Altitude Solar Power Research
# Script to set-up batch jobs for fixed-tilt optimizations on Euler
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

# exit if batch indices are out of range:
if firstIndex < 1 or lastIndex < 1:
    print("[ERROR] Batch indices out of range...")
    sys.exit(-2)

batch_dataset = Dataset("batches")
haspr.get_csv_data(pathToBatchCSV, batch_dataset)

# cycle through batch data and execute if index is within range:
for p in batch_dataset.payload:
    batch_index = int(p[0])

    if batch_index < firstIndex:
        continue

    if batch_index > lastIndex:
        break

    batch_type = str(p[1])
    batch_coords = str(p[2])
    batch_coords = batch_coords.replace('[', '')
    batch_coords = batch_coords.replace(']', '')
    batch_coords = int(batch_coords)
    output_folder = str(p[4])
    output_folder = output_folder.split(" -> ")
    output_folder = output_folder[1]
    sweep_index = int(p[5])

    # construct command:
    command = ["bsub", "python", "./main_euler_fixed.py"]
    coords_option = "coords/coords" + str(batch_coords) + ".csv"
    command.append(coords_option)
    output_option = "output/" + output_folder
    command.append(output_option)
    sis_dataset_option = "datasets/2017/00_2017_SIS_merged.nc"
    command.append(sis_dataset_option)
    sid_dataset_option = "datasets/2017/01_2017_SID_merged.nc"
    command.append(sid_dataset_option)
    type_option = 0
    if batch_type == "O1":
        type_option = "1"
    elif batch_type == "O2":
        type_option = "2"
    else:
        print("[ERROR] unrecognizable batch type: {}".format(batch_type))
        sys.exit(-3)
    command.append(type_option)
    sweep_option = str(sweep_index)
    command.append(sweep_option)

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
