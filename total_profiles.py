import haspr
from haspr import Result


generationProfilesDir = "D:\\HASPR Flat Output\\Flat Generation Profiles"  # path to gen. profiles directory
haspr.outputDirectory = "D:\\HASPR Output"  # results and output directory
title = "Total Flat Generation Profile"  # title of resulting output CSV

d = haspr.get_total_profiles(title, generationProfilesDir)

# initialize output:
total_profiles = d[0].payload

# add the rest of the profiles one by one:
for d_i in d[1:]:
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

r = Result(title)
r.format = "CSV"
r.output_directory = ...
header = 'Time, Total Production [W/m2]'
r.payload.append(header)

for tp in total_profiles:
    time_string = str(tp[0])
    gen_string = str(tp[1])
    new_string = time_string + ', ' + gen_string
    r.payload.append(new_string)











