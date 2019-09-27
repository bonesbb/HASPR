# HASPR - High-Altitude Solar Power Research
# Script to copy files from batch output to the corresponding historic profile directories
# Version 0.1
# Author: neyring

from shutil import copyfile
import haspr
from os import walk

batchDirectory = "E:\\O2 Winter Results\\B1604"
dataYear = "2017"
globalDestinationDir = "D:\\00_Results\\02_Generation Profiles\\Case 5 - 30 to 65 deg winter opt"
haspr.osPathDelimiter = "\\"

# get file names in batch directory:
file_names = []
for (dirpath, dirnames, filenames) in walk(batchDirectory):
    file_names.extend(filenames)

# get output directory names:
dir_names = []
for (dirpath, dirnames, filenames) in walk(globalDestinationDir):
    dir_names.extend(dirnames)

# cycle through file names and copy to corresponding destination:
counter = 0
for f in file_names:
    if "Generation Model" in f:
        # add year to file name:
        new_name = f.replace(".csv", " - " + dataYear + ".csv")

        # get site Id
        id_str = new_name.split(" ")
        id_str = id_str[1] + " " + id_str[2] + " "

        # set destination path and copy file:
        for d in dir_names:
            if (id_str in d) and not ("leap" in d):
                src = batchDirectory + haspr.osPathDelimiter + f
                dst = globalDestinationDir + haspr.osPathDelimiter + d + haspr.osPathDelimiter + new_name
                copyfile(src, dst)
                print("{} copied to {}".format(src, dst))
                counter = counter + 1

print("-> {} files copied.".format(counter))
