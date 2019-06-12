# HASPR - High-Altitude Solar Power Research
# Script to process Surface Albedo data for POA model input
# Version 0.1
# Author: neyring

import haspr
from haspr import Dataset
import sys
from datetime import datetime
from datetime import timedelta


time_of_interest = '2017-02-14T15:30:00.000000000'

# load full SAL data into Dasaset object:
input_path = "D:\\POA Datasets\\02_SAL_merged.nc"

d = Dataset("SAL")
d.spatial_res = 0.25

haspr.load_netcdf_dataset(input_path, d)

# point of interest
latT = 45.890238429084
lonT = 9.240239184
latT2 = 45.875
lonT2 = 5.875

lat3 = 46.09934
lon3 = 7.22039


x = haspr.get_avg_surface_albedo(d, lat3, lon3, time_of_interest)

print("\nAverage SAL = {}".format(x))

sys.exit(1)

salX = d.payload.sal

resolution_factor = d.spatial_res / 2  # e.g. 0.025 for 0.05deg resolution
lat_slice = slice(latT-resolution_factor, latT+resolution_factor)
lon_slice = slice(lonT-resolution_factor, lonT+resolution_factor)

x = salX.sel(lat=lat_slice, lon=lon_slice)

#print(x.coords.get('time').values)




