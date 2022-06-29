from typing import Dict, List, Tuple
from unicodedata import category

import pandas as pd
import copy
from geopy.distance import geodesic

import preprocessing.backend as backend
import preprocessing.battery as battery
import preprocessing.clustering as clustering

def collect_user_inputs(request_values):
    start_point = request_values.get("start-point")
    end_point = request_values.get("end-point")
    range_start = request_values.get("range-start")
    range_arrival = request_values.get("range-arrival")
    start_time = request_values.get("start-time")
    start_time = f"{start_time}:00"
    return start_point, end_point, range_start, range_arrival, start_time

def search_input(request_values):
    search_point = request_values.get("search-point")
    return search_point

def get_nearest_charging_stations(
    search_point: List[Tuple[float, float]], bng_dat_path: str = "./resources/bng_df.csv"
    ) -> pd.DataFrame: 

    stations = pd.read_csv(bng_dat_path)
    nearest_df = clustering.nearest_charging_stations(search_point, stations)
    return nearest_df


def get_lat_long_from_coordinates(
    coordinates: Dict[str, object]
) -> Tuple[float, float]:
    try:
        lon = coordinates["features"][0]["geometry"]["coordinates"][0]
        lat = coordinates["features"][0]["geometry"]["coordinates"][1]
        return lat, lon
    except IndexError:
        return 0.0, 0.0


def get_markers(
    origin_lat: float, origin_lon: float, destination_lat: float, destination_lon: float
) -> str:
    markers = ""
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd="origin",
        latitude=origin_lat,
        longitude=origin_lon,
    )
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd="destination",
        latitude=destination_lat,
        longitude=destination_lon,
    )
    return markers


def compute_midpoint(lat1, lon1, lat2, lon2) -> Tuple[float, float]:
    return (lat1 + lat2) / 2, (lon1 + lon2) / 2


def get_clustering_data(
    point_list: List[Tuple[float, float]], 
    origin_lat: float, 
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    bng_dat_path: str = "./resources/bng_df.csv", 
    
) -> pd.DataFrame:
    path = pd.DataFrame(point_list, columns=["lat", "lng"])

    stations = pd.read_csv(bng_dat_path)
    stations = clustering.dimension_reduction(path, origin_lat, origin_lon, dest_lat, dest_lon, stations)
    df = clustering.clustering_algo(path, stations)
    return df

def process_inputs_own_rest(
    start_point: str,
    rest_point: str,
    end_point:str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    total_distance: float,
    bng_dat_path: str = "./resources/bng_df.csv",

):  
    origin = backend.get_coordinates(start_point)
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin)

    rest_place = backend.get_coordinates(rest_point)
    rest_lat, rest_lon = get_lat_long_from_coordinates(rest_place)

    destination = backend.get_coordinates(end_point)
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination)

    closest_df = clustering.near_points([[rest_lat, rest_lon]], stations = pd.read_csv('./resources/bng_df.csv'))

    closest_df["lat_lon"] = list(zip(closest_df.Latitude, closest_df.Longitude))
    near = closest_df.loc[closest_df.Label == "Closest"]

    point = [[rest_lat,rest_lon]]
     
    dists = near['lat_lon'].apply(lambda x: geodesic(point, x).km)

    closest = near.loc[dists.idxmin()]

    rest_lat, rest_lon = closest["Latitude"], closest["Longitude"]


    point_list, distance_travelled_by_rest_place, time = backend.get_route(
        origin_lat, origin_lon, rest_lat, rest_lon
    )

    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    df = get_clustering_data(point_list,origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)

    initial_soc = float(range_start)
    final_threshold = float(range_arrival)
    total_time = 0
    total_distance = total_distance
    min_threshold = 15
    dist_travelled = 0
    range_ev = 75
    stop = 1
    range_needed = 0
    ave_speed = 40
    trip_start = start_time

    
    lst = battery.station_coordinates_own_rest(df, 
    initial_soc, 
    min_threshold, 
    total_distance, 
    dist_travelled, 
    range_ev, 
    stop, 
    final_threshold, 
    range_needed,
    ave_speed, 
    start_time, 
    trip_start, 
    total_time, 
    rest_lat, 
    rest_lon, 
    distance_travelled_by_rest_place)

    print(lst)

    if type(lst) == str:
            night_travel = False
            time_end = 0
            point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
            lst = [lst]
            idx_lst = [0]
            lst = dict(zip(idx_lst, lst))
                    
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            last_leg = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                            longitude=origin_lon,
                                                                                                    ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                            longitude=destination_lon,
                                                                                                    ))

            last_leg2 = []
            rest_charge_last_leg = []

            return (
            marker_lst,
            markers,
            mid_lat,
            mid_lon,
            point_list,
            distance,
            time,
            initial_soc,
            final_threshold,
            start_time,
            lst,
            res,
            last_leg,
            night_travel,
            time_end,
            last_leg2,
            rest_charge_last_leg)

    else:
        lstcopy = copy.deepcopy(lst)
        lst = copy.deepcopy(lst[1][0])
       
        del lstcopy[list(lstcopy.keys())[0]]

        keys = list(lst.keys())
        time_end = lst[keys[-1]][0]
        night_travel = lst[keys[-1]][1]
        if len(keys) > 1:
            last_leg = [lst[keys[-2]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))

            lst3 = copy.deepcopy(lstcopy)
            del lst3[list(lst3.keys())[-1]]
            rest_charge_last_leg = lst3[list(lst3.keys())[-1]]
            del lst3[list(lst3.keys())[-1]]

            del lst[keys[-1]]
            keys = keys[:-1]
            del lst[keys[-1]]
            marker_lst = []
            lst_coord = []

            for i in lst.keys():
                id = "stop" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )
                                )
                lst_coord.append([lst[i][2],lst[i][3]])



            for i in lst3.keys():
                id = "stoprest" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst3[i][1]),\
                                                                                        longitude=float(lst3[i][2]),
                                                                                                )
                                                                    
                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst3[i][1]),\
                                                                                        longitude=float(lst3[i][2]),
                                                                                                )
                                )
                lst_coord.append([lst3[i][1],lst3[i][2]])

            last_leg2 = lst3

            lst2 = lst_coord
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
           
            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                last_leg2,
                rest_charge_last_leg)

        else:
            rest_charge_last_leg = []
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  
            last_leg2 = []
            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                last_leg2,
                rest_charge_last_leg)      

            
        


        
    
def process_inputs(
    start_point: str,
    end_point: str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    bng_dat_path: str = "./resources/bng_df.csv",
):
    origin = backend.get_coordinates(start_point)
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin)

    destination = backend.get_coordinates(end_point)
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination)

    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    point_list, distance, time = backend.get_route(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    df = get_clustering_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)

    initial_soc = float(range_start)
    final_threshold = float(range_arrival)
    total_time = 0
    total_distance = distance
    min_threshold = 15
    dist_travelled = 0
    range_ev = 75
    stop = 1
    range_needed = 0
    ave_speed = 40
    trip_start = start_time

    lst = battery.station_coordinates(
        df,
        initial_soc,
        min_threshold,
        total_distance,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
    )

    if type(lst) == str:
        night_travel = False
        time_end = 0
        point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
        lst = [lst]
        idx_lst = [0]
        lst = dict(zip(idx_lst, lst))
                
        lst_coord = []
        lst2 = lst_coord
        marker_lst = []
        lst2.insert(0, [origin_lat, origin_lon])
        lst2.append([destination_lat, destination_lon])
        idx = [i for i in range(len(lst2))]
        res = {idx[i]: lst2[i] for i in range(len(idx))}
        last_leg = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))
        return (
        marker_lst,
        markers,
        mid_lat,
        mid_lon,
        point_list,
        distance,
        time,
        initial_soc,
        final_threshold,
        start_time,
        lst,
        res,
        last_leg,
        night_travel,
        time_end)

    else:
        keys = list(lst.keys())
        time_end = lst[keys[-1]][0]
        night_travel = lst[keys[-1]][1]
        if len(keys) > 1:
            last_leg = [lst[keys[-2]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))

            lst3 = copy.deepcopy(lst)

            del lst[keys[-1]]
            keys = keys[:-1]
            del lst[keys[-1]]
            marker_lst = []
            lst_coord = []

            for i in lst.keys():
                id = "stop" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )
                                )
                lst_coord.append([lst[i][2],lst[i][3]])

            

            df = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
            for i in lst_coord:
                df2 = backend.get_POI(i[0], i[1])
                df = pd.concat([df, df2],ignore_index=True)
            
            for index, row in df.iterrows():
                id = "POI" + str(index)
                
                
                markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                        longitude=float(row[3]),
                                                                                        name = row[0],
                                                                                        category = row[1] )
                
                data = f"{row[0]}, {row[1]}"                                                                        
                markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                        longitude=float(row[3]),
                                                                                                ))
            

            lst2 = lst_coord
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
           
            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end)

        else:
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  

            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end)      


def process_inputs_nonight(
    start_point: str,
    end_point: str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    bng_dat_path: str = "./resources/bng_df.csv",
):
    origin = backend.get_coordinates(start_point)
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin)

    destination = backend.get_coordinates(end_point)
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination)

    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    point_list, distance, time = backend.get_route(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    df = get_clustering_data(point_list,origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)

    initial_soc = float(range_start)
    final_threshold = float(range_arrival)
    total_time = 0
    total_distance = distance
    min_threshold = 15
    dist_travelled = 0
    range_ev = 75
    stop = 1
    range_needed = 0
    ave_speed = 40
    trip_start = start_time

    lst = battery.station_coordinates_no_night(
        df,
        initial_soc,
        min_threshold,
        total_distance,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
    )
    
    print(lst)
    if type(lst) == str:
        night_travel = False
        time_end = 0
        point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
        lst = [lst]
        idx_lst = [0]
        lst = dict(zip(idx_lst, lst))
                
        lst_coord = []
        lst2 = lst_coord
        marker_lst = []
        lst2.insert(0, [origin_lat, origin_lon])
        lst2.append([destination_lat, destination_lon])
        idx = [i for i in range(len(lst2))]
        res = {idx[i]: lst2[i] for i in range(len(idx))}
        last_leg = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))
        return (
        marker_lst,
        markers,
        mid_lat,
        mid_lon,
        point_list,
        distance,
        time,
        initial_soc,
        final_threshold,
        start_time,
        lst,
        res,
        last_leg,
        night_travel,
        time_end)

    else:
        keys = list(lst.keys())
        time_end = lst[keys[-1]][0]
        night_travel = lst[keys[-1]][1]
        if len(keys) > 1:
            last_leg = [lst[keys[-2]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))

            lst3 = copy.deepcopy(lst)

            del lst[keys[-1]]
            keys = keys[:-1]
            del lst[keys[-1]]
            marker_lst = []
            lst_coord = []

            for i in lst.keys():
                id = "stop" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )
                                )
                lst_coord.append([lst[i][2],lst[i][3]])
            
            lst2 = lst_coord
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
           
            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end)

        else:
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  

            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end)      
