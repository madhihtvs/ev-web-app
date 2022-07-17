import pandas as pd
from scipy.spatial import distance_matrix, KDTree
import numpy as np
from scipy.stats import zscore
from operator import itemgetter
from geopy.distance import geodesic
from sklearn.neighbors import BallTree


def clustering_algo(path, stations):
    # if "lat" or "lng" in stations.columns:
    #     stations.rename(columns = {'lat':'Latitude', 'lng':'Longitude'}, inplace = True)
    
    # if "Location" in stations.columns:
    #     stations.rename(columns = {'Location':'Station Name'}, inplace = True)

    
    # stations["Station Name"] = stations["Station Name"].str.replace(',','')
    stations.drop(columns=['Sl No']) # Drop column mentioning station number as index is enough
    # stations_pos = stations[['Latitude', 'Longitude']].to_numpy()
    # path = path[["lat","lng"]]
    # path = path.iloc[::15, :]
    # path = path.to_numpy()

    # zs = np.abs(zscore(stations_pos, 0))
    # filtered_entries = (zs < 3).all(axis=1)
    # stations_pos = stations_pos[filtered_entries]

    # disntace_matrix = distance_matrix(path, stations_pos)

    # # for each point in the path, we take the 5 closest recharging stations (without counting the duplciates)
    # closest = np.argsort(disntace_matrix, -1)[:, :5]
    # closest = np.unique(closest.ravel())
    # closest_points = stations_pos[closest]

    # closest_df = pd.DataFrame(closest_points, columns=['Latitude', 'Longitude']) 

    # closest_df = pd.merge(stations, closest_df, how='inner')
    

    # path_df = pd.DataFrame(path, columns=['Latitude', 'Longitude']) 

    # closest_df["route"] = 0

    # path_df["route"] = 1
    # route_df = path_df.append([closest_df], ignore_index = True)


    # route_df['route'] = route_df['route'].astype(str)
    # df22 = route_df[route_df['route'] == '0']
    # dff = route_df[route_df['route'] == '1']

    # df22["lat_lon"] = list(zip(df22.Latitude, df22.Longitude))

    closest_df = stations
    closest_df["route"] = 0 # stations labelled as 0
    




    mega = [] # Creating empty list known as mega
    # path_df = path_df[["Latitude", "Longitude"]]
    # closest_df2 = closest_df[["Latitude", "Longitude"]]
    # path2 = path_df.to_numpy()
    # closest2 = closest_df2.to_numpy()
    path2 = path[["lat","lng"]] # Selecting only lat and lng columns from path dataframe
    path2 = path2.iloc[::15, :] # Slicing dataframe for every 15th row to reduce density
    path2 = path2.to_numpy() #Converting dataframe to 2D numpy array

    
    path_df = pd.DataFrame(path2, columns=['Latitude', 'Longitude']) #Creating path df from path2 array
    path_df["route"] = 1 #Path coordinates labelled as 1
    route_df = path_df.append([closest_df], ignore_index = True) # Combining path and closest df to route df


    route_df['route'] = route_df['route'].astype(str) # Converting route column to string
    #df22 = route_df[route_df['route'] == '0']
    dff = route_df[route_df['route'] == '1'] # Taking out only path coordinates


    closest2 = stations[['Latitude', 'Longitude']].to_numpy() # Converting stations coordinates to 2D numpy array


    disntace_matrix2 = distance_matrix(path2, closest2) # Finding distance between each charging station and path coordinate using distance matrix from scipy


    for i in range(len(disntace_matrix2)): #For each row of distance matrix
        a = list(disntace_matrix2[i]) # Access each row
        minimum = min(a) # Find the min distance for each path coordinate
        idx = a.index(minimum) # Get the index of the charging station that is the closest
        closest = stations.loc[idx] # Locate the index from the charging stations dataframe
        #closest = closest_df.loc[idx]
        mega.append([closest["Station Name"],closest["Latitude"], closest["Longitude"], minimum]) # append results to mega list


    dist = [0.000000] # Create dist list with starting distance to be zero 
    i = 0 # set counter to be zero
    while i <= len(dff) - 2: # While i is less than the second last element
        b = geodesic((dff.iloc[i+1]["Latitude"],dff.iloc[i+1]["Longitude"]), (dff.iloc[i]["Latitude"],dff.iloc[i]["Longitude"])).km # Find distance between each consecutive coordinate
        dist.append(b) # Append distance to dist list
        i += 1 # increase counter by 1

    dff['dist'] = dist # attach distance list to path dataframe


    dff["Nearest_Charging_Station"] = mega #attach mega list to path dataframe

    names = dff['Nearest_Charging_Station'].to_numpy() #convert nearest cs column to numpy
    Name_Charging_Station = [] # Create empty list for name of CS
    Lat_CS = [] # Create empty list for lat CS
    Lng_CS = [] # Create empty list for lng CS
    Distance_to_CS = [] # Create empty list for distance to CS

    for i in names: # For each element in names, append each of the sub elements to the correct list
        Name_Charging_Station.append(i[0])
        Lat_CS.append(i[1])
        Lng_CS.append(i[2])
        Distance_to_CS.append(i[3])

    data_tuples = list(zip(Name_Charging_Station,Lat_CS,Lng_CS,Distance_to_CS)) # Create data tuple from the different lists above
    dff_2 = pd.DataFrame(data_tuples, columns=['Name_Charging_Station','Lat_CS','Lng_CS','Distance_to_CS']) # Create dataframe from the data tuple
    dff = pd.merge(dff, dff_2, left_index=True, right_index=True) # merge dff and dff2 


    total = [] # Create empty list named total to store total distances

    for i in range(len(dff)): # Get each distance out from dataframe
        total.append(dff.iloc[int(i)]['dist'])

    # Calculate consecutive distances and add up so that you know what is the distance travelled till the specific path coordinate from origin
    a = 0
    new = []
    for i in total:
        a += i
        new.append(a)
    
    dff["distance_travelled_till_here"] = new # attach to dataframe




    return dff




def nearest_charging_stations(pt, stations):
        """Finding the nearest charging stations given a point and list of stations. This method uses BallTree clustering which is not in use"""
        if "lat" or "lng" in stations.columns:
                stations.rename(columns = {'lat':'Latitude', 'lng':'Longitude'}, inplace = True)
        
        if "Location" in stations.columns:
                stations.rename(columns = {'Location':'Station Name'}, inplace = True)

        stations["Station Name"] = stations["Station Name"].str.replace(',','')
        stations.drop(columns=['Sl No'])
        stations_pos = stations[['Latitude', 'Longitude']].to_numpy()
        tree = BallTree(stations_pos, metric = "euclidean")
        ind = tree.query_radius(pt, r=0.01)
        df_nearest = pd.DataFrame()  
        for i in ind[0]:
                a = stations.loc[stations.index == i]
                df_nearest = pd.concat([df_nearest,a])
        df_nearest = df_nearest.drop(columns=['Sl No'])
        df_nearest = df_nearest.reset_index(drop=True)
        df_nearest["Label"] = "Nearest Point"
        lst = ["Query Point", pt[0][1], pt[0][0], "Query Point"]
        df_nearest.loc[len(df_nearest)] = lst
        return df_nearest


def near_points(pt, stations):
        """Finding the nearest charging stations given a point and list of stations. This method uses distance matrix, brute force distance calculation to get the nearest stations. It is not in use now."""
        stations2 = stations

        if "lat" or "lng" in stations2.columns:
                stations2.rename(columns = {'lat':'Latitude', 'lng':'Longitude'}, inplace = True)
        
        if "Location" in stations2.columns:
                stations2.rename(columns = {'Location':'Station Name'}, inplace = True)

        stations2["Station Name"] = stations2["Station Name"].str.replace(',','')
        stations_pos2 = stations2[['Latitude', 'Longitude']].to_numpy()

        path = pt

        zs = np.abs(zscore(stations_pos2, 0))
        filtered_entries = (zs < 3).all(axis=1)
        stations_pos = stations_pos2[filtered_entries]

        disntace_matrix = distance_matrix(path, stations_pos)

        closest = np.argsort(disntace_matrix, -1)[:, :5]
        closest = np.unique(closest.ravel())
        closest_points = stations_pos[closest]

        closest_df = pd.DataFrame(closest_points, columns=['Latitude', 'Longitude']) 

        closest_df = pd.merge(stations, closest_df, how='inner')
        closest_df["Label"] = "Closest"
        closest_df = closest_df.iloc[:,1:]

        return closest_df


    
def dimension_reduction(path, origin_lat, origin_lon, dest_lat, dest_lon, stations):
    """This function queries the nearest charging station points to a given path."""
    stations2 = stations

    if "lat" or "lng" in stations2.columns:
        stations2.rename(columns = {'lat':'Latitude', 'lng':'Longitude'}, inplace = True)
    
    if "Location" in stations.columns:
        stations2.rename(columns = {'Location':'Station Name'}, inplace = True)

    
    stations2["Station Name"] = stations2["Station Name"].str.replace(',','') # removing any comma that may be in address
    stations2.drop(columns=['Sl No']) # dropping number column

    orgdest = [[origin_lat, origin_lon],[dest_lat,dest_lon]]
    route_df = path.iloc[::15, :] # slicing dataframe to reduce density
    route_array = route_df.to_numpy() # converting df to numpy array
    stations2 = stations2[['Latitude', 'Longitude']].to_numpy() # converting stations to numpy array
    kdB = KDTree(stations2) # Creating KDTree from stations numpy array
    ind = kdB.query(route_array, k=5)[-1] # Perform clustering of 5 nearest neighbours

    lst = [] # Create empty list to store station coordinates

    for i in range(len(ind)): # Finding the station coordinates based on the indexes from KDTree
        for j in ind[i]:
            lst.append(stations2[j])
    
    closest_df = pd.DataFrame(lst, columns=['Latitude', 'Longitude']) # Creating dataframe from lst
    closest_df = pd.merge(stations, closest_df, how='inner') # merge with stations dataframe to get other information like name and address

    return closest_df


    
