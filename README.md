# HASPR
Solar energy research environment written in Python

High-Altitude Solar Power Research (HASPR) -> Case Study of Floating Solar in Switzerland

-----

Developer: Nicholas Eyring (neyring)

-----

HASPR’s scripts are segmented in two parts: First part = hapsr.py coupled with “main” scripts for running our POA model. The first – calculating generation profiles for sets of coordinates at a temporal resolution of 30 minutes – is the computational bottleneck. The second part consists of analysis scripts which are computationally insignificant in comparison with our POA model. This being the case, HASPR’s structure is designed to execute the first part on a high-performance computer and to execute the second part on a typical workstation.

-----

**Adding a model to HASPR**

Make the following adjustments to haspr.py:
-	Add the model to the "initialize" function, add the required datasets here as well
-	Add path variables and Dataset class adjustments if new dataset was added
-	Write the model’s function (adding results to the model’s “results” array)
-	Add code to call the new function if the model’s name matches (in the Model class’ execute function)

-----

**Feeding a list of coordinates to HASPR**

