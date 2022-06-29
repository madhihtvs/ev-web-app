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
    # stations.drop(columns=['Sl No'])
    stations_pos = stations[['Latitude', 'Longitude']].to_numpy()
    path = path[["lat","lng"]]
    path = path.iloc[::15, :]
    path = path.to_numpy()

    zs = np.abs(zscore(stations_pos, 0))
    filtered_entries = (zs < 3).all(axis=1)
    stations_pos = stations_pos[filtered_entries]

    disntace_matrix = distance_matrix(path, stations_pos)

    # for each point in the path, we take the 5 closest recharging stations (without counting the duplciates)
    closest = np.argsort(disntace_matrix, -1)[:, :5]
    closest = np.unique(closest.ravel())
    closest_points = stations_pos[closest]

    closest_df = pd.DataFrame(closest_points, columns=['Latitude', 'Longitude']) 

    closest_df = pd.merge(stations, closest_df, how='inner')
    

    path_df = pd.DataFrame(path, columns=['Latitude', 'Longitude']) 

    closest_df["route"] = 0

    path_df["route"] = 1
    route_df = path_df.append([closest_df], ignore_index = True)


    route_df['route'] = route_df['route'].astype(str)
    df22 = route_df[route_df['route'] == '0']
    dff = route_df[route_df['route'] == '1']

    df22["lat_lon"] = list(zip(df22.Latitude, df22.Longitude))

    mega = []
    path_df = path_df[["Latitude", "Longitude"]]
    closest_df2 = closest_df[["Latitude", "Longitude"]]
    path2 = path_df.to_numpy()
    closest2 = closest_df2.to_numpy()
    disntace_matrix2 = distance_matrix(path2, closest2)


    for i in range(len(disntace_matrix2)):
        a = list(disntace_matrix2[i])
        minimum = min(a)
        idx = a.index(minimum)
        closest = closest_df.loc[idx]
        mega.append([closest["Station Name"],closest["Latitude"], closest["Longitude"], minimum])


    dist = [0.000000]
    i = 0
    while i <= len(dff) - 2:
        b = geodesic((dff.iloc[i+1]["Latitude"],dff.iloc[i+1]["Longitude"]), (dff.iloc[i]["Latitude"],dff.iloc[i]["Longitude"])).km
        dist.append(b)
        i += 1

    dff['dist'] = dist


    dff["Nearest_Charging_Station"] = mega

    names = dff['Nearest_Charging_Station'].to_numpy()
    Name_Charging_Station = []
    Lat_CS = []
    Lng_CS = []
    Distance_to_CS = []

    for i in names:
        Name_Charging_Station.append(i[0])
        Lat_CS.append(i[1])
        Lng_CS.append(i[2])
        Distance_to_CS.append(i[3])

    data_tuples = list(zip(Name_Charging_Station,Lat_CS,Lng_CS,Distance_to_CS))
    dff_2 = pd.DataFrame(data_tuples, columns=['Name_Charging_Station','Lat_CS','Lng_CS','Distance_to_CS'])
    dff = pd.merge(dff, dff_2, left_index=True, right_index=True)


    total = []

    for i in range(len(dff)):
        total.append(dff.iloc[int(i)]['dist'])


    a = 0
    new = []
    for i in total:
        a += i
        new.append(a)
    
    dff["distance_travelled_till_here"] = new




    return dff




def nearest_charging_stations(pt, stations):
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

    stations2 = stations

    if "lat" or "lng" in stations2.columns:
        stations2.rename(columns = {'lat':'Latitude', 'lng':'Longitude'}, inplace = True)
    
    if "Location" in stations.columns:
        stations2.rename(columns = {'Location':'Station Name'}, inplace = True)

    
    stations2["Station Name"] = stations2["Station Name"].str.replace(',','')
    stations2.drop(columns=['Sl No'])

    orgdest = [[origin_lat, origin_lon],[dest_lat,dest_lon]]
    route_df = path.iloc[::15, :]
    route_array = route_df.to_numpy()
    stations2 = stations2[['Latitude', 'Longitude']].to_numpy()
    kdB = KDTree(stations2)
    ind = kdB.query(route_array, k=20)[-1]

    lst = []

    for i in range(len(ind)):
        for j in ind[i]:
            lst.append(stations2[j])
    
    closest_df = pd.DataFrame(lst, columns=['Latitude', 'Longitude']) 
    closest_df = pd.merge(stations, closest_df, how='inner')

    return closest_df


    
