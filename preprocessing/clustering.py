from turtle import pos
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
import numpy as np
from scipy.stats import zscore
import plotly.express as px
from operator import itemgetter
from geopy.distance import geodesic
from datetime import datetime
import math
from datetime import timedelta




def clustering_algo(path, stations):
    if "lat" or "lng" in stations.columns:
        stations.rename(columns = {'lat':'Latitude', 'lng':'Longitude'}, inplace = True)
        
    
    if "Location" in stations.columns:
        stations.rename(columns = {'Location':'Station Name'}, inplace = True)


    
    stations["Station Name"] = stations["Station Name"].str.replace(',','')
    stations.drop(columns=['Sl No'])
    stations_pos = stations[['Latitude', 'Longitude']].to_numpy()
    path = path[["lat","lng"]]
    path = path.to_numpy()

    zs = np.abs(zscore(stations_pos, 0))
    filtered_entries = (zs < 3).all(axis=1)
    stations_pos = stations_pos[filtered_entries]

    disntace_matrix = distance_matrix(path, stations_pos)

    # for each point in the path, we take the 5 closest recharging stations (wihtout counting the duplciates)
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

    fig = px.scatter_mapbox(route_df,lat="Latitude",lon="Longitude",mapbox_style="carto-positron", zoom = 10, color = "route")

    

    mega = []
    for index, row in dff.iterrows():
        lst = []
        for idx,row2 in df22.iterrows():
            station = row2['Station Name']
            lat1 = row['Latitude']
            lng1 = row['Longitude']
            
            lat2 = row2['Latitude']
            lng2 = row2['Longitude']
            dist = geodesic((lat1,lng1), (lat2,lng2)).km
            lst.append([station,lat2,lng2,dist])
        val = sorted(lst, key= itemgetter(3))[0]
        mega.append(val)
    
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




    return fig, dff

