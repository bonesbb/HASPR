# HASPR
HASPR grants users the ability to model the output of solar arrays given high-resolution meteorological data.

High-Altitude Solar Power Research (HASPR) -> Case Study of Floating Solar in Switzerland

-----

Developer: Nicholas Eyring (neyring)

-----

HASPR’s scripts are segmented in two parts. The first part calculates generation profiles for sets of coordinates at a temporal resolution of 30 minutes and is the computational bottleneck. The second part consists of analysis scripts which are computationally insignificant in comparison with our POA model. This being the case, HASPR’s structure is designed to execute the first part on a high-performance computer and to execute the second part on a typical workstation.

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


