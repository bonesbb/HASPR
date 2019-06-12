import haspr
from haspr import Dataset
import sys

path = "D:\\POA Datasets\\02_SAL_merged.nc"

d = Dataset("test")
d.spatial_res = 0.25

haspr.load_netcdf_dataset(path, d)

salX = d.payload.sal

time = '2005-01-01T00:00:00.000000000'

# point of interest
latT = 45.890238429084
lonT = 9.240239184
latT2 = 45.875
lonT2 = 5.875


#print(d.payload.sal.coords.get('time').values)

to_return = salX.sel(lat=latT2, lon=lonT2, time=time).values

print(to_return)

pixel = haspr.get_pixel(latT2, lonT2, d.spatial_res)


#print(d.payload.sal.coords.get('time').values)

x = haspr.get_pixel_value(salX, latT, lonT, time, d.spatial_res)
print(x)
