import pandas as pd
import math 
from datetime import timedelta
from preprocessing.clustering import near_points



def charging_time(remaining_dist, current_soc):
    """Getting time and updated soc after charging till max of 85"""
    soc_required = remaining_dist / 0.75 
    soc_required = min(soc_required, 85)
    if soc_required > current_soc:
        time = ((soc_required - current_soc)/5) * 15
    else:
        time = ((soc_required)/5) * 15

    return(soc_required, time/60)

def charging_full(current_soc):
    """Charging full till 100 percent since we are halting at a specific place overnight"""
    soc_required = 100
    time = ((soc_required - current_soc)/5) * 15
    return(soc_required, time/60)


def get_sec(time_str):
    """Get seconds from time format HH:MM:SS"""
    if "day" in time_str:
        time_str = time_str.split(',')[1].lstrip()
    time_str = time_str.split('.', 1)[0]
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)



def charge_and_go(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, range_needed,
ave_speed, trip_start_at, trip_start, total_time):
    """Default method of finding optimal charging stations"""
    try:

        dist_left = total_distance - dist_travelled #Find distance left
        night_travel = False #Set flag of night travel to be False
        possible_range = (100 - min_threshold)/100 * range_ev # Finding possible range that can be covered (Not used)

        while dist_left > 0: # Continuous loop till dist_left becomes zero
            if initial_soc < min_threshold: # If the initial soc is lesser than min threshold, cannot travel, break loop
                print("Vehicle is unable to travel safely")
                break
            
        

            possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold)) # Calculate distance that can be covered with current soc or distance left whichever is lesser
            dist_travelled += possible_dist # Add possible distance to distance travelled
            dist_left = total_distance - dist_travelled # Calculate distance left after increasing distance travelled
            df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))] #Slicing dataframe of charging stations to specific distance of distance travelled
            
            while len(df_1) < 1: #If there are no charging stations in the specified distance above, then run this loop
                dist_travelled -= 0.5 # decrease distance travelled by half a kilometre in each iteration
                dist_left += 0.5
                possible_dist -= 0.5
                df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))] #Slice dataframe to check if a station exists

            
            df_1.sort_values(by = ['Distance_to_CS']) # Sort dataframe smallest distance to charging station
            idx = df_1.index[0] # Retrieving index
            a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]] # Getting information of charging station from dataframe
            new_soc = charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[0] # Get updated soc after charging at the station
    
            
            

            while df_1.iloc[0]['Distance_to_CS'] > 0.5: # If the charging station is more than 0.5 km, we find a new one
                dist_travelled = dist_travelled - 1
                possible_dist -= 1
                dist_left = dist_left + 1
                df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
                df_1.sort_values(by = ['Distance_to_CS'])
                idx = df_1.index[0]
                a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]]
                


            if dist_left <= possible_dist:
                #Terminaing condition happens here where distance left is lesser than or equal to possible distance that can be travelled
            
                    
                    # Calculating the soc that would be reduced
                    soc_reduction = dist_left / (range_ev/100)
                    #Checking if safe for travel, if not recharge
                    new_soc = initial_soc - (possible_dist/ (range_ev/100))
                    if new_soc - soc_reduction < min_threshold: #if the new soc after travel of this leg would be lesser than min threshold, we need to charge
                
                        # Check the distance needed for the final leg based on the arrival soc requested by the user
                        range_needed = range_ev/100 * (final_threshold - min_threshold)

                        # Calculate the new soc based on the range needed but max would be 100
                        b = min(initial_soc - (possible_dist/ (range_ev/100)) + charging_time(dist_left+range_needed, min_threshold)[0],100)

                        print("Starting SoC: ", initial_soc, "%") # starting soc of leg
                        print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%") # current soc after travelling leg
                        print("Leg Start:", str(trip_start).split(".", 1)[0]) #time of leg start
                        leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600))) # calculating time of leg end
                        total_time += (possible_dist/ave_speed) * 3600 #adding leg trip duration to total time
                        leg_end = str(leg_end).split(".", 1)[0] #formatting leg end
                        print("Leg End:", str(leg_end)) # Displaying leg end time
                        print("Stop:", stop) # Stop number
                        print("Distance Travelled in Total:", dist_travelled, "km") # Total distance travelled so far
                        print("Distance Travelled before this Stop:", possible_dist, "km") # Distance travelled in this leg

                        print("Charge at:",a) # Location of charging stations
                        print("Charging Start Time:", str(leg_end)) # Charging start time
                        print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs") # Charging duration in hours
        
                        time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 #Getting charging end time
                        time_end = timedelta(seconds = time_end) # converting seconds to proper time
                        print("Charging End Time:", str(time_end).split(".", 1)[0]) #Charging End Time display
                        print("Distance Left:", total_distance - dist_travelled, "km") # Showing distance left
                        total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Add charging duration to total time
                        
                        print("Updated Charge:",b, "%") #Display updated charge
                        print("*************")

                        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b ] #yield results to be used in display of HTML info

                        #Check if there is any charging requirement between 2 am and 6 am. If there is, then night travel is set to True
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
    
                        print("Travelling", dist_left, "km now") # Printing distance being travelled in the last leg
                        print("Leg Start:", str(time_end)) # Printing start of leg
                        leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600))) # Calculate leg end time
                        total_time += (dist_left/ave_speed) * 3600 # Add last leg duration to total time
                        print("Leg End:",str(leg_end)) # Print end of leg
                        
                        print("Current SoC:", b - soc_reduction, "%") # Print current soc after last leg

                        yield [b, dist_left, b-soc_reduction] # Yielding current soc, distance left and arrival soc

                        dist_left = dist_left - dist_left # Setting distance left to zero
                        print("Trip Duration:",total_time/3600, "hrs") # Printing total duration
                        sec = get_sec(trip_start_at) + total_time # Getting trip end time in seconds
                        td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                        print("Trip End:",td ) # Printing trip end time
                        print("Reached Destination:", dist_left, "km left") # Printing destination reached 
                        
                        yield [sec, night_travel, b - soc_reduction] # yielding final time, night travel flag and arrival soc
                        break # force break from program
                        
                    else:
                   
                        
                        print("No More Stops, Final Lap") # If the last leg is safe to be travelled using current soc
                        print("Starting SoC:", new_soc, "%") # print starting soc
                        print(f"Distance Travelled in Total: {dist_travelled} km") # printing distance travelled in total
                        print("Travelling", dist_left, "km now") # printing distance being travelled now
                        
                        print("Current SoC:", new_soc - soc_reduction, "%") # print current soc after this leg

                        yield [dist_left, new_soc - soc_reduction] #yield distance left and final soc

                        dist_left = dist_left - dist_left # updating distance left to zero
                        print("Trip Duration:",total_time/3600, "hrs") #print total duration
                        sec = get_sec(trip_start) + total_time # Getting trip end time in seconds
                        td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                        print("Trip End:",td )  # Printing trip end time
                        print("Reached Destination:", dist_left, "km left") # Printing destination reached 
            
            print("Starting SoC: ", initial_soc, "%") #Priting initial soc if it did not go terminating stage
            print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%") # Getting soc if possible distance is being travlled
            print("Leg Start:", trip_start) # Printing trip start time
            leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600))) # Calculating leg end time
            total_time += (possible_dist/ave_speed) * 3600 # Adding leg duration to total time 
            leg_end = str(leg_end).split(".", 1)[0] # Formatting leg duration
            print("Leg End:",str(leg_end).rstrip(".")) # Print leg end time
            print("Stop:", stop) # Printing stop number
            print("Distance Travelled in Total:", dist_travelled, "km") # Printing total distance travelled
            print("Distance Travelled before this Stop:", possible_dist, "km") # Printing possible distance in this leg
            
            print("Charge at:", a) # Printing location of charging station
            print("Charging Start Time:", str(leg_end))# Charging start time
            print("Charging Time:", charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # Charging duration in hours
            time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 #Getting charging end time
            time_end = timedelta(seconds = time_end) # converting seconds to proper time
            print("Charging End Time:", str(time_end).split(".", 1)[0])  #Charging End Time display
                        
            print("Distance Left:", total_distance - dist_travelled, "km") # Printing distance left after this leg
            
            print("Updated Charge:",new_soc, "%") # Printing updated charge
            print("*************")

            yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ] # yielding start soc, leg distance, lat of cs, lon of cs, soc after leg, charging time and updated soc after charging

            #Check if there is any charging requirement between 2 am and 6 am. If there is, then night travel is set to True
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

            
            
            total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # add charging time above to total time
            initial_soc = new_soc # initial soc becomes updated soc after charge
            stop += 1 # stop being incremeted by 1
            trip_start = str(time_end) # trip start is set to time end of previous leg

    except:
        # If there is any kind of error, likely due to lack of charging stations (df_1 would be empty, so cannot be sliced later)
        # Then yield error message
        yield "Trip cannot be completed as no charging station is available in the vicinity"

def no_night(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, range_needed,
ave_speed, trip_start_at, trip_start, total_time):
    try:
        dist_left = total_distance - dist_travelled  #Find distance left

        possible_range = (100 - min_threshold)/100 * range_ev # Finding possible range that can be covered (Not used)
 
        while dist_left > 0: # Continuous loop till dist_left becomes zero
            if initial_soc < min_threshold:  # If the initial soc is lesser than min threshold, cannot travel, break loop
                print("Vehicle is unable to travel safely")
                break
            
            
            possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold)) # Calculate distance that can be covered with current soc or distance left whichever is lesser
            dist_travelled += possible_dist # Add possible distance to distance travelled
            dist_travelled = min(total_distance, dist_travelled) #maximum of distance can only be total distance, not more than that
            dist_left = total_distance - dist_travelled # Calculate distance left after increasing distance travelled

            if dist_left <= 0.0: 
                # Calculating the soc that would be reduced
                soc_reduction = possible_dist / (range_ev/100)
                print("No More Stops, Final Lap")  # If the last leg is safe to be travelled using current soc
                print("Starting SoC:", new_soc, "%") # print starting soc
                print(f"Distance Travelled in Total: {dist_travelled} km")  # printing distance travelled in total
                print("Travelling", possible_dist, "km now") # printing distance being travelled now
                        
                print("Current SoC:", new_soc - soc_reduction, "%") # print current soc after this leg

                yield [new_soc, possible_dist, new_soc - soc_reduction]#yield start soc, distance left and final soc

                dist_left = dist_left - dist_left # updating distance left to zero
                print("Trip Duration:",total_time/3600, "hrs") #print total duration
                sec = get_sec(trip_start) + total_time # Getting trip end time in seconds
                td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                print("Trip End:",td ) # Printing trip end time

                yield [sec, False , new_soc - soc_reduction] #yield total time, night travel as False and arrival soc
                print("Reached Destination:", dist_left, "km left") # Printing destination reached 
                break
        
            df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))] #Slicing dataframe of charging stations to specific distance of distance travelled

            while len(df_1) < 1: #If there are no charging stations in the specified distance above, then run this loop
                
                dist_travelled += 0.5 # increasse distance travelled by half a kilometre in each iteration
                dist_left -= 0.5
                df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]

            df_1.sort_values(by = ['Distance_to_CS']) # Sort dataframe smallest distance to charging station
            idx = df_1.index[0]  # Retrieving index
            a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]] # Getting information of charging station from dataframe
            new_soc = charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[0] # Get updated soc after charging at the station
    
            
            while df_1.iloc[0]['Distance_to_CS'] > 0.5: # If the charging station is more than 0.5 km, we find a new one
                dist_travelled = dist_travelled - 1
                possible_dist -= 1
                dist_left = dist_left + 1
                df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
                df_1.sort_values(by = ['Distance_to_CS'])
                idx = df_1.index[0]
                a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]]
                


            if dist_left <= possible_dist:
                #Terminaing condition happens here where distance left is lesser than or equal to possible distance that can be travelled
            
                 # Calculating the soc that would be reduced
                soc_reduction = dist_left / (range_ev/100)
                #Checking if safe for travel, if not recharge
                new_soc = initial_soc - (possible_dist/ (range_ev/100))
                if new_soc - soc_reduction < min_threshold:
                
                    # Check the distance needed for the final leg based on the arrival soc requested by the user
                    range_needed = range_ev/100 * (final_threshold - min_threshold)
                    # Calculate the new soc based on the range needed but max would be 100    
                    b = min(initial_soc - (possible_dist/ (range_ev/100)) + charging_time(dist_left+range_needed, min_threshold)[0],100)

                    print("Starting SoC: ", initial_soc, "%") # starting soc of leg
                    print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%") # current soc after travelling leg
                    print("Leg Start:", trip_start)#time of leg start
                    leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600))) # calculating time of leg end
            
                    print("Leg End:",str(leg_end)) # Displaying leg end time
                    print("Stop:", stop) # Stop number
                    print("Distance Travelled in Total:", dist_travelled, "km") # Total distance travelled so far
                    print("Distance Travelled before this Stop:", possible_dist, "km") # Distance travelled in this leg

                        
                    # Check if the time now is between 2am and 6am, since this is our charging stop. We need to charge till 100 percent due to the overnight halt.
                    if len(str(leg_end).split(".", 1)[0]) < 8:
                        # This case handles time with less than 8 digits which means there is no zero in front of a single digit hour
                        if "02:00:00" <= "0" + str(leg_end).split(".", 1)[0] <= "06:00:00":
                            print("Charge at:", a) # Printing station information
                            print("Charging Start Time:", str(leg_end).split(".", 1)[0]) # Print charging start time
                            print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # print charging duration in hrs
                            time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end
                            time_end = timedelta(seconds = time_end) # Convert seconds to time format
                            print("Charging End Time:", str(time_end)) # Print charging end time
                            print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                            total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                            print("Total Time:", total_time/3600) # Print total time
                            new_soc = 100 # New soc becomes 100
                            print("Updated Charge:",new_soc, "%") # Print new soc
                
                            b = new_soc # set b to new soc
                            print("*************")
                            # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                            yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],b]



                        else:
                            # If the charging requirement is not between 2am and 6am, we just charge till max of 85% if needed
                            print("Charge at:",a) # Printing station information
                            print("Charging Start Time:", str(leg_end).split(".", 1)[0]) # Print charging start time
                            print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")  # print charging duration in hrs
                            time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end
                            time_end = timedelta(seconds = time_end) # Convert seconds to time format
                            print("Charging End Time:", str(time_end)) # Print charging end time
                            print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                            total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                            
                            print("Updated Charge:",b, "%") # Print updated charge
                
                            b = new_soc # set b to new soc
                            print("*************")
                            # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                            yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b]
                            


            
                    elif len(str(leg_end).split(".", 1)[0]) == 8:
                        # This case handles time with exactly 8 digits 
                        if "02:00:00" <= str(leg_end).split(".", 1)[0] <= "06:00:00":


                            print("Charge at:", a) # Printing station information
                            print("Charging Start Time:", str(leg_end).split(".", 1)[0])  # Print charging start time
                            print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # print charging duration in hrs
                            time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end 
                            time_end = timedelta(seconds = time_end) # Convert seconds to time format
                            print("Charging End Time:", str(time_end)) # Print charging end time
                            print("Distance Left:", total_distance - dist_travelled, "km")  # Print distance left
                            total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                            print("Total Time:", total_time/3600) # Print total time
                            new_soc = 100# New soc becomes 100
                            print("Updated Charge:",new_soc, "%") # Print new soc
                    
                            b = new_soc # set b to new soc
                            print("*************")
                            # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                            yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],b]
                

                        else:

                            print("Charge at:",a) # Printing station information
                            print("Charging Start Time:", str(leg_end).split(".", 1)[0]) # Print charging start time
                            print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs")   # print charging duration in hrs
                            time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end
                            time_end = timedelta(seconds = time_end) # Convert seconds to time format
                            print("Charging End Time:", str(time_end)) # Print charging end time
                            print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                            total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                            
                            print("Updated Charge:",b, "%") # Print updated charge
                
                            print("*************")
                            # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                            yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b]
                    
                                    

                    print("Travelling", dist_left, "km now") # Print distance travelled in leg
                    soc_reduction = dist_left / (range_ev/100) # Calculating the soc that would be reduced
                    print("Leg Start:", str(time_end)) # Printing leg start time
                    leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600))) # Calculating leg end time
                
                    print("Leg End:",str(leg_end)) # Printing leg end time               
                    print("Current SoC:", b - soc_reduction, "%") # Printing soc after leg
                    yield [b, dist_left, b-soc_reduction] # yield starting soc, leg distance and soc after leg

                    dist_left = dist_left - dist_left # update dist left to zero
                    print("Trip Duration:",total_time/3600, "hrs")  #print total duration
                    sec = get_sec(trip_start_at) + total_time # Getting trip end time in seconds
                    td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                    print("Trip End:",td )  # Printing trip end time
                    print("Reached Destination:", dist_left, "km left") # Printing destination reached 
                        
                    yield [sec, False , b - soc_reduction]  # yielding final time, night travel flag as False and arrival soc
                    break # break from program

            

                else:
 
                    print("No More Stops, Final Lap")  # If the last leg is safe to be travelled using current soc
                    print("Starting SoC:", new_soc, "%") # print starting soc
                    print(f"Distance Travelled in Total: {dist_travelled} km")# printing distance travelled in total
                    print("Travelling", possible_dist, "km now")  # printing distance being travelled now
                        
                    print("Current SoC:", new_soc - soc_reduction, "%") # print current soc after this leg

                    yield [new_soc, possible_dist, new_soc - soc_reduction] #yield distance left and final soc

                    dist_left = dist_left - dist_left # updating distance left to zero
                    print("Trip Duration:",total_time/3600, "hrs") #print total duration
                    sec = get_sec(trip_start) + total_time # Getting trip end time in seconds
                    td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                    print("Trip End:",td ) # Printing trip end time

                    yield [sec, False , new_soc - soc_reduction]  # yielding final time, night travel flag as False and arrival soc
                    print("Reached Destination:", dist_left, "km left")  # Printing destination reached 
                    break  # break from program
            
            print("Starting SoC: ", initial_soc, "%") # print start soc
            print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%") # print soc after leg
            print("Leg Start:", trip_start) # print leg start time
            leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600))) # Calculate leg end time 

            print("Leg End:",str(leg_end)) # print leg end time
            print("Stop:", stop) # print stop number
            print("Distance Travelled in Total:", dist_travelled, "km") # print total distance travelled
            print("Distance Travelled before this Stop:", possible_dist, "km") # print leg distance
            

        
             # Check if the time now is between 2am and 6am, since this is our charging stop. We need to charge till 100 percent due to the overnight halt.
            if len(str(leg_end).split(".", 1)[0]) < 8: 
                 # This case handles time with less than 8 digits which means there is no zero in front of a single digit hour
                if "02:00:00" <= "0" + str(leg_end).split(".", 1)[0] <= "06:00:00":
            
                    print("Charge at:", a) # Printing station information
                    print("Charging Start Time:", str(leg_end).split(".", 1)[0]) # Print charging start time
                    print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # print charging duration in hrs
                    time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end
                    time_end = timedelta(seconds = time_end) # Convert seconds to time format
                    print("Charging End Time:", str(time_end)) # Print charging end time
                    print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                    total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                    print("Total Time:", total_time/3600) # Print total time
                    new_soc = 100 # New soc becomes 100
                    print("Updated Charge:",new_soc, "%") # Print new soc

                    print("*************")
                    # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                    yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],new_soc ]

                    

                    

                else:
                    # If the charging requirement is not between 2am and 6am, we just charge till max of 85% if needed
                    print("Charge at:", a) # Printing station information
                    print("Charging Start Time:", str(leg_end).split(".", 1)[0]) # Print charging start time
                    print("Charging Time:", charging_time(dist_left,initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # print charging duration in hrs
                    time_end = get_sec(str(leg_end)) + charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end
                    time_end = timedelta(seconds = time_end) # Convert seconds to time format
                    print("Charging End Time:", str(time_end)) # Print charging end time
                    print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                    total_time += charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                    print("Total Time:", total_time/3600) # print total time
                    print("Updated Charge:",new_soc, "%") # print updated soc

                    print("*************")
                    # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                    yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ]
        

            
            elif len(str(leg_end)).split(".", 1)[0] == 8:
                # This case handles time with exactly 8 digits 
                if "02:00:00" <= str(leg_end).split(".", 1)[0] <= "06:00:00":

                    
                    print("Charge at:", a)  # Printing station information
                    print("Charging Start Time:", str(leg_end).split(".", 1)[0])  # Print charging start time
                    print("Charging Time:", charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # print charging duration in hrs
                    time_end = get_sec(str(leg_end)) + charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end 
                    time_end = timedelta(seconds = time_end) # Convert seconds to time format
                    print("Charging End Time:", str(time_end))  # Print charging end time
                    print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                    total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                    print("Total Time:", total_time/3600) # Print total time
                    new_soc = 100 # new soc becomes 100
                    print("Updated Charge:",new_soc, "%") #print new soc
                    print("*************")
                    # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                    yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1],new_soc ]


                else:

                    print("Charge at:", a) # Printing station information
                    print("Charging Start Time:", str(leg_end).split(".", 1)[0]) # Print charging start time
                    print("Charging Time:", charging_time(dist_left,initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # print charging duration in hrs
                    time_end = get_sec(str(leg_end)) + charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # calculate charging time end
                    time_end = timedelta(seconds = time_end) # Convert seconds to time format
                    print("Charging End Time:", str(time_end)) # Print charging end time
                    print("Distance Left:", total_distance - dist_travelled, "km") # Print distance left
                    total_time += charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Adding charging duration to total time
                    print("Total Time:", total_time/3600)  #print total time
                    print("Updated Charge:",new_soc, "%") # print updated soc

                    print("*************")
                    # yield initial soc, distance travelled in leg, cs lat, cs lon, soc after leg, charging duration, updated soc
                    yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ]



            total_time += charging_full(initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # add charging time to total time
            initial_soc = new_soc # Set initial soc to new soc
            stop += 1 # increment stop by 1

            trip_start = str(time_end) # set trip start to leg time end
    except:
        # If there is any kind of error, likely due to lack of charging stations (df_1 would be empty, so cannot be sliced later)
        # Then yield error message
        return("Trip cannot be completed as no charging station is available in the vicinity")
    

def own_rest(df, initial_soc, min_threshold, total_distance, dist_travelled, range_ev, stop, final_threshold, range_needed,
    ave_speed, trip_start_at, trip_start, total_time, rest_lat, rest_lon,distance_travelled_by_rest_place, df_complete): 
    """This function is called if the user has a specific place to rest and we incorporate into the routing"""
    try:
        dist_left = total_distance - dist_travelled  #Find distance left
        possible_range = (100 - min_threshold)/100 * range_ev  # Finding possible range that can be covered (Not used)
        rest_lat = float(rest_lat) # converting string rest lat to float
        rest_lng = float(rest_lon) # converting string rest long to float

        # We travel using the default method charge and go till the rest place. We have to travel no matter how late it is in the night since the user wants to rest there
        chargefunction = charge_and_go(df, initial_soc, min_threshold, distance_travelled_by_rest_place, dist_travelled, range_ev, stop, 15, range_needed, 
        ave_speed, trip_start_at, trip_start, total_time)

        # storing values from yield calls in charge and go
        lst = {}
        step = 1
        for value in chargefunction: 
                lst[step] = value
                step += 1

        # Data processing of details from charge and go
        keys = list(lst.keys())

        current_soc = lst[keys[-1]][-1]
        trip_end_sec = lst[keys[-1]][0]
        trip_end = timedelta(seconds=trip_end_sec)

        yield [lst]


        dist_left = total_distance - distance_travelled_by_rest_place #Find distance left after rest place
        dist_travelled = distance_travelled_by_rest_place # Set distance travelled till now to distance to rest place CS
    

        df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(distance_travelled_by_rest_place) ) & (df['distance_travelled_till_here'] <= math.ceil(distance_travelled_by_rest_place+0.5))]#Slicing dataframe of charging stations to specific distance of distance travelled
        
        while len(df_1) < 1: #If there are no charging stations in the specified distance above, then run this loop
            dist_travelled -= 0.5 # decrease distance travelled by half a kilometre in each iteration
            dist_left += 0.5
            df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]

        df_1.sort_values(by = ['Distance_to_CS']) # Sort dataframe smallest distance to charging station
        idx = df_1.index[0] # Retrieving index
        a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]] # Getting information of charging station from dataframe
            

        print("Charge at:", a) # Location of charging stations
        print("Charging Start Time:", str(trip_end).split(".", 1)[0]) # Charging start time
        print("Charging Time:", charging_full(current_soc)[1], "hrs") # Charging duration in hours
        time_end = get_sec(str(trip_end)) + charging_full(current_soc)[1] * 3600 # Calculating time end of charging 
        time_end = timedelta(seconds = time_end) # converting seconds to proper time
        print("Charging End Time:", str(time_end)) # Charging End Time display
        print("Distance Left:", dist_left, "km") # Showing distance left
        total_time += charging_full(current_soc)[1] * 3600 # Add charging duration to total time
        print("Total Time:", total_time/3600) # Display total time
        initial_soc = 100 # set initial soc to 100 due to overnight charge
        print("Updated Charge:",initial_soc, "%") #Display updated charge
        print("*************")

        #yield start soc, rest lat, rest lon, and charging duration to reach 100%
        yield [current_soc, rest_lat, rest_lng, charging_full(current_soc)[1], initial_soc]

        trip_start = str(time_end) # set trip start to leg time end



        # After charging if the distance the left is zero, continue the usual way
        while dist_left > 0: # Continuous loop till dist_left becomes zero
            if initial_soc < min_threshold: # If the initial soc is lesser than min threshold, cannot travel, break loop
                print("Vehicle is unable to travel safely")
                break

            possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold)) # Calculate distance that can be covered with current soc or distance left whichever is lesser

            if dist_left <= possible_dist: #Terminaing condition happens here where distance left is lesser than or equal to possible distance that can be travelled
                 # Calculating the soc that would be reduced
                soc_reduction = dist_left / (range_ev/100)
                #Checking if safe for travel, if not recharge
                new_soc = initial_soc - (possible_dist/ (range_ev/100)) 

                if new_soc - soc_reduction < min_threshold: #if the new soc after travel of this leg would be lesser than min threshold, we need to charge
                    place = True # setting place to True to which means that we need to charge one last time in the final leg
                    possible_dist = min(dist_left, range_ev/100 * (initial_soc-min_threshold))
                    dist_travelled += possible_dist # Add possible distance to distance travelled
                    dist_travelled = min(total_distance, dist_travelled) # dist travelled can only be maximum of total distance cannot be more than that
                    dist_left = total_distance - dist_travelled # Calculate distance left after increasing distance travelled
                    df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))]
                
                    while len(df_1) < 1: #If there are no charging stations in the specified distance above, then run this loop
                        dist_travelled -= 0.5  # decrease distance travelled by half a kilometre in each iteration
                        dist_left += 0.5
                        possible_dist -= 0.5
                        df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))] #Slice dataframe to check if a station exists

                        if possible_dist < 10: # if there is no station after moving forward for 10km, we declare that place is False and we cannot continue the trip
                            place = False
                            print("Vehicle is unable to complete trip. No more charging points available.")
                            break

                    if place == True: # If we have a non zero dataframe
                        df_1.sort_values(by = ['Distance_to_CS']) # Sort dataframe smallest distance to charging station
                        idx = df_1.index[0] # Retrieving index of the smallest dist CS
                        a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]] # Getting information of charging station from dataframe
                        # Calculate the distance needed for the final leg based on the arrival soc requested by the user
                        range_needed = range_ev/100 * (final_threshold - min_threshold)
                        # Calculate the new soc based on the range needed but max would be 100
                        b = min(initial_soc - (possible_dist/ (range_ev/100)) + charging_time(dist_left+range_needed, min_threshold)[0],100)

                        print("Starting SoC: ", initial_soc, "%") # starting soc of leg
                        print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%") # current soc after travelling leg
                        print("Leg Start:", trip_start) #time of leg start
                        leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))  # calculating time of leg end
            
                        print("Leg End:",str(leg_end))  # Displaying leg end time
                        print("Stop:", stop) # Stop number
                        print("Distance Travelled in Total:", dist_travelled, "km") # Total distance travelled so far
                        print("Distance Travelled before this Stop:", possible_dist, "km") # Distance travelled in this leg
                        print("Charge at:",a) # Location of charging stations
                        print("Charging Start Time:", str(leg_end)) # Charging start time
                        print("Charging Time:", charging_time(dist_left+range_needed, min_threshold)[1], "hrs") # Charging duration in hours
            
                        time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600  #Getting charging end time
                        time_end = timedelta(seconds = time_end)  # converting seconds to proper time
                        print("Charging End Time:", str(time_end).split(".", 1)[0])  #Charging End Time display
                        print("Distance Left:", total_distance - dist_travelled, "km") # Showing distance left
                        total_time += charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 # Add charging duration to total time
                            
                        print("Updated Charge:",b, "%") #Display updated charge
                        print("*************")
                        # yield start soc, distance in leg, lat cs, lng cs, soc after leg, charging duration, updated soc
                        yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],b]
                
                        
                        
                        print("Travelling", dist_left, "km now")# Printing distance being travelled in the last leg
                        print("Leg Start:", str(time_end))# Printing start of leg
                        leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600))) # Calculate leg end time
                        total_time += (dist_left/ave_speed) * 3600 # Add last leg duration to total time
                        print("Leg End:",str(leg_end)) # Print end of leg
                        soc_reduction = dist_left / (range_ev/100)   # Calculating the soc that would be reduced        
                        print("Current SoC:", new_soc - soc_reduction, "%") # print soc after reduction
                        yield [b, dist_left, b-soc_reduction] #yield start soc, distance in leg, arrival soc
                        dist_left = dist_left - dist_left # Setting distance left to zero
                        print("Trip Duration:",total_time/3600, "hrs") # Printing total duration
                        sec = get_sec(trip_start_at) + total_time # Getting trip end time in seconds
                        td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                        print("Trip End:",td ) # Printing trip end time
                        print("Reached Destination:", dist_left, "km left")  # Printing destination reached 
                        yield [sec, False , b - soc_reduction] # yielding final time, night travel flag and arrival soc
                        break # force break from program

                    else:
                        dist_travelled -= possible_dist # if a place does not exist for charging station, keep the original place for charging 
                        dist_left = total_distance - dist_travelled # Calculate distance left after increasing distance travelled
                        soc_reduction = dist_left / (range_ev/100) # Calculating the soc that would be reduced
                        new_soc = 100 # set new soc to 100
                        print("Starting SoC:", new_soc, "%") # starting soc of leg
                        print("Travelling", dist_left, "km now") # distance in leg
                        print("Leg Start:", str(time_end)) #time of leg start
                        leg_end = timedelta(seconds= (get_sec(str(time_end)) + (dist_left/ave_speed * 3600)))  # calculating time of leg end
                        total_time += (dist_left/ave_speed) * 3600 #adding leg trip duration to total time
                        print("Leg End:",str(leg_end))   # Displaying leg end time    
                        soc_reduction = dist_left / (range_ev/100)  # Calculating the soc that would be reduced   
                        print("Current SoC:", new_soc - soc_reduction, "%") # current soc after travelling leg

                        yield [new_soc, dist_left, new_soc-soc_reduction] # Yielding current soc, distance left and arrival soc

                        dist_left = dist_left - dist_left # Setting distance left to zero
                        print("Trip Duration:",total_time/3600, "hrs") # Printing total duration
                        sec = get_sec(trip_start_at) + total_time # Getting trip end time in seconds
                        td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                        print("Trip End:",td ) # Printing trip end time
                        print("Reached Destination:", dist_left, "km left")  # Printing destination reached
                        yield [sec, False , new_soc - soc_reduction] # yielding final time, night travel flag to False and arrival soc
                        break




                else:  
                    new_soc = 100 # set new soc to 100
                    print("No More Stops, Final Lap")  # If the last leg is safe to be travelled using current soc
                    print("Starting SoC:", new_soc, "%") # print starting soc
                    print(f"Distance Travelled in Total: {dist_travelled} km") # printing distance travelled in total
                    print("Travelling", possible_dist, "km now") # printing distance being travelled now
                        
                    print("Current SoC:", new_soc - soc_reduction, "%") # print current soc after this leg

                    yield [new_soc, possible_dist, new_soc - soc_reduction]  #yield distance left and final soc

                    dist_left = dist_left - dist_left  # updating distance left to zero
                    print("Trip Duration:",total_time/3600, "hrs")  #print total duration
                    sec = get_sec(trip_start) + total_time # Getting trip end time in seconds
                    td = timedelta(seconds=sec) # Converting trip end seconds to proper time
                    print("Trip End:",td ) # Printing trip end time

                    yield [sec, False , new_soc - soc_reduction]  #yield distance left and final soc
                    print("Reached Destination:", dist_left, "km left") # Printing destination reached 
                    break
            

            else:
                dist_travelled += possible_dist #adding possible dist 
                dist_left = total_distance - dist_travelled #Find distance left

                print("Starting SoC: ", initial_soc, "%")  # starting soc of leg
                print("Current SoC:", initial_soc - (possible_dist/ (range_ev/100)), "%") # current soc after travelling leg
                print("Leg Start:", trip_start) #time of leg start
                leg_end = timedelta(seconds= (get_sec(trip_start) + (possible_dist/ave_speed * 3600)))  # calculating time of leg end
                total_time += (possible_dist/ave_speed) * 3600 #adding leg trip duration to total time
                leg_end = str(leg_end).split(".", 1)[0] #formatting leg end time
                print("Leg End:",str(leg_end).rstrip(".")) # Displaying leg end time
                print("Stop:", stop) # Stop number
                print("Distance Travelled in Total:", dist_travelled, "km")  # Total distance travelled so far
                print("Distance Travelled before this Stop:", possible_dist, "km")  # Distance travelled in this leg
                

                
                df_1 = df.loc[(df['distance_travelled_till_here'] >=math.floor(dist_travelled) ) & (df['distance_travelled_till_here'] <= math.ceil(dist_travelled+0.5))] #Slicing dataframe of charging stations to specific distance of distance travelled
                df_1.sort_values(by = ['Distance_to_CS']) # Sort dataframe smallest distance to charging station
                try:
                    idx = df_1.index[0] # Retrieving index
                except IndexError: # If there is no cs available in the df, then print error and show max possible distance that can be travelled
                    print("Possible Distance:", dist_travelled)
                    print("Total Distance:", total_distance)
                    print("Trip cannot be completed as no charging station is available in the vicinity")
                    yield "Trip cannot be completed as no charging station is available in the vicinity"
                    return("Trip cannot be completed as no charging station is available in the vicinity")
                    
                a = [idx,df_1.iloc[0]["Name_Charging_Station"],df_1.iloc[0]["Lat_CS"],df_1.iloc[0]["Lng_CS"],df_1.iloc[0]["Distance_to_CS"]] # Getting information of charging station from dataframe
                
                print("Charge at:", a) # Location of charging station
                print("Charging Start Time:", str(leg_end)) # Charging start time
                print("Charging Time:", charging_time(dist_left, initial_soc - (possible_dist/ (range_ev/100)))[1], "hrs") # Charging duration in hours
                time_end = get_sec(str(leg_end)) + charging_time(dist_left+range_needed, initial_soc - (possible_dist/ (range_ev/100)))[1] * 3600 #Getting charging end time
                time_end = timedelta(seconds = time_end) # converting seconds to proper time
                print("Charging End Time:", str(time_end).split(".", 1)[0]) #Charging End Time display
                            
                print("Distance Left:", total_distance - dist_travelled, "km")   #Showing distance left
                
                print("Updated Charge:",new_soc, "%") #Display updated charge
                print("*************")

                yield [initial_soc, possible_dist, a[2], a[3], initial_soc - (possible_dist/ (range_ev/100)),charging_time(dist_left+range_needed, min_threshold)[1],new_soc ] #yield results to be used in display of HTML info

                initial_soc = new_soc # initial soc becomes updated soc after charge
                stop += 1 # stop being incremeted by 1
                trip_start = str(time_end) # trip start is set to time end of previous leg
    except:
        # If there is any kind of error, likely due to lack of charging stations (df_1 would be empty, so cannot be sliced later)
        # Then yield error message
        return("Trip cannot be completed as no charging station is available in the vicinity")
    


def station_coordinates(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time):
    """Retrieves information from each yield as the above is a generator function. Hence, this would join everything in a dictionary for access later"""
    possible_range = (initial_soc - min_threshold)/100 * range_ev # Calculate total possible distance with current soc
    lst = {} # empty dict
    if possible_range >= total_distance: # Check if total possible range with current soc is more than total distance required for trip
        lst = "Route from Origin to Destination with No Charging" # set lst to string if no charging is required
    else: # iterate through charge and go function and store data in dict
        stop = 1
        for value in charge_and_go(df, initial_soc, min_threshold, total_distance, 
        dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time):
            if type(value) == str: # If error from generator function, then return string
                return "Trip cannot be completed as no charging station is available in the vicinity" 
            else:
                lst[stop] = value
                stop += 1

    return lst

    
def station_coordinates_no_night(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time):
    """Retrieves information from each yield as the above is a generator function. Hence, this would join everything in a dictionary for access later"""
    possible_range = (initial_soc - min_threshold)/100 * range_ev  # Calculate total possible distance with current soc
    lst = {} # empty dict
    if possible_range >= total_distance:  # Check if total possible range with current soc is more than total distance required for trip
        lst = "Route from Origin to Destination with No Charging" # set lst to string if no charging is required 
    else: # iterate through charge and go function and store data in dict
        stop = 1
        for value in no_night(df, initial_soc, min_threshold, total_distance, 
        dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time): 
            if type(value) == str: # If error from generator function, then return string
                return "Trip cannot be completed as no charging station is available in the vicinity" 
            else:
                lst[stop] = value
                stop += 1

    return lst



def station_coordinates_own_rest(df, initial_soc, min_threshold, total_distance, 
    dist_travelled, range_ev, stop, final_threshold, range_needed, ave_speed, trip_start_at, trip_start, total_time,
    rest_lat, rest_lon,distance_travelled_by_rest_place, df_complete):
    """Retrieves information from each yield as the above is a generator function. Hence, this would join everything in a dictionary for access later"""
    possible_range = (initial_soc - min_threshold)/100 * range_ev # Calculate total possible distance with current soc
    lst = {} # empty dict
    if possible_range >= total_distance: # Check if total possible range with current soc is more than total distance required for trip
        lst = "Route from Origin to Destination with No Charging"  # set lst to string if no charging is required 
    else:
        stop = 1
        for value in own_rest(df, initial_soc, min_threshold, total_distance, 
        dist_travelled, range_ev, stop, final_threshold, range_needed,
    ave_speed, trip_start_at, trip_start, total_time, rest_lat, rest_lon,distance_travelled_by_rest_place,df_complete): 

            if type(value) == str: # If error from generator function, then return string
                return "Trip cannot be completed as no charging station is available in the vicinity" 
            else:
                lst[stop] = value
                stop += 1

    return lst



