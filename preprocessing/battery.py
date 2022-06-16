import pandas as pd
import math 
from datetime import timedelta


def time_24(time):
    while time > 86400:
        time -= 86400
    return time

def charging_time(remaining_dist, current_soc):
    soc_required = remaining_dist / 0.75 
    soc_required = min(soc_required, 85)
    time = ((soc_required - current_soc)/5) * 15
    return(soc_required, time/60)

def charging_full(current_soc):
    soc_required = 100
    time = ((soc_required - current_soc)/5) * 15
    return(soc_required, time/60)


def get_sec(time_str):
    """Get seconds from time."""
    if "day" in time_str:
        time_str = time_str.split(',')[1].lstrip()
    time_str = time_str.split('.', 1)[0]
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)



def charge_and_go(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, range_needed,
ave_speed, trip_start_at, trip_start, total_time):
    dist_left = total_distance - dist_travelled
    night_travel = False
    possible_range = (100 - min_threshold)/100 * range_ev

    while dist_left > 0:
        if initial_soc < min_threshold:
            print("Vehicle is unable to travel safely")
            break
        
    

        possible_dist = range_ev/100 * (initial_soc-min_threshold)
        dist_travelled += possible_dist
        dist_left = total_distance - dist_travelled
        df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
        df_1.sort_values(by = ['Distance_to_CS'])
        idx = df_1.index[0]
        a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]]
        new_soc = charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[0]
 
        
        

        while df_1.iloc[0]['Distance_to_CS'] > 0.5:
            dist_travelled = dist_travelled - 1
            possible_dist -= 1
            dist_left = dist_left + 1
            df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
            df_1.sort_values(by = ['Distance_to_CS'])
            idx = df_1.index[0]
            a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]]
            


        if dist_left <= possible_dist:
            
                
                #dist_travelled += dist_left
                #dist_left = 0
                soc_reduction = dist_left / (range_ev/100)
                #Checking if safe for travel, if not recharge
                new_soc = initial_soc - (possible_dist/ (range_ev/100))
                if new_soc - soc_reduction < min_threshold:
            
                
                    range_needed = range_ev/100 * (final_threshold - min_threshold)

        
                    b = min(initial_soc - (possible_dist/ (range_ev/100)) + charging_time(dist_left+range_needed, min_threshold)[0],100)

                    print("Starting SoC: ", initial_soc, "%")
                    print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%")
                    print("Leg Start:", trip_start)
                    leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))
                    total_time += (possible_dist/ave_speed) * 3600
                    print("Leg End:",str(leg_end))
                    print("Stop:", stop)
                    print("Distance Travelled in Total:", dist_travelled, "km")
                    print("Distance Travelled before this Stop:", possible_dist, "km")

                    print("Charge at:",a)
                    print("Charging Start Time:", str(leg_end))
                    print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")
                    time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                    time_end = timedelta(seconds = time_end)
                    print("Charging End Time:", str(time_end))
                    print("Distance Left:", total_distance - dist_travelled, "km")
                    total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                    
                    print("Updated Charge:",b, "%")
                    print("*************")
                    yield [a[2], a[3]]
                    
                    if len(str(leg_end)) < 8:
                        if "02:00:00" <= "0" + str(leg_end) <= "06:00:00":
                            night_travel = True
        
                    elif len(str(leg_end)) == 8:
                        if "02:00:00" <= str(leg_end) <= "06:00:00":
                            night_travel = True
                    
                    elif len(str(time_end)) < 8:
                        if "02:00:00" <= "0" + str(time_end) <= "06:00:00":
                            night_travel = True
                    
                    elif len(str(time_end)) == 8:
                        if "02:00:00" <= str(time_end) <= "06:00:00":
                            night_travel = True

                    print("Travelling", dist_left, "km now")
                    print("Leg Start:", str(time_end))
                    leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600)))
                    total_time += (dist_left/ave_speed) * 3600
                    print("Leg End:",str(leg_end))
                    
                    print("Current SoC:", b - soc_reduction, "%")
                    dist_left = dist_left - dist_left
                    print("Trip Duration:",total_time/3600, "hrs")
                    sec = get_sec(trip_start_at) + total_time
                    td = timedelta(seconds=sec)
                    print("Trip End:",td )
                    print("Reached Destination:", dist_left, "km left")
                     
                    return sec, night_travel, td, b - soc_reduction

                else:
                    print("No More Stops, Final Lap")
                    print("Starting SoC:", new_soc, "%")
                    print(f"Distance Travelled in Total: {dist_travelled} km")
                    print("Travelling", dist_travelled, "km now")
                    
                    print("Current SoC:", new_soc - soc_reduction, "%")
                    dist_left = dist_left - dist_left
                    print("Trip Duration:",total_time/3600, "hrs")
                    sec = get_sec(trip_start) + total_time
                    td = timedelta(seconds=sec)
                    print("Trip End:",td )
                    print("Reached Destination:", dist_left, "km left")
        
        print("Starting SoC: ", initial_soc, "%")
        print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%")
        print("Leg Start:", trip_start)
        leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))
        total_time += (possible_dist/ave_speed) * 3600
        print("Leg End:",str(leg_end))
        print("Stop:", stop)
        print("Distance Travelled in Total:", dist_travelled, "km")
        print("Distance Travelled before this Stop:", possible_dist, "km")
        
        print("Charge at:", a)
        print("Charging Start Time:", str(leg_end))
        print("Charging Time:", charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
        time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
        time_end = timedelta(seconds = time_end)
        print("Charging End Time:", str(time_end))
                    
        print("Distance Left:", total_distance - dist_travelled, "km")
        
        print("Updated Charge:",new_soc, "%")
        print("*************")

        yield [a[2],a[3]]

        if len(str(leg_end)) < 8:
            if "02:00:00" <= "0" + str(leg_end) <= "06:00:00":
                night_travel = True
        
        elif len(str(leg_end)) == 8:
            if "02:00:00" <= str(leg_end) <= "06:00:00":
                night_travel = True
        
        elif len(str(time_end)) < 8:
            if "02:00:00" <= "0" + str(time_end) <= "06:00:00":
                night_travel = True
        
        elif len(str(time_end)) == 8:
            if "02:00:00" <= str(time_end) <= "06:00:00":
                night_travel = True

         

        total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
        initial_soc = new_soc
        stop += 1
        trip_start = str(time_end)
    

def station_coordinates(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time):
    lst = {}
    stop = 1
    for value in charge_and_go(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time): 
        lst[stop] = value
        stop += 1

    return lst