# HASPR - High-Altitude Solar Power Research
# Background script/library - classes, functions, algos
# Version 0.3
# Author: neyring

from pysolar.solar import *
import csv
import xarray
import datetime
from datetime import datetime
from datetime import timedelta
import os
from os import walk
import tarfile
import sys
import pytz
import math

# GLOBAL VARIABLES
outputText = []  # lines for output report
models = []  # initialized collection of all available models
loadedDataSets = []  # datasets which have been fetched
coordinates = -1  # coordinates of interest (solar sites)
sdp_developmentPhases = []
sdp_transitionProbabilities = []
usableSurface = 0
sites = []


# path variables
sisDataPath = ""  # path to SIS dataset
sisdDataPath = ""  # path to SIS direct dataset
salDataPath = ""  # path to surface albedo dataset
sisnDataPath = ""  # path to SIS normal dataset
demDataPath = ""  # path to SwissGrid demand data
outputDirectory = ""  # results and output directory


# initialize model and dataset objects
def initialize():
    # Available Datasets:

    # CM SAF SIS dataset (global incoming on flat surface)
    cmsaf_sis = Dataset("CMSAF_sis")
    cmsaf_sis.spatial_res = 0.05
    cmsaf_sis.temporal_res = 30

    # CM SAF SIS direct dataset (direct incoming on flat surface)
    cmsaf_sisd = Dataset("CMSAF_sisd")
    cmsaf_sisd.spatial_res = 0.05
    cmsaf_sisd.temporal_res = 30

    # CM SAF SIS normal dataset (direct incoming on solar-normal surface)
    cmsaf_sisn = Dataset("CMSAF_sisn")
    cmsaf_sisn.spatial_res = 0.05
    cmsaf_sisn.temporal_res = 30

    # CM SAF SAL dataset (surface albedo as percentage)
    cmsaf_sal = Dataset("CMSAF_sal")
    cmsaf_sal.spatial_res = 0.25
    cmsaf_sal.temporal_res = 7200  # 5 days

    # SwissGrid total CH demand dataset
    swissgrid_demand_ch = Dataset("SwissGrid_demandCH")
    swissgrid_demand_ch.temporal_res = 15

    # Available Models:

    # SIS total flat generation model
    poa_sis = Model("SIS", [cmsaf_sis])
    models.append(poa_sis)

    # SIS normal generation model (solar tracking)
    poa_normal = Model("SIS_normal", [cmsaf_sis, cmsaf_sisd, cmsaf_sal])
    models.append(poa_normal)

    # SIS_demand Swiss demand - total flat generation
    sis_dem = Model("MAR_sis", [cmsaf_sis, swissgrid_demand_ch])
    models.append(sis_dem)

    # POA_iso generation profiling model
    poa_iso = Model("POA_iso", [cmsaf_sis, cmsaf_sisd, cmsaf_sal])
    models.append(poa_iso)

    # MAR_iso market match model
    mar_iso = Model("MAR_iso", [cmsaf_sis, cmsaf_sisd, cmsaf_sisn,
                                swissgrid_demand_ch])
    models.append(mar_iso)

    return

# CLASSES


# Model class:
#   - defines components, time-step, panel positions etc.
class Model:
    # constructor
    def __init__(self, name, req_data):
        self.name = name
        self.req_data = req_data  # required datasets
        self.results = []
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
                run_sis_model(self, False)
                return
            elif self.name == "SIS_normal":
                run_sis_normal_model(self, False)
                return
            elif self.name == "POA_iso":
                run_poa_iso_model(self)
                return
            elif self.name == "SIS_demand":
                run_sis_demand_model(self, False)
                return
            else:
                # warning that model is not implemented
                print("\n[ERROR] {} model implementation not found - skipping model".format(self.name))
                return
        else:
            # warning user that data has not been loaded
            print("\n[ERROR] Missing data - skipping {} model".format(self.name))
        return


# Dataset class:
#   - defines a dataset
class Dataset:
    # constructor
    def __init__(self, name):
        self.name = name
        self.spatial_res = 0  # in degrees (1dim)
        self.temporal_res = 0  # in minutes
        self.data_loaded = False
        self.variable = ""
        self.format = ""
        self.payload = []

    # method to load the data to local disk
    def load_data(self):
        if self.name == "CMSAF_sis":
            load_netcdf_dataset(sisDataPath, self)
        elif self.name == "SwissGrid_demandCH":
            get_csv_data(demDataPath, self)
        elif self.name == "CMSAF_sisd":
            load_netcdf_dataset(sisdDataPath, self)
        elif self.name == "CMSAF_sisn":
            load_netcdf_dataset(sisnDataPath, self)
        elif self.name == "CMSAF_sal":
            load_netcdf_dataset(salDataPath, self)
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

    # method to save the result as a CSV file to an output folder
    def dump(self):
        # write CSV file
        path = outputDirectory + "\\" + self.title + ".csv"
        file = open(path, "w")

        # write lines from payload:
        for p in self.payload:
            file.write(str(p) + "\n")
        file.close()
        print("\n -> '{}' csv file written to {}.".format(self.title, path))
        return


# Site class
#   - defines a potential energy plant site
class Site:
    # constructor
    def __index__(self, title, coords, surface):
        self.title = title
        self.coords = coords
        self.surfaceArea = surface


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
def dump_results(model_objects):
    counter = 0
    for m in model_objects:
        print("Dumping results from {} model...".format(m.name))
        for r in m.results:
            r.dump()
            counter = counter + 1
    print("\n{} result objects dumped.".format(counter))
    return


# writes the output report file to the local disk
def write_output_report():
    # todo
    return


# MODEL FUNCTIONS


# function to run SIS model
# @model: SIS model object
# @mode: True = embedded in another model, False = model of interest
def run_sis_model(model, mode):
    # get SIS dataset payload:
    payload = model.req_data[0].payload
    payload = payload.SIS

    time_array = payload.coords.get('time').values
    efficiency = get_efficiency(model)

    # initialize overview result (totals for each site):
    overview_result = Result("SIS Flat Generation Overview")
    overview_result.format = "CSV"
    overview_result.payload.append("Site ID, Latitude (decimal), Longitude (decimal), Total SIS Flat Generation [Wh/m2]"
                                   ", Winter SIS Flat Generation [Wh/m2],Summer SIS Flat Generation [Wh/m2]")

    coord_counter = 0
    for c in coordinates:
        coord_counter = coord_counter + 1

        # get pixel
        pixel = get_pixel(c[0], c[1], model.req_data[0].spatial_res)

        # initialize current result (full generation profile):
        current_result = Result("Site {} - SIS Flat Generation Model".format(coord_counter))
        current_result.format = "CSV"
        current_result.payload.append("Time, Generation [Wh/m2]")

        print("\n\nSite {} of {}:".format(coord_counter, len(coordinates)))

        total_generation = 0
        winter_total = 0
        for t in time_array:
            to_write = "Calculating output at time = {}".format(t)
            sys.stdout.write('\r' + str(to_write))
            sys.stdout.flush()
            time_sub = str(t)[0:10]
            time_sub = time_sub.split('-')
            month = time_sub[1]
            is_winter = False
            if int(month) < 5 or int(month) > 10:
                is_winter = True
            irradiation = get_pixel_value(payload, pixel[0], pixel[1], t, model.req_data[0].spatial_res)
            electricity_gen = efficiency*irradiation
            energy_gen = electricity_gen * (float(model.req_data[0].temporal_res) / 60)  # we want Wh
            str_to_write = str(t) + ", " + str(energy_gen)
            current_result.payload.append(str_to_write)
            if float(energy_gen) > 0:
                total_generation = total_generation + float(energy_gen)
                if is_winter:
                    winter_total = winter_total + float(energy_gen)

        summer_total = total_generation - winter_total

        # build string for overview result:
        overview_to_append = str(coord_counter) + ", "
        overview_to_append = overview_to_append + str(c[0]) + ", "
        overview_to_append = overview_to_append + str(c[1]) + ", "
        overview_to_append = overview_to_append + str(total_generation) + ", "
        overview_to_append = overview_to_append + str(winter_total) + ", "
        overview_to_append = overview_to_append + str(summer_total)

        overview_result.payload.append(overview_to_append)

        total_text = "Site {} - Total SIS Flat Generation = {} Wh per m2".format(coord_counter, total_generation)
        winter_text = " -> Winter SIS Flat Generation = {} Wh per m2".format(winter_total)
        summer_text = " -> Summer SIS Flat Generation = {} Wh per m2".format(summer_total)

        print("\n" + total_text)
        print(winter_text)
        print(summer_text)

        # add current result to model:
        model.results.append(current_result)

    # add overview result to model:
    model.results.append(overview_result)

    if not mode:
        # todo: note -> we can just return the result objects! (check if inner model results will be dumped...)
        return []

    return []


# function to run SIS normal model
# @model: SIS normal model object
# @mode: True = embedded in another model, False = model of interest
def run_sis_normal_model(model, mode):
    # get time array
    payload = model.req_data[0].payload
    payload = payload.SIS
    time_array = payload.coords.get('time').values

    # initialize overview result (totals for each site):
    overview_result = Result("SIS Full Tracking Generation Overview")
    overview_result.format = "CSV"
    overview_result.payload.append("Site ID, Latitude (decimal), Longitude (decimal) ,Total SIS Full Tracking"
                                   " Generation [Wh/m2], Winter SIS Full Tracking Generation [Wh/m2],"
                                   " Summer SIS Full Tracking Generation [Wh/m2]")

    coord_counter = 0
    for c in coordinates:
        coord_counter = coord_counter + 1

        # initialize current result (full generation profile):
        current_result = Result("Site {} - SIS Full Tracking Generation Model".format(coord_counter))
        current_result.format = "CSV"
        current_result.payload.append("Time, Generation [Wh/m2]")

        print("\n\nSite {} of {}:".format(coord_counter, len(coordinates)))

        total_generation = 0
        winter_total = 0
        for t in time_array:
            to_write = "Calculating output at time = {}".format(t)
            sys.stdout.write('\r' + str(to_write))
            sys.stdout.flush()
            time_sub = str(t)[0:10]
            time_sub = time_sub.split('-')
            month = time_sub[1]
            is_winter = False
            if int(month) < 5 or int(month) > 10:
                is_winter = True

            # get panel azimuth and tilt to track the sun:
            dt_time = to_datetime_utc(t)
            timezone = pytz.utc
            time_aware = timezone.localize(dt_time)

            solar_position = get_solar_position(c, time_aware)

            panel_azimuth = solar_position[1]  # equals solar azimuth
            panel_tilt = 90 - solar_position[0]  # equals 90 - solar altitude
            panel_position = [panel_tilt, panel_azimuth]

            # get surface albedo:
            sal_data = model.req_data[2]
            surface_albedo = get_avg_surface_albedo(sal_data, c[0], c[1], t)

            # get harnessed irradiation:
            irradiation_data = [model.req_data[0], model.req_data[1]]  # [SIS, SISd]
            irradiation = get_poa(c, t, irradiation_data, surface_albedo, solar_position, panel_position)

            # get energy generated:
            efficiency = get_efficiency(model)
            electricity_gen = efficiency * irradiation
            energy_gen = electricity_gen * (float(model.req_data[0].temporal_res) / 60)  # we want Wh

            str_to_write = str(t) + ", " + str(energy_gen)
            current_result.payload.append(str_to_write)

            if float(energy_gen) > 0:
                total_generation = total_generation + float(energy_gen)
                if is_winter:
                    winter_total = winter_total + float(energy_gen)

        summer_total = total_generation - winter_total

        # build string for overview result:
        overview_to_append = str(coord_counter) + ", "
        overview_to_append = overview_to_append + str(c[0]) + ", "
        overview_to_append = overview_to_append + str(c[1]) + ", "
        overview_to_append = overview_to_append + str(total_generation) + ", "
        overview_to_append = overview_to_append + str(winter_total) + ", "
        overview_to_append = overview_to_append + str(summer_total)

        overview_result.payload.append(overview_to_append)

        total_text = "Site {} - Total SIS Full Tracking Generation = {} Wh per m2".format(coord_counter, total_generation)
        winter_text = " -> Winter SIS Full Tracking Generation = {} Wh per m2".format(winter_total)
        summer_text = " -> Summer SIS Full Tracking Generation = {} Wh per m2".format(summer_total)

        print("\n" + total_text)
        print(winter_text)
        print(summer_text)

        # add current result to model:
        model.results.append(current_result)

    # add overview result to model:
    model.results.append(overview_result)

    if not mode:
        # todo: note -> we can just return the result objects! (check if inner model results will be dumped...)
        return []

    return []


# function to run SIS demand model
# @model: SIS demand model object
# @mode: True = embedded in another model, False = model of interest
def run_sis_demand_model(model, mode):
    result = []
    # get generation profile:
    generation_profile = run_sis_model(model, False)

    # get demand data:
    payload = model.req_data[1].payload
    time_array = []
    demand_array = []
    for p in payload:
        time_array.append(p[0])
        demand_array.append(p[1])

    demand_filtered = []
    index = 0

    # filter out demand at generation profile resolution:
    previous_demand = 0
    for d in demand_array:
        if index % 2 == 0:
            total_interval_demand = float(d) + float(previous_demand)
            demand_filtered.append(total_interval_demand)
        previous_demand = d
        index = index + 1

    gp_count = 0
    for gp in generation_profile:
        gp_count = gp_count + 1
        supplied = []
        count = 0
        total_supplied = 0
        for d in demand_filtered:
            demand_index = (2 * count) + 1

            if demand_index >= len(time_array):
                break

            time_supplied = time_array[demand_index]
            output_supplied = gp.payload[count]
            output_supplied = output_supplied[1]

            site = sites[gp_count - 1]
            output_supplied = float(get_surface_area(site)) * float(output_supplied)

            count = count + 1
            d = float(d) / 1000
            if float(d) >= float(output_supplied):
                d = float(d) - float(output_supplied)
                supplied.append([str(time_supplied), str(output_supplied)])
                total_supplied = total_supplied + float(output_supplied)
            elif float(output_supplied) > d and d > 0:
                output_supplied = d
                d = float(d) - float(output_supplied)
                supplied.append([str(time_supplied), str(output_supplied)])
                total_supplied = total_supplied + float(output_supplied)
            else:
                output_supplied = 0
                supplied.append([str(time_supplied), str(output_supplied)])
                total_supplied = total_supplied + float(output_supplied)

        print("\nSite {} - Total Demand-Matched Supply = {} Wh per m2".format(gp_count, total_supplied))

        # result object:
        title = "Site {} - SIS Flat Demand-Matched Model".format(gp_count)
        header = ["Time", "Supplied [Wh/m2]"]
        result_object = Result(title, header)
        result_object.payload = supplied
        result.append(result_object)

    return result


# function to run POA_iso model
# @model: POA_iso model object
def run_poa_iso_model(model):
    # todo
    return


# HELPER FUNCTIONS


# function to get surface area of interest
def get_surface_area(site):
    return float(usableSurface) * float(site.surfaceArea)


# function to get sites as objects
def set_sites(path):
    if path == "":
        print("\n[WARNING]No path given for sites .csv file...")
        return -2
    else:
        # read .csv file for coordinates of interest
        csv_file_reader = csv.reader(open(path, "r"))
        is_header = True
        count = 0
        for row in csv_file_reader:
            count = count + 1
            if is_header:
                is_header = False
                continue  # headers

            surface_area = row[1]
            this_site = Site()  # create site object without coords
            this_site.surfaceArea = surface_area

            sites.append(this_site)

        return


# function to write csv
# @data: csv rows to write
# @path: path to write to
def write_csv(data, path):
    with open(path, 'w') as writeFile:
        writer = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for d in data:
            writer.writerow(d)
        writeFile.close()
    return


# function to get an array of data from a csv file
# @path: file path to the csv sheet
# @return: array of csv data
def get_csv_data(path, dataset):
    to_return = []
    csv_file_reader = csv.reader(open(path, "r"))
    is_header = True
    for row in csv_file_reader:
        if is_header:
            is_header = False
            continue  # headers
        to_return.append(row)

    dataset.payload = to_return
    return to_return


# returns plane of array power received by one square meter of panel at given coordinates and time
# @coords: coordinates of interest [lat, lon]
# @time: time of interest
# @irradiation_array: [SIS, SISd] datasets
# @surface_albedo: surface albedo to use
# @solar_position: [solar altitude, solar azimuth]
# @panel_position: [panel_tilt, panel_azimuth]
def get_poa(coords, time, irradiation_array, surface_albedo, solar_position, panel_position):
    # get necessary values from datasets:
    resolution = irradiation_array[0].spatial_res
    sis_data = irradiation_array[0].payload.SIS
    sisd_data = irradiation_array[1].payload.SID

    pixel = get_pixel(coords[0], coords[1], resolution)

    sis = get_pixel_value(sis_data, pixel[0], pixel[1], time, resolution)
    sis_d = get_pixel_value(sisd_data, pixel[0], pixel[1], time, resolution)
    sis_diff = sis - sis_d

    # get angles in radians:
    solar_zenith_angle = math.radians(90 - solar_position[0])  # SZA = 90 - altitude
    solar_az = math.radians(solar_position[1])

    panel_tilt = math.radians(panel_position[0])
    panel_az = math.radians(panel_position[1])

    # calculate cosine of angle between solar_position and panel_normal position:
    c1 = math.sin(solar_zenith_angle) * math.cos(solar_az) * math.sin(panel_tilt) * math.cos(panel_az)
    c2 = math.sin(solar_zenith_angle) * math.sin(solar_az) * math.sin(panel_tilt) * math.sin(panel_az)
    c3 = math.cos(solar_zenith_angle) * math.cos(panel_tilt)

    cos_alpha = c1 + c2 + c3

    # direct beam component:
    beam_component = 0
    if solar_position[0] > 0:  # we only have a direct beam component if the solar altitude is above 0 degrees (horizon)
        beam_component = cos_alpha * sis_d / math.cos(solar_zenith_angle)

    # diffuse component:
    sky_view_factor = (1 + math.cos(panel_tilt)) / 2
    diffuse_component = sis_diff * sky_view_factor

    # ground-reflected component:
    ground_view_factor = (1 - math.cos(panel_tilt)) / 2
    ground_component = sis * surface_albedo * ground_view_factor

    # return sum of all components:
    total_poa = beam_component + diffuse_component + ground_component
    return total_poa


# returns efficiency of the system based on the given model
# @model: model object in question
# @return: efficiency in [0,1]
def get_efficiency(model):
    # todo - function of temperature?
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
    # multiplier is negative if coordinate is S or W
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
# @return: array of [solar altitude, solar position]
def get_solar_position(coords, timepoint):
    solar_alt = get_altitude(coords[0], coords[1], timepoint)
    solar_az = get_azimuth(coords[0], coords[1], timepoint)
    return [solar_alt, solar_az]


# function to load netcdf 4 data to a given Dataset
# @path: file path of dataset to load
# @dataset: dataset object to which the data will be loaded
def load_netcdf_dataset(path, dataset):
    full_dataset = xarray.open_dataset(path)
    dataset.payload = full_dataset
    dataset.format = "netCDF"
    print("\nPayload data set for {}.".format(dataset.name))
    return


# function to convert datetime64 string to datetime UTC
def to_datetime_utc(timepoint):
    return datetime.utcfromtimestamp(timepoint.astype('O') / 1e9)


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


# function to get coordinate pixel from any point on the grid
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


# function to get surface albedo for a given time by averaging values between 2005 and 2015
# @dataset: surface albedo dataset to use
# @lat: latitude of point of interest
# @lon: longitude of point of interest
# @return: average surface albedo for time of year (factor between 0 and 1)
def get_avg_surface_albedo(dataset, lat, lon, time):

    # get data for given coordinates:
    sal_data = dataset.payload.sal
    resolution_factor = dataset.spatial_res / 2  # e.g. 0.025 for 0.05deg resolution
    lat_slice = slice(lat - resolution_factor, lat + resolution_factor)
    lon_slice = slice(lon - resolution_factor, lon + resolution_factor)

    sal_data_full = sal_data.sel(lat=lat_slice, lon=lon_slice)
    sal_data_times = sal_data_full.coords.get('time').values

    # match time given to available SAL values:
    time_points_to_average = []
    date_of_interest = get_date(time)
    year_of_interest = date_of_interest[0]
    month_of_interest = date_of_interest[1]
    day_of_interest = date_of_interest[2]

    date_string = year_of_interest + '-' + month_of_interest + '-' + day_of_interest
    datetime_of_interest = datetime.strptime(date_string, '%Y-%m-%d')  # convert to datetime to allow for arithmetic!

    # get all values for given day/month:
    for t in sal_data_times:
        date = get_date(str(t))
        year = year_of_interest  # we want to match the dates to the year in question to allow for date arithmetic!
        month = date[1]
        day = date[2]

        # get datetime object:
        date_string = year + '-' + month + '-' + day
        datetime_object = datetime.strptime(date_string, '%Y-%m-%d')

        # SAL data is pentad (5 day):
        match_array = [datetime_object]

        for i in [1, 2, 3, 4]:
            match_array.append(datetime_object + timedelta(days=i))

        # check if date of interest is in our match array:
        if match_array.__contains__(datetime_of_interest):
            time_points_to_average.append(str(t))

    # get average SAL from matched times:
    current_sum = 0
    counter = 0
    for mt in time_points_to_average:
        value = float(sal_data.sel(lat=lat_slice, lon=lon_slice, time=mt).values)

        # disregard 'nan's:
        if value > 0:
            current_sum = current_sum + value
            counter = counter + 1

    if counter > 0:
        avg = current_sum / counter
    else:
        print("\n[WARNING] No available surface albedo values for {}, {} at time {}".format(lat, lon, time))
        return 0

    # dataset values are in percent, we want absolute factor:
    avg = avg / 100

    return avg


# function to get year, month, and day given a time
# @time: time from which to get date
# @return: [year, month, day] as array of strings
def get_date(time):
    time = str(time)
    split = time.split('T')
    date = split[0]
    split = date.split('-')
    year = split[0]
    month = split[1]
    day = split[2]
    return [year, month, day]


# DATASCRAPE FUNCTIONS #

# function to load a full dataset
# @name: name of new dataset
# @path: file path of full netcdf data
# @return: a new dataset with loaded netcdf as payload
def load_netcdf(name, path):
    dataset = Dataset(name)
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
