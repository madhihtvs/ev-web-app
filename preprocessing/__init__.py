from typing import Dict, List, Tuple
from unicodedata import category

import pandas as pd
import copy
from geopy.distance import geodesic

import preprocessing.backend as backend
import preprocessing.battery as battery
import preprocessing.clustering as clustering

def _get_intermediate_points(request_values):
    intermediate_points = []
    keys = request_values.keys()
    matching = list(filter(lambda s: 'intermediate' in s, keys))
    for value in matching:
        intermediate_points.append(request_values[value])
    return intermediate_points

def collect_user_inputs(request_values):
    start_point = request_values.get("start-point")
    end_point = request_values.get("end-point")
    intermediate_points = _get_intermediate_points(request_values)
    range_start = request_values.get("range-start")
    range_arrival = request_values.get("range-arrival")
    start_time = request_values.get("start-time")
    start_time = f"{start_time}:00"
    poi_radius = request_values.get("poi-radius")
    return start_point, end_point, range_start, range_arrival, start_time, intermediate_points, poi_radius

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
    orig_address = backend.get_address(origin_lat, origin_lon)
    dest_address = backend.get_address(destination_lat, destination_lon)
    
    markers = ""
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd="origin",
        latitude=origin_lat,
        longitude=origin_lon,
    )

    markers += """{idd}.bindPopup("{address}");""".format(idd=f"origin", address = f"{orig_address}")
    
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd="destination",
        latitude=destination_lat,
        longitude=destination_lon,
    )
    markers += """{idd}.bindPopup("{address}");""".format(idd=f"destination", address = f"{dest_address}")
    
    return markers


def get_markers_intermediate(markers, lst):
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd=f"intermediate{lst[0]+1}",
        latitude=lst[1],
        longitude=lst[2],
    )
    markers += """{idd}.bindPopup("{data}");""".format(idd=f"intermediate{lst[0]+1}", data = f"Intermediate Point {lst[0]+1}")
    return markers


def compute_midpoint(lat1, lon1, lat2, lon2) -> Tuple[float, float]:
    return (lat1 + lat2) / 2, (lon1 + lon2) / 2



def get_stations_data(
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
    return stations

def get_clustering_data(
    point_list: List[Tuple[float, float]], 
    origin_lat: float, 
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    stations: pd.DataFrame,
    bng_dat_path: str = "./resources/bng_df.csv", 
    
) -> pd.DataFrame:
    path = pd.DataFrame(point_list, columns=["lat", "lng"])

    # stations = pd.read_csv(bng_dat_path)
    # stations = clustering.dimension_reduction(path, origin_lat, origin_lon, dest_lat, dest_lon, stations)
    df = clustering.clustering_algo(path, stations)
    return df

def process_inputs_own_rest(
    start_point: str,
    rest_point: str,
    end_point:str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    intermediate_points: list,
    total_distance: float,
    bng_dat_path: str = "./resources/bng_df.csv",

):  
    origin = backend.get_coordinates(start_point)
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin)

    rest_place = backend.get_coordinates(rest_point)
    rest_lat, rest_lon = get_lat_long_from_coordinates(rest_place)

    accom_lat, accom_lon = rest_lat, rest_lon

    destination = backend.get_coordinates(end_point)
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination)

    intermediate_points_coords = []
    
    for i in range(len(intermediate_points)):
        location = intermediate_points[i]
        coords = backend.get_coordinates(location)
        intermediate_lat, intermediate_lon = get_lat_long_from_coordinates(coords)
        intermediate_points_coords.append([i, intermediate_lat, intermediate_lon])
    
    
    closest_df = clustering.near_points([[rest_lat, rest_lon]], stations = pd.read_csv('./resources/bng_df.csv'))

    closest_df["lat_lon"] = list(zip(closest_df.Latitude, closest_df.Longitude))
    near = closest_df.loc[closest_df.Label == "Closest"]

    point = [[rest_lat,rest_lon]]
     
    dists = near['lat_lon'].apply(lambda x: geodesic(point, x).km)

    closest = near.loc[dists.idxmin()]

    rest_lat, rest_lon = closest["Latitude"], closest["Longitude"]

    
    

    if len(intermediate_points_coords) > 0:
        points = []
        for i in intermediate_points_coords:
            points.append([i[1],i[2]])
        points.insert(0, [origin_lat, origin_lon])
        points.append([rest_lat, rest_lon])

        point_list, distance_travelled_by_rest_place, time = backend.get_route_many(points)
        point_list_alt_1, distance_travelled_by_rest_place_alt_1, time_alt_1 = backend.get_route_many_short(points)

        points.append([destination_lat, destination_lon])
        point_list_complete, dist_complete, time_complete = backend.get_route_many(points)
        point_list_complete_alt, dist_complete_alt, time_complete_alt = backend.get_route_many_short(points)
    else:
        points = []
        points.insert(0, [origin_lat, origin_lon])
        points.append([rest_lat, rest_lon])
        points.append([destination_lat, destination_lon])

        point_list, distance_travelled_by_rest_place, time = backend.get_route(
            origin_lat, origin_lon, rest_lat, rest_lon
        )
        point_list_alt_1, distance_travelled_by_rest_place_alt_1, time_alt_1 = backend.get_route_short(
            origin_lat, origin_lon, rest_lat, rest_lon
        )
        point_list_complete, dist_complete, time_complete = backend.get_route_many(points)
        point_list_complete_alt, dist_complete_alt, time_complete_alt = backend.get_route_many_short(points)

        point_list_complete, dist_complete, time_complete = backend.get_route_many(points)
        point_list_complete_alt, dist_complete_alt, time_complete_alt = backend.get_route_many_short(points)


  
    stations = get_stations_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)
    

    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    
    for i in intermediate_points_coords:
        markers = get_markers_intermediate(markers, i)

    
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    df = get_clustering_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    df_alt_1 = get_clustering_data(point_list_alt_1, origin_lat, origin_lon, destination_lat, destination_lon,stations, bng_dat_path)
    
    df_complete = get_clustering_data(point_list_complete, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    df_complete_alt = get_clustering_data(point_list_complete_alt, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    

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

    
    lst = battery.station_coordinates_own_rest(
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
        rest_lat, 
        rest_lon, 
        distance_travelled_by_rest_place,
        df_complete)

    lst_alt_1 = battery.station_coordinates_own_rest(
        df_alt_1,
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
        distance_travelled_by_rest_place_alt_1,
        df_complete_alt
    )

    if lst == "Trip cannot be completed as no charging station is available in the vicinity":
        return None
    if type(lst) == str or type(lst_alt_1) == str:
            night_travel = False
            time_end = 0
            if len(intermediate_points_coords) < 1:
                point_list, distance, time = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
            else:
                point_list, distance, time = backend.get_route_many_short(points)

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


            night_travel_alt = False
            time_end_alt = 0
            if len(intermediate_points_coords) < 1:
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
            else:
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)
        
            lst_alt_1 = [lst_alt_1]
            idx_lst_alt = [0]
            lst_alt_1 = dict(zip(idx_lst_alt, lst_alt_1))
                    
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            last_leg_alt = {0: [initial_soc, distance_alt_1, initial_soc - (distance_alt_1/ (range_ev/100))]}


            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                            longitude=origin_lon,
                                                                                                    ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                            longitude=destination_lon,
                                                                                                    ))

            last_leg2_alt = []
            rest_charge_last_leg_alt = []
            markers_alt = markers

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
            rest_charge_last_leg,
            
            
            marker_lst_alt,
            markers_alt,
            mid_lat,
            mid_lon,
            point_list_alt_1,
            distance_alt_1,
            time_alt_1,
            initial_soc,
            final_threshold,
            start_time,
            lst_alt_1,
            res_alt,
            last_leg_alt,
            night_travel_alt,
            time_end_alt,
            last_leg2_alt,
            rest_charge_last_leg_alt)

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
                markers += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
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
                markers += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst3[i][1]),\
                                                                                        longitude=float(lst3[i][2]),
                                                                                                )
                                                                    
                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst3[i][1]),\
                                                                                        longitude=float(lst3[i][2]),
                                                                                                )
                                )
                lst_coord.append([lst3[i][1],lst3[i][2]])

            
            rest_address = backend.get_address(accom_lat, accom_lon)
            id = "restlocationbyuser"
            markers += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_Hotel);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(accom_lat),\
                                                                                        longitude=float(accom_lon),
                                                                               
                                                                                         )
            name_accom = f"{rest_address}"                                                                        
            markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = name_accom)




            last_leg2 = lst3

            lst2 = lst_coord
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)


            #For alternative route1
            lstcopy_alt = copy.deepcopy(lst_alt_1)
            lst_alt_1 = copy.deepcopy(lst_alt_1[1][0])
 
            del lstcopy_alt[list(lstcopy_alt.keys())[0]]


            keys_alt = list(lst_alt_1.keys())
            time_end_alt = lst_alt_1[keys_alt[-1]][0]
            night_travel_alt = lst_alt_1[keys_alt[-1]][1]
            if len(keys_alt) > 1:
                last_leg_alt = [lst_alt_1[keys_alt[-2]]]
                idx_lst_alt = [0]
                last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
                
                lst3_alt = copy.deepcopy(lstcopy_alt)
  
                del lst3_alt[list(lst3_alt.keys())[-1]]

                rest_charge_last_leg_alt = lst3_alt[list(lst3_alt.keys())[-1]]
                del lst3_alt[list(lst3_alt.keys())[-1]]

                del lst_alt_1[keys_alt[-1]]
                keys_alt = keys_alt[:-1]
                del lst_alt_1[keys_alt[-1]]
                marker_lst_alt = []
                lst_coord_alt = []
                
                markers_alt = markers

                for i in lst_alt_1.keys():
                    id = "stop_alt" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                            longitude=float(lst[i][3]),
                                                                                                    )

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                            longitude=float(lst[i][3]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst[i][2],lst[i][3]])



                for i in lst3_alt.keys():
                    id = "stoprest_alt" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(lst3[i][1]),\
                                                                                            longitude=float(lst3[i][2]),
                                                                                                    )
                                                                        
                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst3[i][1]),\
                                                                                            longitude=float(lst3[i][2]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst3[i][1],lst3[i][2]])


                rest_address = backend.get_address(accom_lat, accom_lon)
                id = "restlocationbyuser"
                markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_Hotel);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(accom_lat),\
                                                                                            longitude=float(accom_lon),
                                                                                    
                                                                                                    )
                name_accom = f"{rest_address}"                                                                        
                markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id, data = name_accom)


                last_leg2_alt = lst3_alt

                lst2_alt = lst_coord_alt
                lst2_alt.insert(0, [origin_lat, origin_lon])
                if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
                lst2_alt.append([destination_lat, destination_lon])
                idx_alt = [i for i in range(len(lst2_alt))]
                res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many(lst2_alt)
                
            
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
                    rest_charge_last_leg,
                    
                    marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt,
                    last_leg2_alt,
                    rest_charge_last_leg_alt)

        else:
            rest_charge_last_leg = []
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
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


            rest_charge_last_leg_alt = []
            last_leg_alt = [lst_alt_1[keys_alt[-1]]]
            idx_lst_alt = [0]
            last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many(lst2_alt)
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  
            last_leg2_alt = []


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
                rest_charge_last_leg,
                
                marker_lst_alt,
                markers_alt,
                mid_lat,
                mid_lon,
                point_list_alt_1,
                distance_alt_1,
                time_alt_1,
                initial_soc,
                final_threshold,
                start_time,
                lst_alt_1,
                res_alt,
                last_leg_alt,
                night_travel_alt,
                time_end_alt,
                last_leg2_alt,
                rest_charge_last_leg_alt)      

            
        


        
    
def process_inputs(
    start_point: str,
    end_point: str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    intermediate_points: list,
    poi_radius: int,
    bng_dat_path: str = "./resources/bng_df.csv",
):
    
    origin = backend.get_coordinates(start_point)
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin)

    destination = backend.get_coordinates(end_point)
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination)

    intermediate_points_coords = []
    
    for i in range(len(intermediate_points)):
        location = intermediate_points[i]
        coords = backend.get_coordinates(location)
        intermediate_lat, intermediate_lon = get_lat_long_from_coordinates(coords)
        intermediate_points_coords.append([i, intermediate_lat, intermediate_lon])
    
  
    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)

    for i in intermediate_points_coords:
        markers = get_markers_intermediate(markers, i)


    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )
 
    
    

    if len(intermediate_points_coords) > 0:
        points = []
        for i in intermediate_points_coords:
            points.append([i[1],i[2]])
        points.insert(0, [origin_lat, origin_lon])
        points.append([destination_lat, destination_lon])
        point_list, distance, time = backend.get_route_many(points)
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)

    else:


        point_list, distance, time = backend.get_route(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
    
    
    
    stations = get_stations_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)
    

    if len(intermediate_points_coords) > 0:
        df_near = pd.DataFrame(columns = ["Station Name","Longitude","Latitude","Label"])
        for i in intermediate_points_coords:
            pt = [[i[1],i[2]]]
            df = clustering.near_points(pt, stations)
            df = df.drop_duplicates()
            df_near = pd.concat([df_near, df])
        
    
        for idx, row in df_near.iterrows():
            markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                    {idd}.addTo(map);".format(
            idd=f"charging_near_intermediate_{idx+1}",
            latitude=row[2],
            longitude=row[1],
        )
            markers += """{idd}.bindPopup("{data}");""".format(idd=f"charging_near_intermediate_{idx+1}", data = f"Charging Point: {row[0]}")
    
    
    df = get_clustering_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    df_alt_1 = get_clustering_data(point_list_alt_1, origin_lat, origin_lon, destination_lat, destination_lon,stations, bng_dat_path)
    

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
    
    lst_alt_1 = battery.station_coordinates(
        df_alt_1,
        initial_soc,
        min_threshold,
        distance_alt_1,
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

    if lst == "Trip cannot be completed as no charging station is available in the vicinity":
        return None

    if type(lst) == str:
        night_travel = False
        time_end = 0

        if len(intermediate_points_coords) < 1:
            point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list, distance, time = backend.get_route_many(points)
        

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



        night_travel_alt = False
        time_end_alt = 0
        if len(intermediate_points_coords) < 1:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)
        
            

        lst_alt_1 = [lst_alt_1]
        idx_lst_alt = [0]
        lst_alt_1 = dict(zip(idx_lst_alt, lst_alt_1))
                
        lst_coord_alt = []
        lst2_alt = lst_coord_alt
        marker_lst_alt = []
        lst2_alt.insert(0, [origin_lat, origin_lon])
        lst2_alt.append([destination_lat, destination_lon])
        idx_alt = [i for i in range(len(lst2_alt))]
        res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
        last_leg_alt = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))

        markers_alt = markers                                                 
                               
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
        
        marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

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
                markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
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
                df2 = backend.get_POI(i[0], i[1], poi_radius)
                df = pd.concat([df, df2],ignore_index=True)
            
            for index, row in df.iterrows():
                id = "POI" + str(index)
                
                
                markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_POI);\
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
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
           

            # For alternate route 1
        
            keys_alt = list(lst_alt_1.keys())
            time_end_alt = lst_alt_1[keys_alt[-1]][0]
            night_travel_alt = lst_alt_1[keys_alt[-1]][1]
            if len(keys_alt) > 1:
                last_leg_alt = [lst_alt_1[keys_alt[-2]]]
                idx_lst_alt = [0]
                last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))

                lst3_alt = copy.deepcopy(lst_alt_1)

                del lst_alt_1[keys_alt[-1]]
                keys_alt = keys_alt[:-1]
                del lst_alt_1[keys_alt[-1]]
                marker_lst_alt = []
                lst_coord_alt = []
                markers_alt = markers

                for i in lst_alt_1.keys():
                    id_alt = "stop" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id_alt, latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst_alt_1[i][2],lst_alt_1[i][3]])

                

                df_alt = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
                for i in lst_coord_alt:
                    df2 = backend.get_POI(i[0], i[1], poi_radius)
                    df_alt = pd.concat([df_alt, df2],ignore_index=True)
                
                for index, row in df_alt.iterrows():
                    id_alt = "POI_alt" + str(index)
                    
                    
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_POI);\
                                                    {idd}.addTo(map);".format(idd=id_alt, latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                            name = row[0],
                                                                                            category = row[1] )
                    
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id_alt, data = data)

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                                    ))
                

                lst2_alt = lst_coord_alt
                lst2_alt.insert(0, [origin_lat, origin_lon])
                if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
                lst2_alt.append([destination_lat, destination_lon])
                idx_alt = [i for i in range(len(lst2_alt))]
                res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)


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
                    
                    marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

        else:
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2.append([i[1], i[2]])
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

            
            last_leg_alt = [lst_alt_1[keys_alt[-1]]]
            idx_lst_alt = [0]
            last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
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
                time_end,
                
                    marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt 
                )      
    

def process_inputs_nonight(
    start_point: str,
    end_point: str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    intermediate_points: list,
    poi_radius: int,
    bng_dat_path: str = "./resources/bng_df.csv",
):
    origin = backend.get_coordinates(start_point)
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin)

    destination = backend.get_coordinates(end_point)
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination)


    intermediate_points_coords = []
    
    for i in range(len(intermediate_points)):
        location = intermediate_points[i]
        coords = backend.get_coordinates(location)
        intermediate_lat, intermediate_lon = get_lat_long_from_coordinates(coords)
        intermediate_points_coords.append([i, intermediate_lat, intermediate_lon])
    


    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    
    for i in intermediate_points_coords:
        markers = get_markers_intermediate(markers, i)


    
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )
    if len(intermediate_points_coords) > 0:
        points = []
        for i in intermediate_points_coords:
            points.append([i[1],i[2]])
        points.insert(0, [origin_lat, origin_lon])
        points.append([destination_lat, destination_lon])
        point_list, distance, time = backend.get_route_many(points)
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)

    else:
        point_list, distance, time = backend.get_route(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
    

    stations = get_stations_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)
    
    if len(intermediate_points_coords) > 0:
        df_near = pd.DataFrame(columns = ["Station Name","Longitude","Latitude","Label"])
        for i in intermediate_points_coords:
            pt = [[i[1],i[2]]]
            df = clustering.near_points(pt, stations)
            df = df.drop_duplicates()
            df_near = pd.concat([df_near, df])
        
    
        for idx, row in df_near.iterrows():
            markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                    {idd}.addTo(map);".format(
            idd=f"charging_near_intermediate_{idx+1}",
            latitude=row[2],
            longitude=row[1],
        )
            markers += """{idd}.bindPopup("{data}");""".format(idd=f"charging_near_intermediate_{idx+1}", data = f"Charging Point: {row[0]}")
    
    
    
    df = get_clustering_data(point_list,origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    df_alt_1 = get_clustering_data(point_list_alt_1, origin_lat, origin_lon, destination_lat, destination_lon,stations, bng_dat_path)
    


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

    lst_alt_1 = battery.station_coordinates_no_night(
        df_alt_1,
        initial_soc,
        min_threshold,
        distance_alt_1,
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

        if len(intermediate_points_coords) < 1:
            point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list, distance, time = backend.get_route_many(points)
        



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
                                                                                        longitude=origin_lon,
                                                                                                ))
        
        night_travel_alt = False
        time_end_alt = 0

        if len(intermediate_points_coords) < 1:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)
        
            

        lst_alt_1 = [lst_alt_1]
        idx_lst_alt = [0]
        lst = dict(zip(idx_lst_alt, lst_alt_1))
                
        lst_coord_alt = []
        lst2_alt = lst_coord_alt
        marker_lst_alt = []
        lst2_alt.insert(0, [origin_lat, origin_lon])
        lst2_alt.append([destination_lat, destination_lon])
        idx_alt = [i for i in range(len(lst2_alt))]
        
        res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
        last_leg_alt = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}

        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                     longitude=destination_lon,
        markers_alt = markers    
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
        time_end,
        
        marker_lst_alt,
        markers_alt,
        mid_lat,
                mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

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
                markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
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
                df2 = backend.get_Hotel(i[0], i[1])
                df3 = backend.get_POI(i[0], i[1], poi_radius)

                df = pd.concat([df, df2, df3],ignore_index=True)
            
            for index, row in df.iterrows():
                if row[1] != "accommodation":
                    id = "Hotel" + str(index)

                    markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_POI);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                            name = row[0],
                                                                                            category = row[1] )
                    
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                                    ))

                else:
                    id = "POI" + str(index)
            
                    markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_Hotel);\
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
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
           
            # For alternate route 1
            keys_alt = list(lst_alt_1.keys())
            time_end_alt = lst_alt_1[keys_alt[-1]][0]
            night_travel_alt = lst_alt_1[keys_alt[-1]][1]
            if len(keys_alt) > 1:
                last_leg_alt = [lst_alt_1[keys_alt[-2]]]
                idx_lst_alt = [0]
                last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))

                lst3_alt = copy.deepcopy(lst_alt_1)

                del lst_alt_1[keys_alt[-1]]
                keys_alt = keys_alt[:-1]
                del lst_alt_1[keys_alt[-1]]
                marker_lst_alt = []
                lst_coord_alt = []
                markers_alt = markers

                for i in lst_alt_1.keys():
                    id_alt = "stop" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id_alt, latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst_alt_1[i][2],lst_alt_1[i][3]])

            df_alt = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
            for i in lst_coord_alt:
                df2 = backend.get_Hotel(i[0], i[1])
                df3 = backend.get_POI(i[0], i[1], poi_radius)
                df_alt = pd.concat([df_alt, df2 ,df3],ignore_index=True)
                
            for index, row in df_alt.iterrows():
                if row[1] != "accommodation":
                    id = "Hotel" + str(index)

                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_POI);\
                                                                {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                        name = row[0],
                                                                                                        category = row[1] )
                                
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                                ))

                else:
                    id = "POI" + str(index)
                        
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_Hotel);\
                                                                {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                        name = row[0],
                                                                                                        category = row[1] )
                                
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                                ))                                                                     
                
            lst2_alt = lst_coord_alt
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]

            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)
                                                                                                


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
                
                marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

        else:
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2.append([i[1], i[2]])
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

                                                                                                
            last_leg_alt = [lst_alt_1[keys_alt[-1]]]
            idx_lst_alt = [0]
            last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
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
                time_end,
                marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt )      
