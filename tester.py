import haspr
from haspr import Dataset
import sys
import math
from datetime import datetime

fullFixedPanelSweepRange = haspr.get_full_fixed_panel_sweep_range()
fixedPanelSweepBatches = haspr.get_sweep_batches(fullFixedPanelSweepRange, 20)  # we want to run  20 at a time

opt1_sweep = haspr.get_opt1_sweep_range()

batches = haspr.get_sweep_batches(opt1_sweep, 20)

print(len(batches[1]))

sys.exit(2)

print(len(fullFixedPanelSweepRange))

time = '2005-01-01T00:00:00.000000000'

latT = 45.890238429084
lonT = 9.240239184

#x = haspr.get_solar_position([latT, lonT], time)

#print(x)



d = Dataset("test")
d.spatial_res = 0.05

path = "D:\\POA Datasets\\03_2017_SIS_normal_merged.nc"

haspr.load_netcdf_dataset(path, d)

print(d.payload)

sys.exit(1)

time = '2005-01-01T00:00:00.000000000'

# point of interest
latT = 45.890238429084
lonT = 9.240239184
latT2 = 45.875
lonT2 = 5.875


#print(d.payload.sal.coords.get('time').values)

to_return = salX.sel(lat=latT2, lon=lonT2, time=time).values

#print(to_return)

pixel = haspr.get_pixel(latT2, lonT2, d.spatial_res)


#print(d.payload.sal.coords.get('time').values)

x = haspr.get_pixel_value(salX, latT, lonT, time, d.spatial_res)
print(x)
