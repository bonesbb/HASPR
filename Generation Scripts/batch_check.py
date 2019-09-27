# HASPR - High-Altitude Solar Power Research
# Script to check if batches have successfully run. Outputs incomplete batch list.
# Version 0.1
# Author: neyring

from os import walk
import haspr
from haspr import Dataset
from haspr import Result

# PARAMETERS #
directoryToCheck = "E:\\O2 Winter Results"  # path to directory containing batch output
pathToBatchCSV = "D:\\00_Results\\99_Model Inputs\\Euler batches full.csv"
haspr.outputDirectory = "D:\\00_Results\\99_Model Inputs\\Out"
haspr.osPathDelimiter = "\\"


# get all inner directory names
dir_names = []
for (dirpath, dirnames, filenames) in walk(directoryToCheck):
    dir_names.extend(dirnames)

incomplete_dirs = []

print("Indices of incomplete directories:")

for d in dir_names:
    inner_files = []
    inner_dir_path = directoryToCheck + "\\" + d
    for (dirpath, dirnames, filenames) in walk(inner_dir_path):
        inner_files.extend(filenames)
    files_found = len(inner_files)
    if files_found != 41 and files_found != 5:
        batch_index = int(d[1:])
        incomplete_dirs.append(batch_index)
        print(batch_index)

print("{} incomplete dirs".format(len(incomplete_dirs)))

# create new batch list
batch_list = Dataset("batch list")
haspr.get_csv_data(pathToBatchCSV, batch_list)

new_batch_data = []

for p in batch_list.payload:
    batch_id = int(p[0])
    if batch_id in incomplete_dirs:
        str_to_append = str(p[0])
        for pi in p[1:]:
            str_to_append = str_to_append + "," + str(pi)
        new_batch_data.append(str_to_append)

result = Result("Euler_batches_resubmit")
result.payload.append("Batch Number, Type, Site IDs, Year, Output Folder, Sweep Index, Job Sub, Result Check")
for nbd in new_batch_data:
    result.payload.append(nbd)

result.dump()
