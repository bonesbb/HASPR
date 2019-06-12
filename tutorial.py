# HASPR - High-Altitude Solar Power Research
# Tutorial
# Version 0.1
# Author: neyring

import haspr



haspr.initialize()
modelsToRun = ["SIS"]  # can be multiple models!

haspr.set_coordinates("D:\\coordinates of interest.csv")  # .csv file path of coordinates
haspr.sisDataPath = "D:\\00_SIS_merged.nc"  # path to SIS dataset

haspr.temporalResolution = 30  # model resolution in minutes
haspr.spatialResolution = 0.05  # resolution of datasets in degrees

haspr.outputDirectory = "D:\\HASPR Output"  # results and output directory

# get model objects to run
modelObjects = []
for m in haspr.models:
    for um in modelsToRun:
        if um == m.name:
            modelObjects.append(m)
            break

# run models
haspr.get_data(modelObjects)
haspr.run_models(modelObjects)
haspr.dump_results()



inputTarDirectory = "[path to some directory]"
outputDirectory = "[choose output directory]"

varName = "[satellite variable name]"

minLongitude = 5.85  # Swiss min=5.9
maxLongitude = 10.6  # Swiss max=10.55
minLatitude = 45.75  # Swiss min=45.8
maxLatitude = 47.9  # Swiss max=47.85

haspr.extract_from_tar(inputTarDirectory, outputDirectory, varName,
                       minLongitude, maxLongitude, minLatitude, maxLatitude)


