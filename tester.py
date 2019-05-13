import haspr
from haspr import Dataset

haspr.sisDataPath = "D:\\00_SIS_merged.nc"  # path to SIS dataset
haspr.sisdDataPath = ""  # path to SIS direct dataset
haspr.salDataPath = ""  # path to surface albedo dataset

time = '2017-01-01T09:30:00.000000000'

# SIS dataset
d = Dataset("SIS CH", [])

haspr.load_netcdf_dataset(haspr.sisDataPath, d)

sisX = d.payload.SIS

# point of interest
latT = 45.890238429084
lonT = 9.240239184

pixel = haspr.get_pixel(latT, lonT)
print(haspr.get_pixel_value(sisX, pixel[0], pixel[1], time))





