# HASPR - High-Altitude Solar Power Research
# Background script/library - classes, functions, algos
# Version 0.7
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
import numpy as np

# GLOBAL VARIABLES
outputText = []  # lines for output report
models = []  # initialized collection of all available models
loadedDataSets = []  # datasets which have been fetched
coordinates = -1  # coordinates of interest (solar sites)
sdp_developmentPhases = []
sdp_transitionProbabilities = []
usableSurface = 0  # fraction of water body surface area which can be used
currentFixedPanelSweepRange = []  # array of [az, tilt] values to sweep in current model
fixedPanelSweepIncrement = 10  # in degrees
sites = []
poaBreakdownValues = []  # used to analyse the contribution of the 3 components in POA models
nanCounter = [0, 0]  # used to add the number of NANs to each output report. Format = [#irradianceNAN, #salNANs]


# path variables
osPathDelimiter = ""  # operating system dependent => "/" for unix systems, "\\" for windows
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

    # POA normal generation model (solar tracking)
    poa_normal = Model("POA_normal", [cmsaf_sis, cmsaf_sisd, cmsaf_sal])
    models.append(poa_normal)

    # POA fixed position model (parameter sweep)
    poa_fixed = Model("POA_fixed", [cmsaf_sis, cmsaf_sisd, cmsaf_sal])
    poa_fixed.sweep_range = currentFixedPanelSweepRange  # set sweep range!
    models.append(poa_fixed)

    # SIS_demand Swiss demand - total flat generation
    sis_dem = Model("MAR_sis", [cmsaf_sis, swissgrid_demand_ch])
    models.append(sis_dem)

    # POA_fixed generation profiling model - fixed position optimization
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
        self.sweep_range = []

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
            elif self.name == "POA_normal":
                run_poa_normal_model(self)
                return
            elif self.name == "POA_fixed":
                run_poa_fixed_model(self)
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
        self.output_directory = outputDirectory

    # method to save the result as a CSV file to an output folder
    def dump(self):
        # write CSV file
        path = self.output_directory + osPathDelimiter + self.title + ".csv"
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
# @return: result objects generated by the model
def run_sis_model(model):
    # get SIS dataset payload:
    payload = model.req_data[0].payload
    payload = payload.SIS

    time_array = payload.coords.get('time').values
    efficiency = get_efficiency(model)

    # initialize overview result (totals for each site):
    overview_result = Result("SIS Flat Generation Overview")
    overview_result.format = "CSV"
    overview_result.payload.append("Site ID, Latitude (decimal), Longitude (decimal), Total SIS Flat Generation [Wh/m2]"
                                   ", Winter SIS Flat Generation [Wh/m2], Summer SIS Flat Generation [Wh/m2], "
                                   "# SIS NANs")

    coord_counter = 0
    for c in coordinates:
        coord_counter = coord_counter + 1

        # reset NAN counter:
        global nanCounter
        nanCounter = [0, 0]

        # get pixel
        pixel = get_pixel(c[0], c[1], model.req_data[0].spatial_res)

        # initialize current result (full generation profile):
        current_result = Result("Site {} - SIS Flat Generation Model".format(c[2]))
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
        overview_to_append = overview_to_append + str(summer_total) + ", "
        overview_to_append = overview_to_append + str(nanCounter[0])

        overview_result.payload.append(overview_to_append)

        total_text = "Site {} - Total SIS Flat Generation = {} Wh per m2".format(c[2], total_generation)
        winter_text = " -> Winter SIS Flat Generation = {} Wh per m2".format(winter_total)
        summer_text = " -> Summer SIS Flat Generation = {} Wh per m2".format(summer_total)

        print("\n" + total_text)
        print(winter_text)
        print(summer_text)

        # add current result to model:
        model.results.append(current_result)

    # add overview result to model:
    model.results.append(overview_result)

    return model.results


# function to run SIS normal model
# @model: SIS normal model object
# @return: result objects generated by the model
def run_poa_normal_model(model):
    # get time array
    payload = model.req_data[0].payload
    payload = payload.SIS
    time_array = payload.coords.get('time').values

    # initialize overview result (totals for each site):
    overview_result = Result("SIS Full Tracking Generation Overview")
    overview_result.format = "CSV"
    overview_result.payload.append("Site ID, Latitude (decimal), Longitude (decimal), Total SIS Full Tracking"
                                   " Generation [Wh/m2], Winter SIS Full Tracking Generation [Wh/m2],"
                                   " Summer SIS Full Tracking Generation [Wh/m2], # Irradiation NANs,"
                                   " # Surface Albedo NANs")

    coord_counter = 0
    for c in coordinates:
        coord_counter = coord_counter + 1

        # reset NAN counter:
        global nanCounter
        nanCounter = [0, 0]

        # initialize current result (full generation profile):
        current_result = Result("Site {} - SIS Full Tracking Generation Model".format(c[2]))
        current_result.format = "CSV"
        current_result.payload.append("Time, Generation [Wh/m2]")

        # initialize current POA Breakdown Result:
        current_poa_breakdown_result = Result("Site {} - POA Breakdown".format(c[2]))
        current_poa_breakdown_result.format = "CSV"
        current_poa_breakdown_result.payload.append("Direct Component [W], Diffuse Component [W], Ground Component [W]")
        global poaBreakdownValues
        poaBreakdownValues = []  # re-initialize breakdown values

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
        overview_to_append = str(c[2]) + ", "
        overview_to_append = overview_to_append + str(c[0]) + ", "
        overview_to_append = overview_to_append + str(c[1]) + ", "
        overview_to_append = overview_to_append + str(total_generation) + ", "
        overview_to_append = overview_to_append + str(winter_total) + ", "
        overview_to_append = overview_to_append + str(summer_total) + ", "
        overview_to_append = overview_to_append + str(nanCounter[0]) + ", "
        overview_to_append = overview_to_append + str(nanCounter[1])

        overview_result.payload.append(overview_to_append)

        total_text = "Site {} - Total SIS Full Tracking Generation = {} Wh per m2".format(c[2], total_generation)
        winter_text = " -> Winter SIS Full Tracking Generation = {} Wh per m2".format(winter_total)
        summer_text = " -> Summer SIS Full Tracking Generation = {} Wh per m2".format(summer_total)

        print("\n" + total_text)
        print(winter_text)
        print(summer_text)

        # add current result to model:
        model.results.append(current_result)

        # finalize POA breakdown result:
        for i in poaBreakdownValues:
            str_to_append = str(i[0]) + ", "
            str_to_append = str_to_append + str(i[1]) + ", "
            str_to_append = str_to_append + str(i[2])
            current_poa_breakdown_result.payload.append(str_to_append)

        model.results.append(current_poa_breakdown_result)

    # add overview result to model:
    model.results.append(overview_result)

    return model.results


# function to run POA fixed model
# @model: POA fixed model object
# @return: result objects generated by the model
def run_poa_fixed_model(model):
    # for-loop to calculate profiles for each position in the sweep:
    for params in model.sweep_range:
        az = params[0]
        tilt = params[1]

        is_a_sweep = True  # used to break the sweep if we have already optimized
        if len(coordinates[0]) > 3:
            is_a_sweep = False
            az = "OPT"
            tilt = "OPT"

        # get generation profiles for current sweep position:
        print("\n*******************************************************\n")
        print("\n-> Running POA_fixed model for azimuth = {}, tilt = {}".format(az, tilt))

        # get time array
        payload = model.req_data[0].payload
        payload = payload.SIS
        time_array = payload.coords.get('time').values

        # initialize overview result (totals for each site):
        overview_result = Result("{}-{} Fixed Generation Overview".format(az, tilt))
        overview_result.format = "CSV"
        overview_result.payload.append("Site ID, Latitude (decimal), Longitude (decimal), Total Fixed Tilt Generation"
                                       " [Wh/m2], Winter Fixed Tilt Generation [Wh/m2], "
                                       "Summer Fixed Tilt Generation [Wh/m2], # Irradiation NANs,"
                                       " # Surface Albedo NANs")

        coord_counter = 0
        for c in coordinates:
            coord_counter = coord_counter + 1

            # set azimuth and tilt if we are not in a sweep:
            if not is_a_sweep:
                az = c[3]
                tilt = c[4]

            # reset NAN counter:
            global nanCounter
            nanCounter = [0, 0]

            # initialize current result (full generation profile):
            current_result = Result("{}-{} Site {} - Fixed Generation Model".format(az, tilt, c[2]))
            current_result.format = "CSV"
            current_result.payload.append("Time, Generation [Wh/m2]")

            # initialize current POA Breakdown Result:
            current_poa_breakdown_result = Result("{}-{} Site {} - POA Breakdown".format(az, tilt, c[2]))
            current_poa_breakdown_result.format = "CSV"
            current_poa_breakdown_result.payload.append("Direct Component [W], Diffuse Component [W],"
                                                        " Ground Component [W]")
            global poaBreakdownValues
            poaBreakdownValues = []  # re-initialize breakdown values

            print("\n\n{}-{} Site {} of {}:".format(az, tilt, coord_counter, len(coordinates)))

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

                # get solar position:
                dt_time = to_datetime_utc(t)
                timezone = pytz.utc
                time_aware = timezone.localize(dt_time)

                solar_position = get_solar_position(c, time_aware)

                panel_position = [tilt, az]

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
            overview_to_append = str(c[2]) + ", "
            overview_to_append = overview_to_append + str(c[0]) + ", "
            overview_to_append = overview_to_append + str(c[1]) + ", "
            overview_to_append = overview_to_append + str(total_generation) + ", "
            overview_to_append = overview_to_append + str(winter_total) + ", "
            overview_to_append = overview_to_append + str(summer_total) + ", "
            overview_to_append = overview_to_append + str(nanCounter[0]) + ", "
            overview_to_append = overview_to_append + str(nanCounter[1])

            overview_result.payload.append(overview_to_append)

            total_text = "{}-{} Site {} - Total SIS Full Tracking Generation = {} Wh/m2".format(az, tilt,
                                                                                                c[2],
                                                                                                total_generation)
            winter_text = " -> Winter SIS Full Tracking Generation = {} Wh/m2".format(winter_total)
            summer_text = " -> Summer SIS Full Tracking Generation = {} Wh/m2".format(summer_total)

            print("\n" + total_text)
            print(winter_text)
            print(summer_text)

            # finalize POA breakdown result:
            for i in poaBreakdownValues:
                str_to_append = str(i[0]) + ", "
                str_to_append = str_to_append + str(i[1]) + ", "
                str_to_append = str_to_append + str(i[2])
                current_poa_breakdown_result.payload.append(str_to_append)

            model.results.append(current_poa_breakdown_result)

            # add current result to model:
            model.results.append(current_result)

        # add overview result to model:
        model.results.append(overview_result)

        # break the sweep for-loop if we are not in a sweep:
        if not is_a_sweep:
            break

    return model.results


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
# @return: array of csv data (no headers)
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
# NOTE: also adds component breakdown to the global poaBreakdownResult object
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
    # we only have a direct beam component if cos_alpha > 0 (sun is not "behind" panel)
    # and solar altitude is above 0 degrees (horizon)
    beam_component = 0
    if cos_alpha > 0 and solar_position[0] > 0:
        beam_component = cos_alpha * sis_d / math.cos(solar_zenith_angle)

    # diffuse component:
    sky_view_factor = (1 + math.cos(panel_tilt)) / 2
    diffuse_component = sis_diff * sky_view_factor

    # ground-reflected component:
    ground_view_factor = (1 - math.cos(panel_tilt)) / 2
    ground_component = sis * surface_albedo * ground_view_factor

    # return sum of all components:
    total_poa = beam_component + diffuse_component + ground_component

    # append components to POA breakdown array:
    poaBreakdownValues.append([beam_component, diffuse_component, ground_component])

    return total_poa


# returns efficiency of the system based on the given model
# @model: model object in question
# @return: efficiency in [0,1]
def get_efficiency(model):
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
            site_id = row[0]

            string_coords = row[1].split(" ")

            lat_decimal = convert_to_decimal(string_coords[0])
            long_decimal = convert_to_decimal(string_coords[1])
            extracted_coord = [lat_decimal, long_decimal, site_id]

            # set optimized fixed position if given:
            if len(row) > 3:
                opt_az = float(row[2])
                opt_tilt = float(row[3])
                extracted_coord.append(opt_az)
                extracted_coord.append(opt_tilt)

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

    # clean characters for use on Euler cluster:
    if "′" in components[1]:
        components[1] = components[1].replace("′", "'")

    if "″" in components[1]:
        components[1] = components[1].replace("″", "\"")

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
# NOTE: counting NANs and setting them to zero occurs here!
# @data: xarray DataArray (variable selected)
# @lat: latitude of pixel
# @lon: longitude of pixel
# @time: time of interest
# @return: selected value
def get_pixel_value(data, lat, lon, time, resolution):
    resolution_factor = resolution / 2  # e.g. 0.025 for 0.05deg resolution
    lat_slice = slice(lat-resolution_factor, lat+resolution_factor)
    lon_slice = slice(lon-resolution_factor, lon+resolution_factor)
    to_return = float(data.sel(lat=lat_slice, lon=lon_slice, time=time).values)

    # if NAN => increment counter and set return value to zero:
    if not to_return >= 0:
        to_return = 0
        global nanCounter
        nanCounter[0] = nanCounter[0] + 1
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
        global nanCounter
        nanCounter[1] = nanCounter[1] + 1
        return 0

    # dataset values are in percent, we want absolute factor:
    avg = avg / 100

    return avg


# function to get year, month, and day given a time
# @time: time from which to get date
# @return: [year, month, day] as array of strings
def get_date(time):
    time = str(time)
    year = -1
    month = -1
    day = -1
    if not time.__contains__('T'):
        date = time.split(" - ")
        date = date[0].split(" ")
        date = date[0].split(".")
        day = date[0]
        month = date[1]
        year = date[2]
    else:
        split = time.split('T')
        date = split[0]
        split = date.split('-')
        year = split[0]
        month = split[1]
        day = split[2]

    return [year, month, day]


# function to get sweep range batches given batch length
# @batch_length: number of parameter combinations to output per batch
# @return: array of parameter sweep batches e.g. [[azimuth1, tilt1], [...],... ]
def get_sweep_batches(full_sweep, batch_length):
    # get chunks of batch_length from the full_sweep array:
    batches = []
    for i in range(0, len(full_sweep), batch_length):
        batches.append(full_sweep[i:i+batch_length])
    return batches


# function to get all available parameter configurations for fixed tilt sweep
# @return: array with each element in the form of [azimuth, tilt]
def get_full_fixed_panel_sweep_range():
    # get arrays of possible values for fixed panel parameter sweep
    max_az = 360
    max_tilt = 90

    # azimuth values to sweep:
    azimuth_sweep = []
    while max_az >= 0:
        azimuth_sweep.append(max_az)
        max_az = max_az - fixedPanelSweepIncrement

    # tilt values to sweep:
    tilt_sweep = []
    while max_tilt > 0:  # exclude cases where tilt = 0 as this implies flat panels
        tilt_sweep.append(max_tilt)
        max_tilt = max_tilt - fixedPanelSweepIncrement

    full_sweep_array = []

    for az in azimuth_sweep:
        for tilt in tilt_sweep:
            full_sweep_array.append([az, tilt])

    return full_sweep_array


# function to get available parameter configurations for 10 deg azimuth sweep with fixed tilt = 12 deg
# @return: array with each element in the form of [azimuth, tilt]
def get_opt1_sweep_range():
    # azimuth sweep in 10 degree increments:
    max_az = 360
    azimuth_sweep = []

    while max_az >= 0:
        azimuth_sweep.append(max_az)
        max_az = max_az - 10

    to_return = []

    for az in azimuth_sweep:
        to_return.append([az, 12])

    return to_return


# function to get available parameter configurations for 10 deg azimuth, 5 deg tilt (between 30, 65) sweep
# @return: array with each element in the form of [azimuth, tilt]
def get_opt2_sweep_range():
    # azimuth sweep in 10 degree increments:
    max_az = 360
    azimuth_sweep = []

    while max_az >= 0:
        azimuth_sweep.append(max_az)
        max_az = max_az - 10

    # tilt sweep in 5 degree increments and range = [30, 65]:
    max_tilt = 65
    min_tilt = 30
    tilt_sweep = []

    while max_tilt >= min_tilt:
        tilt_sweep.append(max_tilt)
        max_tilt = max_tilt - 5

    to_return = []

    for az in azimuth_sweep:
        for t in tilt_sweep:
            to_return.append([az, t])

    return to_return


# ANALYSIS FUNCTIONS #

# function to get hourly generation profile from 30-min input (1 year)
# @title: desired output title (= file name without extension)
# @half_hour_dataset: HASPR Dataset object containing one 30-min profile
# @return: HASPR Result object containing the corresponding hourly profile
def get_hourly_profile(title, half_hour_dataset):
    new_title = title + " - hourly"
    hourly_profile = Result(new_title)
    hourly_profile.payload.append("Time, Generation")
    input_values = half_hour_dataset.payload
    for i in range(0, len(input_values)):
        residual = i % 2
        if residual == 0:
            timestamp = input_values[i][0]
            hourly_generation = float(input_values[i][1]) + float(input_values[i+1][1])
            str_to_append = str(timestamp) + ", " + str(hourly_generation)
            hourly_profile.payload.append(str_to_append)
    return hourly_profile


# function to get daily generation profile from 30-min input (1 year)
# @title: desired output title (= file name without extension)
# @half_hour_dataset: HASPR Dataset object containing one 30-min profile
# @return: HASPR Result object containing the corresponding daily profile
def get_daily_profile(title, half_hour_dataset):
    new_title = title + " - daily"
    daily_profile = Result(new_title)
    daily_profile.payload.append("Time, Generation")
    input_values = half_hour_dataset.payload
    for i in range(0, len(input_values)):
        residual = i % 48
        if residual == 0:
            timestamp = input_values[i][0]
            daily_generation = 0
            for j in range(i, i + 48):
                daily_generation = daily_generation + float(input_values[j][1])
            str_to_append = str(timestamp) + ", " + str(daily_generation)
            daily_profile.payload.append(str_to_append)
    return daily_profile


# function to get monthly generation profile from 30-min input (1 year)
# @title: desired output title (= file name without extension)
# @half_hour_dataset: HASPR Dataset object containing one 30-min profile
# @return: HASPR Result object containing the corresponding monthly profile
def get_monthly_profile(title, half_hour_dataset):
    new_title = title + " - monthly"
    monthly_profile = Result(new_title)
    monthly_profile.payload.append("Time, Generation")
    input_values = half_hour_dataset.payload
    first_date = get_date(input_values[0][0])  # returns [year, month, day]
    year = first_date[0]
    monthly_totals = np.zeros(12)
    for i in range(0, len(input_values)):
        timestamp = input_values[i][0]
        generation = str(input_values[i][1])
        gen_value = 0
        if not generation.__contains__("N/A"):
            gen_value = float(input_values[i][1])
        current_date = get_date(timestamp)
        month = int(current_date[1])
        monthly_totals[month - 1] = monthly_totals[month - 1] + gen_value
    for j in range(0, 12):
        time_str = str(j+1) + "/" + str(year)
        gen_str = str(monthly_totals[j])
        str_to_append = time_str + ", " + gen_str
        monthly_profile.payload.append(str_to_append)
    return monthly_profile


# function to get total sum of generation profiles given a group of individual profiles
# @title: title of the Result to return
# @input_path: file path of the directory containing HASPR generation profiles (CSVs)
# @output_path: file path of output directory (needs to be created by user beforehand)
# @return: result object containing total generation profile (Wh vs. time)
def get_total_profiles(title, input_path, output_path):
    # get all file names in input_directory:
    file_names = []
    for (dirpath, dirnames, filenames) in walk(input_path):
        file_names.extend(filenames)

    print("\nCalculating total generation profile for {} sites...".format(len(file_names)))

    datasets = []

    # extract data from CSV files to Dataset objects:
    for fn in file_names:
        print("   -> Extracting data from {}".format(fn))
        d = Dataset("")
        file_path = input_path + osPathDelimiter + fn
        get_csv_data(file_path, d)
        datasets.append(d)

    print("\nProfile data extracted!")

    # initialize output:
    total_profiles = datasets[0].payload

    # add the rest of the profiles one by one:
    counter = 0
    for d_i in datasets[1:]:
        counter = counter + 1
        print("\n-> Summing values for site {}".format(counter))
        current_payload = d_i.payload
        for i in range(len(current_payload)):
            data_point = current_payload[i]
            gen_value = float(data_point[1])
            point_to_sum = (total_profiles[i])[1]
            # set nan's to zero
            if not float(point_to_sum) > 0:
                point_to_sum = 0
            # disregard new nan's
            if not float(gen_value) > 0:
                gen_value = 0
            new_value = float(point_to_sum) + float(gen_value)
            (total_profiles[i])[1] = str(new_value)

    print("\nBuilding result...")

    r = Result(title)
    r.format = "CSV"
    r.output_directory = output_path
    header = 'Time, Total Production [Wh/m2]'
    r.payload.append(header)

    for tp in total_profiles:
        time_string = str(tp[0])
        gen_string = str(tp[1])
        new_string = time_string + ', ' + gen_string
        r.payload.append(new_string)

    print("\nTotal profile result complete.")

    return r


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
# @return: array of light-weight file paths -> to be used for subsequent merging
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
        tar_path = input_directory + osPathDelimiter + fn
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
            file_path = output_directory + osPathDelimiter + f

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
    return light_weight_file_paths


# function to merge netcdf files
# @merge__directory: directory containing files to merge -> output will be written here
# @var_name: name of the variable of interest (netcdf name)
# @return: path to merged file
def merge_netcdf(merge_directory, var_name):
    file_names = []
    for (dirpath, dirnames, filenames) in walk(merge_directory):
        file_names.extend(filenames)

    print("\nMerging {} files...".format(len(file_names)))

    data_arrays_to_merge = []
    counter = 1
    for fn in file_names:
        ds_name = "tempDS" + str(counter)
        d = load_netcdf(ds_name, merge_directory + osPathDelimiter + fn)
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
    return path_out
