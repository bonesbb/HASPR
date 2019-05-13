# HASPR - High-Altitude Solar Power Research
# Background script/library - classes, functions, algos
# Version 0.1
# Author: neyring

from pysolar.solar import *
import csv
import xarray
import datetime
import os
from os import walk
import tarfile
import numpy


# GLOBAL VARIABLES
outputText = []  # lines for output report
results = []  # model results
reportText = []  # output report
models = []  # initialized collection of all available models
loadedDataSets = []  # datasets which have been fetched
temporalResolution = 0
spatialResolution = 0
coordinates = -1  # coordinates of interest (solar sites)
sdp_developmentPhases = []
sdp_transitionProbabilities = []


# path variables
sisDataPath = ""  # path to SIS dataset
sisdDataPath = ""  # path to SIS direct dataset
salDataPath = ""  # path to surface albedo dataset
outputDirectory = ""  # results and output directory


# initialize model and dataset objects
def initialize():
    # Available Datasets:

    # CM SAF SIS dataset
    cmsaf_sis = Dataset("CMSAF_sis", coordinates)

    # CM SAF SIS direct dataset
    cmsaf_sisd = Dataset("CMSAF_sisd", coordinates)

    # CM SAF SIS normalized dataset
    cmsaf_sisn = Dataset("CMSAF_sisn", coordinates)

    # SwissGrid total CH demand dataset
    swissgrid_demand_ch = Dataset("SwissGrid_demandCH", [])

    # Swiss total hydro production dataset
    swiss_hydro_output = Dataset("Swiss_hydro_output", [])

    # Available Models:

    # SIS total flat generation model
    poa_sis = Model("SIS", [cmsaf_sis])
    models.append(poa_sis)

    # POA_iso generation profiling model
    poa_iso = Model("POA_iso", [cmsaf_sis, cmsaf_sisd, cmsaf_sisn])
    models.append(poa_iso)

    # MAR_iso market match model
    mar_iso = Model("MAR_iso", [cmsaf_sis, cmsaf_sisd, cmsaf_sisn,
                                swissgrid_demand_ch])
    models.append(mar_iso)

    # Hydro_PV_balance model
    hydro_pv_balance = Model("Hydro_PV_balance", [cmsaf_sis, cmsaf_sisd,
                                                  cmsaf_sisn, swissgrid_demand_ch,
                                                  swiss_hydro_output])
    models.append(hydro_pv_balance)

    # SDP - Solar Development Pipeline Models
    sdp_ch = Model("SDP_ch", [sdp_developmentPhases, sdp_transitionProbabilities])
    models.append(sdp_ch)

    return

# CLASSES


# Model class:
#   - defines components, time-step, panel positions etc.
class Model:
    # constructor
    def __init__(self, name, req_data):
        self.name = name
        self.req_data = req_data  # required datasets
        self.timestep = temporalResolution  # model resolution in minutes
        self.data_loaded = False

    # method to check if required datasets have been loaded to ram
    def check_data_loaded(self):
        for ds in self.req_data:
            if not ds.data_loaded:
                return False
        return True

    # method to execute the model
    def execute(self):
        loaded = self.check_data_loaded()
        if loaded:
            # run the model:
            print("\nData check successful. Executing {} model run...".format(self.name))
            # switch on model name:
            if self.name == "SIS":
                run_sis_model(self)
                return
            elif self.name == "POA_iso":
                run_poa_iso_model(self)
                return
            else:
                # warning that model is not implemented
                print("\n[ERROR] {} model implementation not found - skipping model")
                return
        else:
            # warning user that data has not been loaded
            print("\n[ERROR] Missing data - skipping model")
        return


# Dataset class:
#   - defines a dataset
class Dataset:
    # constructor
    def __init__(self, name, coords):
        self.name = name
        self.data_loaded = False
        self.coordinates = coords
        self.variable = ""
        self.format = ""
        self.payload = []

    # method to load the data to local disk
    def load_data(self):
        if self.name == "CMSAF_sis":
            load_netcdf_dataset(sisDataPath, self)
        elif self.name == "CMSAF_sisd":
            # todo
            return
        else:
            # warning that dataset load is not implemented
            print("\n[ERROR] Missing {} Dataset Implementation...".format(self.name))
            return
        self.data_loaded = True
        loadedDataSets.append(self)
        return


# Result class
#   - defines a result output
class Result:
    # constructor
    def __init__(self, title):
        self.title = title
        self.format = ""
        self.payload = []

    # method to save the result to an output folder
    def dump(self):
        # todo
        return

# MAIN METHODS


# sets the datasets of given models
# @models_given: array of models to get data for
def get_data(models_given):
    for m in models_given:
        for d in m.req_data:
            found = False
            for ds in loadedDataSets:
                if ds.name == d.name:
                    print("\n-> {} dataset already loaded!".format(ds.name))
                    found = True
                    d = ds  # set local dataset to fully loaded dataset
                    break

            # get the data set if not loaded
            if not found:
                print("\nLoading {} dataset...".format(d.name))
                d.load_data()
            print("\n-> {} dataset loaded.".format(d.name))
        m.data_loaded = True
    return


# executes given models
# @models_given: array of models to run
def run_models(models_given):
    for m in models_given:
        print("\nPreparing {} model...".format(m.name))
        m.execute()
    return


# dumps the simulation results to the local disk
def dump_results():
    # todo
    return


# writes the output report file to the local disk
def write_output_report():
    # todo
    return

# MODEL FUNCTIONS


# function to run SIS model
# @model: SIS model object
def run_sis_model(model):
    # get SIS dataset payload:
    payload = model.req_data[0].payload
    payload = payload.SIS

    time_array = payload.coords.get('time').values
    efficiency = get_efficiency(model)

    coord = coordinates[0]

    # get pixel
    pixel = get_pixel(coord[0], coord[1], spatialResolution)

    result = [['time', 'generation [W/m2]']]

    for t in time_array:
        print("Calculating output at time = {}".format(t))
        irradiation = get_pixel_value(payload, pixel[0], pixel[1], t, spatialResolution)
        electricity_gen = efficiency*irradiation
        result.append([t, electricity_gen])

    # todo: use result class!

    result = numpy.asarray(result)
    output_path = outputDirectory + "\\sis results.csv"
    os.makedirs(outputDirectory)
    numpy.savetxt(output_path, result, fmt='%s', delimiter=",")
    return


# function to run POA_iso model
# @model: POA_iso model object
def run_poa_iso_model(model):
    # todo
    return


# HELPER FUNCTIONS

# returns plane of array power received by one square meter of panel
# todo
def get_poa(irradiance_array, solar_position, panel_normal_position, surface_albedo):
    # todo: implement plane of array
    # get diffuse radiation:
    # sisdiff = sis - sisd

    # calculate angle between solar_position and panel_normal position:
    # todo

    # plug values into formula:
    # todo

    return -1


# returns efficiency of the system based on the given model
# @model: model object in question
# @return: efficiency in [0,1]
def get_efficiency(model):
    # todo
    return 0.15  # 15% efficiency for now


# function to set coordinates variable from .csv file
# @path: file path of coordinates of interest .csv file
def set_coordinates(path):
    global coordinates
    coordinates = get_coordinates(path)
    return


# function to extract coordinates from .csv file path
# @path: file path of input .csv sheet
# @return: coordinates of interest array, -2 if no path given
def get_coordinates(path):
    if path == "":
        print("\n[WARNING]No path given for coordinates .csv file...")
        return -2
    else:
        # read .csv file for coordinates of interest
        to_return = []
        csv_file_reader = csv.reader(open(path, "r"))
        is_header = True
        for row in csv_file_reader:
            if is_header:
                is_header = False
                continue  # headers

            # clean input
            row[1] = clean_input_coords(row[1])

            string_coords = row[1].split(" ")

            lat_decimal = convert_to_decimal(string_coords[0])
            long_decimal = convert_to_decimal(string_coords[1])
            extracted_coord = [lat_decimal, long_decimal]
            to_return.append(extracted_coord)
        return to_return


# function to clean messy utf-8 coordinate data
# @input_string: string to clean
# @return: cleaned string (no character mix-ups)
def clean_input_coords(input_string):
    to_return = input_string.replace("Â°", "°")
    to_return = to_return.replace("â€²", "'")
    to_return = to_return.replace("â€³", "\"")
    return to_return


# function to convert a coordinate in degrees to decimal
# @coord: coordinate in WGS 84 format (string)
# @return: decimal coordinate
def convert_to_decimal(coord):
    # multiplier is negative is coordinate is S or W
    multiplier = 1
    if coord.endswith('S') or coord.endswith('W'):
        multiplier = -1

    # get the 3 components and cast to integers
    components = coord[:-1].split('°')
    degrees = float(components[0])
    components = components[1].split('\'')
    minutes = float(components[0])
    seconds = float(components[1].replace("\"", ""))

    # get decimal coordinate
    to_return = multiplier*(degrees + (minutes / 60) + (seconds / 3600))
    return to_return


# function to get solar position for given coordinates and datetime (via pysolar library SPA)
# @coords: array of length two -> index 0 = latitude (decimal), index 1 = longitude (decimal)
# @timepoint: datetime in UTC
# @return: array of solar altitude and solar position
def get_solar_position(coords, timepoint):
    solar_alt = get_altitude(coords[0], coords[1], timepoint)
    solar_az = get_azimuth(coords[0], coords[1], timepoint)
    return [solar_alt, solar_az]


# function to load netcdf 4 data to a given Dataset
# @path: file path of dataset to load
# @dataset: dataset object to which the data will be loaded
def load_netcdf_dataset(path, dataset):
    full_dataset = xarray.open_dataset(path)
    model_dataset = apply_coordinates(full_dataset, dataset.coordinates)
    dataset.payload = model_dataset
    dataset.format = "netCDF"
    print("\nPayload data set for {}.".format(dataset.name))
    return


# function to get dataset for coordinates of interest
# @data: Dataset to which the coords will be applied
# @coords: Coordinates of interest (2dim array)
# @return: Dataset which is the result of the coordinates transformation
def apply_coordinates(data, coords):
    # todo
    return data


# function to convert datetime64 string to datetime UTC
def to_datetime_utc(timepoint):
    return datetime.datetime.utcfromtimestamp(timepoint.astype('O') / 1e9)


# function to get all available models
# @return: array of model objects
def get_models():
    # todo
    return


# function to get pixel value from netcdf - note: assumes spacial resolution of 0.05 degrees
# @data: xarray DataArray (variable selected)
# @lat: latitude of pixel
# @lon: longitude of pixel
# @time: time of interest
# @return: selected value
def get_pixel_value(data, lat, lon, time, resolution):
    resolution_factor = resolution / 2  # e.g. 0.025 for 0.05deg resolution
    lat_slice = slice(lat-resolution_factor, lat+resolution_factor)
    lon_slice = slice(lon-resolution_factor, lon+resolution_factor)
    to_return = data.sel(lat=lat_slice, lon=lon_slice, time=time).values
    return float(to_return)


# function to get coordinate pixel from any point on the grid (assuming resolution of 0.05deg)
# @lat: latitude of point of interest
# @lon: longitude of point of interest
# @res: resolution in degrees (e.g. 0.05)
# @return: [lat, lon] of grid pixel point
def get_pixel(lat, lon, res):
    lat_rem = lat % res
    lon_rem = lon % res
    lat_pix = lat + (res - lat_rem)
    lon_pix = lon - lon_rem
    return [lat_pix, lon_pix]


# function to get associated pixels given any coordinate point
# @lat: latitude of point of interest
# @lon: longitude of point of interest
# @res: resolution of pixel grid (1dimension)
# @return: array of associated pixel coordinates
def get_associated_pixels(lat, lon, res):
    resolution_factor = res / 2  # e.g. 0.025 for 0.05deg resolution
    to_return = []

    center_pixel = get_pixel(lat, lon, res)
    to_return.append(center_pixel)

    top_left_pixel = get_pixel(lat+resolution_factor, lon-resolution_factor, res)
    if not to_return.__contains__(top_left_pixel):
        to_return.append(top_left_pixel)

    top_mid_pixel = get_pixel(lat+resolution_factor, lon, res)
    if not to_return.__contains__(top_mid_pixel):
        to_return.append(top_mid_pixel)

    top_right_pixel = get_pixel(lat+resolution_factor, lon+resolution_factor, res)
    if not to_return.__contains__(top_right_pixel):
        to_return.append(top_right_pixel)

    mid_left_pixel = get_pixel(lat, lon-resolution_factor, res)
    if not to_return.__contains__(mid_left_pixel):
        to_return.append(mid_left_pixel)

    mid_right_pixel = get_pixel(lat, lon+resolution_factor, res)
    if not to_return.__contains__(mid_right_pixel):
        to_return.append(mid_right_pixel)

    bottom_left_pixel = get_pixel(lat-resolution_factor, lon-resolution_factor, res)
    if not to_return.__contains__(bottom_left_pixel):
        to_return.append(bottom_left_pixel)

    bottom_mid_pixel = get_pixel(lat-resolution_factor, lon, res)
    if not to_return.__contains__(bottom_mid_pixel):
        to_return.append(bottom_mid_pixel)

    bottom_right_pixel = get_pixel(lat-resolution_factor, lon+resolution_factor, res)
    if not to_return.__contains__(bottom_right_pixel):
        to_return.append(bottom_right_pixel)

    return to_return


# DATASCRAPE FUNCTIONS #

# function to load a full dataset
# @name: name of new dataset
# @path: file path of full netcdf data
# @return: a new dataset with loaded netcdf as payload
def load_netcdf(name, path):
    dataset = Dataset(name, [])
    load_netcdf_dataset(path, dataset)
    return dataset


# function to extract relevant coords and time from dataset
# @dataset: dataset to extract from
# @var_name: variable name to extract
# @lon_min: minimum longitude for slice
# @lon_max: maximum longitude for slice
# @lat_min: minimum latitude for slice
# @lat_max: maximum latitude for slice
# @return: new dataset with extracted netcdf as payload
def extract_data(dataset, var_name, lon_min, lon_max, lat_min, lat_max):
    payload = dataset.payload.get(var_name)
    new_payload = payload.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
    dataset.payload = new_payload
    return dataset


# function to extract both the full and light-weight datasets given a directory of tar files
# @input_directory: directory of tar files to extract from
# @output_directory: directory to write output files to
# @var_name: name of the variable of interest (netcdf name)
# @var_name: variable name to extract
# @lon_min: minimum longitude for light-weight
# @lon_max: maximum longitude for light-weight
# @lat_min: minimum latitude for light-weight
# @lat_max: maximum latitude for light-weight
def extract_from_tar(input_directory, output_directory, var_name, lon_min, lon_max, lat_min, lat_max):
    light_weight_file_paths = []  # used for merging all light-weight files

    # get tar files to cycle through
    print("\nGetting tar files...")
    tar_file_names = []
    for (dirpath, dirnames, filenames) in walk(input_directory):
        tar_file_names.extend(filenames)

    print("\nPreparing to extract from {} tar files...".format(len(tar_file_names)))

    # cycle through tar files
    for fn in tar_file_names:
        print("\nExtracting from {}...".format(fn))
        tar_path = input_directory + "\\" + fn
        tar = tarfile.open(tar_path)
        member_list = tar.getmembers()

        # get file list
        file_names = []
        for member in member_list:
            file_names.append(member.name)

        print("\n -> Extracting {} files...".format(len(file_names)))

        tar.extractall(output_directory)
        tar.close()

        # delete tar file -> extracted full .nc files stay on local disk
        os.remove(tar_path)

        print("\n -> tar file removed. Extracting datasets...")

        # cycle through extracted files
        for f in file_names:
            print("\nExtracting from {} ...".format(f))
            file_path = output_directory + "\\" + f

            # 1. load data
            d = load_netcdf("tempDS", file_path)
            print(" -> data loaded.")

            # 2. extract data
            d_new = extract_data(d, var_name, lon_min, lon_max, lat_min, lat_max)
            print(" -> data extracted.")

            # 3. write new file
            extracted_file_path = output_directory + "\\extracted_" + f
            d_new.payload.to_netcdf(extracted_file_path)
            light_weight_file_paths.append(extracted_file_path)
            print(" -> extracted file written to disk.")

    print("\ntar extraction complete!")
    return


# function to merge netcdf files
# @merge__directory: directory containing files to merge -> output will be written here
# @var_name: name of the variable of interest (netcdf name)
def merge_netcdf(merge_directory, var_name):
    file_names = []
    for (dirpath, dirnames, filenames) in walk(merge_directory):
        file_names.extend(filenames)

    print("\nMerging {} files...".format(len(file_names)))

    data_arrays_to_merge = []
    counter = 1
    for fn in file_names:
        ds_name = "tempDS" + str(counter)
        d = load_netcdf(ds_name, merge_directory + "\\" + fn)
        data_arrays_to_merge.append(d.payload.get(var_name))
        counter = counter + 1

    # merge datasets -> 2 at a time:
    current_merge_index = 1  # start at index 1 since we set current merged set to first array
    current_merged_set = data_arrays_to_merge[0]
    while current_merge_index < len(data_arrays_to_merge):
        print("Merging index {}".format(current_merge_index))
        current_merged_set = xarray.merge([current_merged_set,
                                           data_arrays_to_merge[current_merge_index]])
        print(" -> done.")
        current_merge_index = current_merge_index + 1

    print("\n -> {} datasets merged.".format(len(data_arrays_to_merge)))
    path_out = merge_directory + "\\00_" + var_name + "_merged.nc"
    current_merged_set.to_netcdf(path_out)
    print(" -> merged output written to {}.".format(path_out))
    return
