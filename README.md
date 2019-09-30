# HASPR
HASPR grants users the ability to model the output of solar arrays given high-resolution meteorological data.

High-Altitude Solar Power Research (HASPR) -> Case Study of Floating Solar in Switzerland

-----

Developer: Nicholas Eyring (neyring)

-----

HASPR’s scripts are segmented in two parts. The first part calculates generation profiles for sets of coordinates at a temporal resolution of 30 minutes and is the computational bottleneck. The second part consists of analysis scripts which are computationally insignificant in comparison with our POA model. This being the case, HASPR’s structure is designed to execute the first part on a high-performance computer and to execute the second part on a typical workstation.

-----

**Core Scripts:**

*datascrape.py*:			Script to extract light-weight data sets and merge files from large NetCDF4 directories.

*haspr.py*:				Background script/library containing classes, functions, and global variables.

**Generation Scripts:**

*batch_check.py*:			Checks if batches have successfully run. Outputs incomplete batch list.

*batch_submission_bf.py*:		Script for setting up brute force batch jobs for fixed-tilt optimizations on Euler.

*batch_submission_opt.py*:		Script for setting up batch jobs for fixed-tilt calculations on Euler.

*main_euler_fixed.py*:			Main script for Euler fixed-tilt batches. Sets parameters, runs models, and dumps data.

*main_euler_flat.py*:			Main script for Euler flat batches. Sets parameters, runs models, and dumps data.

*main_euler_tracking.py*:		Main script for Euler tracking batches. Sets parameters, runs models, and dumps data.

*optimization_results.py*:		Determines optimum fixed-tilt positions given directories of brute force output.

*organize_batch_output.py*:		Copies files from batch output to corresponding historic profile directories.

**Processing Scripts:**

*global_remove_leap.py*:		Removes leap days for a global panel configuration case.

*lower_resolution.py*: 			Converts data series to hourly, daily, or monthly resolution. 

*remove_leap_days.py*:			Script to remove leap days from a directory of generation profiles.

**Analysis Scripts:**

*average_aggregate_revenue.py*:		Outputs average bid and potential revenue given a directory of aggregate revenue profiles.

*average_individual_revenue.py*:	Script which averages individual revenue profiles from historic data.

*co2_offset.py*:			Calculates CO2-equivalent offset given generation profiles.

*expected_output_analysis.py*:		Computes aggregate lower bounds and historic variance given a directory of individual expected 						output.

*expected_site_output.py*:		Script to calculate expected output for one site given a directory of historic profiles.

*global_expected_site_output.py*:	Script to calculate expected output for all sites under a design configuration.

*lifetime_costs.py*:			Calculates costs given a CSV file of sites, panel surface area, and tilt angles.

*lifetime_revenue.py*:			Calculates yearly and cumulative revenue for system lifetime given a directory of revenue 						profiles.

*NPV_LCOE.py*:				Computes the NPV and LCOE given lifetime costs/revenues and expected generation profiles.

*revenue.py*:				Outputs revenue profiles for all generation profiles in a given directory.

*sum_individual.py*:			Script to calculate annual sums given generation profiles.

*supply_demand_mismatch.py*:		Computes the potential alleviation of supply/demand mismatches given generation profiles.

*total_expected_output.py*:		Script to calculate generation profiles in Wh from a directory of profiles in Wh per square 						meter.

*total_generation_profile.py*:		Script to calculate aggregate generation profiles given surface areas.

-----

**Adding a model to HASPR**

Make the following adjustments to haspr.py:
- Add the model to the "initialize" function, add the required datasets here as well
- Add path variables and Dataset class adjustments if new dataset was added
- Write the model’s function (adding results to the model’s “results” array)
- Add code to call the new function if the model’s name matches (in the Model class’ execute function)

-----

**Feeding a list of coordinates to HASPR**

HASPR’s solar research models generate results based on a set of coordinates provided by the user. This list of sites of interest needs to be prepared in the form of a .csv file with two columns:

- Column 1 = Site ID (integer)
- Column 2 = WGS 84 coordinates (string)

HASPR’s set_coordinates(path) function takes the file path of the list of coordinates in .csv form as its only argument. This function converts the WGS 84 coordinate string into decimal latitudes and longitudes before setting haspr.py’s global variable coordinates – an iterable list of each site’s latitude, longitude, and integer ID. HASPR’s generation profile models automatically calculate the output for each site in the coordinates list.

-----

**Creating batches to accelerate HASPR models**

We grant HASPR users the ability to segment their models’ parameter sweeps into multiple batches by setting the sweep_range field in the haspr.Model class. HASPR’s get_sweep_batches(full_sweep, batch_length) function returns an array of all sweep batches given the full sweep array and batch length as input. A researcher can then set-up multiple Model instances with the desired sweep ranges to run in parallel - exploiting HPC technologies to minimize runtime.

-----

**Euler script documentation**

The HASPR library contains three scripts for running batches on Euler: main_euler_flat.py for obtaining flat generation profiles (Case 1 – maximum 450 sites per batch), main_euler_tracking.py for obtaining full-tracking generation profiles (Case 2 – maximum 20 sites per batch), and main_euler_fixed.py for calculating fixed-tilt generation profiles (Cases 3 and 4 – maximum 20 sites per batch). The user defines individual jobs using the command line arguments described below:

*Flat Generation Profiles – main_euler_flat.py:*

Command line use: $ bsub python ./main_euler_flat.py [coords] [outputDir] [SISpath]

Description of arguments:
- coords:	Path to .csv coordinates file containing max 450 sites
- outputDir:	Path to desired output directory (e.g. …/out; needs to be created and empty beforehand)
- SISpath:	Path to SIS dataset (e.g. 2015 SIS data)

Example use: $ bsub python ./main_euler_flat.py coords/coords1_to_33.csv output/B6 datasets/2013/00_2013_SIS_merged.nc


*Full-Tracking Generation Profiles – main_euler_tracking.py:*

Command line use: $ bsub python ./main_euler_tracking.py [coords] [outputDir] [SISpath] [SIDpath]

Description of arguments:
- coords:	Path to .csv coordinates file containing max 20 sites
- outputDir:	Path to desired output directory (e.g. …/out; needs to be created and empty beforehand)
- SISpath:	Path to SIS dataset (e.g. 2015 SIS data)
- SIDpath:	Path to SID dataset (e.g. 2015 SID data)

Example use: $ bsub python ./main_euler_tracking.py coords/coords21_to_33.csv output/B14 datasets/2009/00_2009_SIS_merged.nc datasets/2009/01_2009_SID_merged.nc

*Fixed-Tilt Generation Profiles – main_euler_fixed.py:*

Command line use: $ bsub python ./main_euler_fixed.py [coords] [outputDir] [SISpath] [SIDpath] [optType] [sweepIndex]

Description of arguments:
- coords:	Path to .csv coordinates file containing 1 site (see Figure xx for format)
- outputDir:	Path to desired output directory (e.g. …/out; needs to be created and empty beforehand)
- SISpath:	Path to SIS dataset (e.g. 2017 SIS data)
- SIDpath:	Path to SID dataset (e.g. 2017 SID data)
- optType:	Optimization type (1 = azimuth sweep at a fixed 12-degree tilt, 2 = full sweep between 30 and 65 degree tilts)
- sweepIndex:	Index for sweep range (first index = 0; each index represents 20 profiles)
	
Example use:  $ bsub python ./main_euler_fixed.py coords/coords1.csv output/B31 datasets/2017/00_2017_SIS_merged.nc datasets/2017/01_2017_SID_merged.nc 1 0

**Note:** When running main_euler_fixed.py to calculate historic profiles after finding the optimum position, simply omit the optType and sweepIndex arguments and add the optimum azimuth and tilt in columns 3 and 4, respectively, of the .csv coordinates file. Instead of sweeping through positions in this case, the user can input 20 sites at once via the coords argument to define a batch.

**Note:** The path to the SAL dataset is hardcoded into the three Euler scripts since the entire dataset (spanning the years 2006-2015) is small enough to handle with one file.

**Note:** For memory management reasons, batches only incorporate one year of data (i.e. a batch will be defined for multiple sites over the same year instead of multiple years for one site).


