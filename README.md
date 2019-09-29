# HASPR
Solar energy research environment written in Python

High-Altitude Solar Power Research (HASPR) -> Case Study of Floating Solar in Switzerland

-----

Developer: Nicholas Eyring (neyring)

-----

*Adding a model to HASPR*

Make the following adjustments to haspr.py:
-	Add the model to the "initialize" function, add the required datasets here as well
-	Add path variables and Dataset class adjustments if new dataset was added
-	Write the model’s function (adding results to the model’s “results” array)
-	Add code to call the new function if the model’s name matches (in the Model class’ execute function)

