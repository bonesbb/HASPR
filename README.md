# HASPR
Solar energy research environment written in Python

High-Altitude Solar Power Research (HASPR) -> Case Study of Floating Solar in Switzerland

-----

Developer: Nicholas Eyring (neyring)

-----

HASPR’s scripts are segmented in two parts: First part = hapsr.py coupled with “main” scripts for running our POA model. The first, calculating generation profiles for sets of coordinates at a temporal resolution of 30 minutes, is the computational bottleneck. The second part consists of analysis scripts which are computationally insignificant in comparison with our POA model. This being the case, HASPR’s structure is designed to execute the first part on a high-performance computer and to execute the second part on a typical workstation.

-----

**Adding a model to HASPR**

Make the following adjustments to haspr.py:
-	Add the model to the "initialize" function, add the required datasets here as well
-	Add path variables and Dataset class adjustments if new dataset was added
-	Write the model’s function (adding results to the model’s “results” array)
-	Add code to call the new function if the model’s name matches (in the Model class’ execute function)

-----

**Feeding a list of coordinates to HASPR**

HASPR’s solar research models generate results based on a set of coordinates provided by the user. This list of sites of interest needs to be prepared in the form of a .csv file with two columns:

- Column 1 = Site ID (integer)
- Column 2 = WGS 84 coordinates (string)

HASPR’s set_coordinates(path) function takes the file path of the list of coordinates in .csv form as its only argument. This function converts the WGS 84 coordinate string into decimal latitudes and longitudes before setting haspr.py’s global variable coordinates – an iterable list of each site’s latitude, longitude, and integer ID. HASPR’s generation profile models automatically calculate the output for each site in the coordinates list.

-----

**Creating batches to accelerate HASPR models**

We grant HASPR users the ability to segment their models’ parameter sweeps into multiple batches by setting the sweep_range field in the haspr.Model class. HASPR’s get_sweep_batches(full_sweep, batch_length) function returns an array of all sweep batches given the full sweep array and batch length as input. A researcher can then set-up multiple Model instances with the desired sweep ranges to run in parallel - exploiting HPC technologies to minimize runtime.
