import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime

# Establish x-axis:
start_date = datetime.datetime(2017, 1, 1, 0)  # we use 2017 as a generic non-leap year for the plot
datetime_axis = [start_date + datetime.timedelta(minutes=(x*30)) for x in range(17520)]

# set the locator and format to display months on the x-axis:
locator = mdates.MonthLocator()
month_format = mdates.DateFormatter('%b')  # displays 'Jan', 'Feb', etc.

# Plot of average output and variance in output:
plt.subplot(2, 1, 1)
#plt.plot(datetime_axis, average)
plt.ylabel("Expected Output [Wh/m2]")
x = plt.gca().xaxis
x.set_major_locator(locator)
x.set_major_formatter(month_format)

plt.subplot(2, 1, 2)
#plt.plot(datetime_axis, normalized_variance)
x = plt.gca().xaxis
x.set_major_locator(locator)
x.set_major_formatter(month_format)
plt.ylabel("Variance as % of Expected Output")
plt.xlabel("Time of Year")
plt.show()


#plot_output_path = outputDirectory + osPathDelimiter + "test_plot.png"
#plt.savefig(plot_output_path)