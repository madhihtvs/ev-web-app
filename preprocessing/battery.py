from distutils import dist
import pandas as pd
import math 
from datetime import timedelta
from preprocessing.clustering import near_points


def time_24(time):
    while time > 86400:
        time -= 86400
    return time

def charging_time(remaining_dist, current_soc):
    soc_required = remaining_dist / 0.75 
    soc_required = min(soc_required, 85)
    if soc_required > current_soc:
        time = ((soc_required - current_soc)/5) * 15
    else:
        time = ((soc_required)/5) * 15

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
        
        while len(df_1) < 1:
            dist_travelled -= 0.5
            dist_left += 0.5
            possible_dist -= 0.5
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
                    print("Leg Start:", str(trip_start).split(".", 1)[0])
                    leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))
                    total_time += (possible_dist/ave_speed) * 3600
                    leg_end = str(leg_end).split(".", 1)[0]
                    print("Leg End:", str(leg_end))
                    print("Stop:", stop)
                    print("Distance Travelled in Total:", dist_travelled, "km")
                    print("Distance Travelled before this Stop:", possible_dist, "km")

                    print("Charge at:",a)
                    print("Charging Start Time:", str(leg_end))
                    print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")
    
                    time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                    time_end = timedelta(seconds = time_end)
                    print("Charging End Time:", str(time_end).split(".", 1)[0])
                    print("Distance Left:", total_distance - dist_travelled, "km")
                    total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                    
                    print("Updated Charge:",b, "%")
                    print("*************")

                    yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b ]

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

                    yield [b, dist_left, b-soc_reduction]

                    dist_left = dist_left - dist_left
                    print("Trip Duration:",total_time/3600, "hrs")
                    sec = get_sec(trip_start_at) + total_time
                    td = timedelta(seconds=sec)
                    print("Trip End:",td )
                    print("Reached Destination:", dist_left, "km left")
                     
                    yield [sec, night_travel, b - soc_reduction]
                    break
                    
                else:
                    print("No More Stops, Final Lap")
                    print("Starting SoC:", new_soc, "%")
                    print(f"Distance Travelled in Total: {dist_travelled} km")
                    print("Travelling", dist_travelled, "km now")
                    
                    print("Current SoC:", new_soc - soc_reduction, "%")

                    yield [dist_left, new_soc - soc_reduction]

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
        leg_end = str(leg_end).split(".", 1)[0]
        print("Leg End:",str(leg_end).rstrip("."))
        print("Stop:", stop)
        print("Distance Travelled in Total:", dist_travelled, "km")
        print("Distance Travelled before this Stop:", possible_dist, "km")
        
        print("Charge at:", a)
        print("Charging Start Time:", str(leg_end))
        print("Charging Time:", charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
        time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
        time_end = timedelta(seconds = time_end)
        print("Charging End Time:", str(time_end).split(".", 1)[0])
                    
        print("Distance Left:", total_distance - dist_travelled, "km")
        
        print("Updated Charge:",new_soc, "%")
        print("*************")

        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ]

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


def no_night(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, range_needed,
ave_speed, trip_start_at, trip_start, total_time):
    dist_left = total_distance - dist_travelled

    possible_range = (100 - min_threshold)/100 * range_ev

    while dist_left > 0:
        if initial_soc < min_threshold:
            print("Vehicle is unable to travel safely")
            break
        
        
        possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold))
        dist_travelled += possible_dist
        dist_travelled = min(total_distance, dist_travelled)
        dist_left = total_distance - dist_travelled
        df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]

        while len(df_1) < 1:
            
            dist_travelled += 0.5
            dist_left -= 0.5
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
           
                print("Leg End:",str(leg_end))
                print("Stop:", stop)
                print("Distance Travelled in Total:", dist_travelled, "km")
                print("Distance Travelled before this Stop:", possible_dist, "km")

                    
                    
                if len(str(leg_end).split(".", 1)[0]) < 8:
                    if "02:00:00" <= "0" + str(leg_end).split(".", 1)[0] <= "06:00:00":
                        print("Charge at:", a)
                        print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                        print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
                        time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        time_end = timedelta(seconds = time_end)
                        print("Charging End Time:", str(time_end))
                        print("Distance Left:", total_distance - dist_travelled, "km")
                        total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        print("Total Time:", total_time/3600)
                        new_soc = 100
                        print("Updated Charge:",new_soc, "%")
            
                        b = new_soc
                        print("*************")
                        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],b]
                     


                    else:

                        print("Charge at:",a)
                        print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                        print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")
                        time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        time_end = timedelta(seconds = time_end)
                        print("Charging End Time:", str(time_end))
                        print("Distance Left:", total_distance - dist_travelled, "km")
                        total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                         
                        print("Updated Charge:",b, "%")
               
                        b = new_soc
                        print("*************")
                        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b]
                


        
                elif len(str(leg_end).split(".", 1)[0]) == 8:
                    if "02:00:00" <= str(leg_end).split(".", 1)[0] <= "06:00:00":


                        print("Charge at:", a)
                        print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                        print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
                        time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        time_end = timedelta(seconds = time_end)
                        print("Charging End Time:", str(time_end))
                        print("Distance Left:", total_distance - dist_travelled, "km")
                        total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        print("Total Time:", total_time/3600)
                        new_soc = 100
                        print("Updated Charge:",new_soc, "%")
                
                        b = new_soc
                        print("*************")

                        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],b]
              

                    else:

                        print("Charge at:",a)
                        print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                        print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")
                        time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        time_end = timedelta(seconds = time_end)
                        print("Charging End Time:", str(time_end))
                        print("Distance Left:", total_distance - dist_travelled, "km")
                        total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                          
                        print("Updated Charge:",b, "%")
            
                        print("*************")
                        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b]
                
                                

                print("Travelling", dist_left, "km now")
                soc_reduction = dist_left / (range_ev/100)
                print("Leg Start:", str(time_end))
                leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600)))
            
                print("Leg End:",str(leg_end))                
                print("Current SoC:", b - soc_reduction, "%")
                yield [b, dist_left, b-soc_reduction]

                dist_left = dist_left - dist_left
                print("Trip Duration:",total_time/3600, "hrs")
                sec = get_sec(trip_start_at) + total_time
                td = timedelta(seconds=sec)
                print("Trip End:",td )
                print("Reached Destination:", dist_left, "km left")
                     
                yield [sec, False , b - soc_reduction]
                break

        

            else:

                print("No More Stops, Final Lap")
                print("Starting SoC:", new_soc, "%")
                print(f"Distance Travelled in Total: {dist_travelled} km")
                print("Travelling", possible_dist, "km now")
                    
                print("Current SoC:", new_soc - soc_reduction, "%")

                yield [new_soc, possible_dist, new_soc - soc_reduction]

                dist_left = dist_left - dist_left
                print("Trip Duration:",total_time/3600, "hrs")
                sec = get_sec(trip_start) + total_time
                td = timedelta(seconds=sec)
                print("Trip End:",td )

                yield [sec, False , new_soc - soc_reduction]
                print("Reached Destination:", dist_left, "km left")
                break
        
        print("Starting SoC: ", initial_soc, "%")
        print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%")
        print("Leg Start:", trip_start)
        leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))

        print("Leg End:",str(leg_end))
        print("Stop:", stop)
        print("Distance Travelled in Total:", dist_travelled, "km")
        print("Distance Travelled before this Stop:", possible_dist, "km")
        

    

        if len(str(leg_end).split(".", 1)[0]) < 8:
            if "02:00:00" <= "0" + str(leg_end).split(".", 1)[0] <= "06:00:00":
        
                print("Charge at:", a)
                print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
                time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                time_end = timedelta(seconds = time_end)
                print("Charging End Time:", str(time_end))
                print("Distance Left:", total_distance - dist_travelled, "km")
                total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                print("Total Time:", total_time/3600)
                new_soc = 100
                print("Updated Charge:",new_soc, "%")

                print("*************")
                
                yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],new_soc ]

                

                

            else:
                print("Charge at:", a)
                print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                print("Charging Time:", charging_time(dist_left,initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
                time_end = get_sec(str(leg_end)) + charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                time_end = timedelta(seconds = time_end)
                print("Charging End Time:", str(time_end))
                print("Distance Left:", total_distance - dist_travelled, "km")
                total_time += charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                print("Total Time:", total_time/3600)
                print("Updated Charge:",new_soc, "%")

                print("*************")

                yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ]
    

        
        elif len(str(leg_end)).split(".", 1)[0] == 8:
            if "02:00:00" <= str(leg_end).split(".", 1)[0] <= "06:00:00":

                
                print("Charge at:", a)
                print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
                time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                time_end = timedelta(seconds = time_end)
                print("Charging End Time:", str(time_end))
                print("Distance Left:", total_distance - dist_travelled, "km")
                total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                print("Total Time:", total_time/3600)
                new_soc = 100
                print("Updated Charge:",new_soc, "%")
                print("*************")

                yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],new_soc ]


            else:

                print("Charge at:", a)
                print("Charging Start Time:", str(leg_end).split(".", 1)[0])
                print("Charging Time:", charging_time(dist_left,initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs")
                time_end = get_sec(str(leg_end)) + charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                time_end = timedelta(seconds = time_end)
                print("Charging End Time:", str(time_end))
                print("Distance Left:", total_distance - dist_travelled, "km")
                total_time += charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                print("Total Time:", total_time/3600)
                print("Updated Charge:",new_soc, "%")

                print("*************")

                yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ]



        total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
        initial_soc = new_soc
        stop += 1

        trip_start = str(time_end)


def own_rest(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, range_needed,
    ave_speed, trip_start_at, trip_start, total_time, rest_lat, rest_lon,distance_travelled_by_rest_place): 

    dist_left = total_distance - dist_travelled
    possible_range = (100 - min_threshold)/100 * range_ev
    rest_lat = float(rest_lat)
    rest_lng = float(rest_lon)


    chargefunction = charge_and_go(df, initial_soc, min_threshold, distance_travelled_by_rest_place, dist_travelled, range_ev, stop, 15, range_needed, 
    ave_speed, trip_start_at, trip_start, total_time)

    lst = {}
    step = 1
    for value in chargefunction: 
            lst[step] = value
            step += 1

  
    keys = list(lst.keys())

    current_soc = lst[keys[-1]][-1]
    trip_end_sec = lst[keys[-1]][0]
    trip_end = timedelta(seconds=trip_end_sec)

    yield [lst]


    dist_left = total_distance - distance_travelled_by_rest_place
    dist_travelled = distance_travelled_by_rest_place
  

    df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(distance_travelled_by_rest_place) ) & (df['distance_travelled_till_here'] <= math.ceil(distance_travelled_by_rest_place+0.5))]
    
    while len(df_1) < 1:
        dist_travelled -= 0.5
        dist_left += 0.5
        df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]

    df_1.sort_values(by = ['Distance_to_CS'])
    idx = df_1.index[0]
    a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]]
        

    print("Charge at:", a)
    print("Charging Start Time:", str(trip_end).split(".", 1)[0])
    print("Charging Time:", charging_full(current_soc)[1], "hrs")
    time_end = get_sec(str(trip_end)) + charging_full(current_soc)[1] * 3600
    time_end = timedelta(seconds = time_end)
    print("Charging End Time:", str(time_end))
    print("Distance Left:", dist_left, "km")
    total_time += charging_full(current_soc)[1] * 3600
    print("Total Time:", total_time/3600)
    initial_soc = 100
    print("Updated Charge:",initial_soc, "%")
    print("*************")

    yield [current_soc, rest_lat, rest_lng, charging_full(current_soc)[1], initial_soc]

    trip_start = str(time_end)




    while dist_left > 0:
        if initial_soc < min_threshold:
            print("Vehicle is unable to travel safely")
            break

        possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold))
 
        if dist_left <= possible_dist:
            soc_reduction = dist_left / (range_ev/100)
            new_soc = initial_soc - (possible_dist/ (range_ev/100))

            if new_soc - soc_reduction < min_threshold:
                place = True
                possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold))
                dist_travelled += possible_dist
                dist_travelled = min(total_distance, dist_travelled)
                dist_left = total_distance - dist_travelled
                df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
            
                while len(df_1) < 1:
                    dist_travelled -= 0.5
                    dist_left += 0.5
                    possible_dist -= 0.5
                    df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
                    print(df_1)
                    if possible_dist < 10:
                        place = False
                        break

                if place == True:
                    df_1.sort_values(by = ['Distance_to_CS'])
                    idx = df_1.index[0]
                    a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]]
                        
                    range_needed = range_ev/100 * (final_threshold - min_threshold)
                    b = min(initial_soc - (possible_dist/ (range_ev/100)) + charging_time(dist_left+range_needed, min_threshold)[0],100)

                    print("Starting SoC: ", initial_soc, "%")
                    print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%")
                    print("Leg Start:", trip_start)
                    leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))
        
                    print("Leg End:",str(leg_end))
                    print("Stop:", stop)
                    print("Distance Travelled in Total:", dist_travelled, "km")
                    print("Distance Travelled before this Stop:", possible_dist, "km")
                    print("Charge at:",a)
                    print("Charging Start Time:", str(leg_end))
                    print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")
        
                    time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                    time_end = timedelta(seconds = time_end)
                    print("Charging End Time:", str(time_end).split(".", 1)[0])
                    print("Distance Left:", total_distance - dist_travelled, "km")
                    total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600
                        
                    print("Updated Charge:",b, "%")
                    print("*************")
            
                    yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b]
            
                    

                    print("Travelling", dist_left, "km now")
                    print("Leg Start:", str(time_end))
                    leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600)))
                    total_time += (dist_left/ave_speed) * 3600
                    print("Leg End:",str(leg_end))      
                    soc_reduction = dist_left / (range_ev/100)          
                    print("Current SoC:", new_soc - soc_reduction, "%")
                    yield [b, dist_left, b-soc_reduction]
                    dist_left = dist_left - dist_left
                    print("Trip Duration:",total_time/3600, "hrs")
                    sec = get_sec(trip_start_at) + total_time
                    td = timedelta(seconds=sec)
                    print("Trip End:",td )
                    print("Reached Destination:", dist_left, "km left")
                    yield [sec, False , b - soc_reduction]
                    break

                else:
                    dist_travelled -= possible_dist
                    dist_left = total_distance - dist_travelled
                    soc_reduction = dist_left / (range_ev/100)
                    new_soc = 100
                    print("Starting SoC:", new_soc, "%")
                    print("Travelling", dist_left, "km now")
                    print("Leg Start:", str(time_end))
                    leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600)))
                    total_time += (dist_left/ave_speed) * 3600
                    print("Leg End:",str(leg_end))      
                    soc_reduction = dist_left / (range_ev/100)          
                    print("Current SoC:", new_soc - soc_reduction, "%")

                    yield [new_soc, dist_left, new_soc-soc_reduction]

                    dist_left = dist_left - dist_left
                    print("Trip Duration:",total_time/3600, "hrs")
                    sec = get_sec(trip_start_at) + total_time
                    td = timedelta(seconds=sec)
                    print("Trip End:",td )
                    print("Reached Destination:", dist_left, "km left")
                    yield [sec, False , new_soc - soc_reduction]
                    break




            else: 
                new_soc = 100
                print("No More Stops, Final Lap")
                print("Starting SoC:", new_soc, "%")
                print(f"Distance Travelled in Total: {dist_travelled} km")
                print("Travelling", possible_dist, "km now")
                    
                print("Current SoC:", new_soc - soc_reduction, "%")

                yield [new_soc, possible_dist, new_soc - soc_reduction]

                dist_left = dist_left - dist_left
                print("Trip Duration:",total_time/3600, "hrs")
                sec = get_sec(trip_start) + total_time
                td = timedelta(seconds=sec)
                print("Trip End:",td )

                yield [sec, False , new_soc - soc_reduction]
                print("Reached Destination:", dist_left, "km left")
                break

def station_coordinates(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time):

    possible_range = (initial_soc - min_threshold)/100 * range_ev
    lst = {}
    if possible_range >= total_distance:
        lst = "Route from Origin to Destination with No Charging" 
    else:
        stop = 1
        for value in charge_and_go(df, initial_soc, min_threshold, total_distance, 
        dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time): 
            lst[stop] = value
            stop += 1

    return lst

    
def station_coordinates_no_night(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time):

    possible_range = (initial_soc - min_threshold)/100 * range_ev
    lst = {}
    if possible_range >= total_distance:
        lst = "Route from Origin to Destination with No Charging" 
    else:
        stop = 1
        for value in no_night(df, initial_soc, min_threshold, total_distance, 
        dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time): 
            lst[stop] = value
            stop += 1

    return lst



def station_coordinates_own_rest(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time,
    rest_lat, rest_lon,distance_travelled_by_rest_place):

    possible_range = (initial_soc - min_threshold)/100 * range_ev
    lst = {}
    if possible_range >= total_distance:
        lst = "Route from Origin to Destination with No Charging" 
    else:
        stop = 1
        for value in own_rest(df, initial_soc, min_threshold, total_distance, 
        dist_travelled, range_ev, stop, final_threshold, range_needed,
    ave_speed, trip_start_at, trip_start, total_time, rest_lat, rest_lon,distance_travelled_by_rest_place): 
            print(value)
            lst[stop] = value
            stop += 1

    return lst



