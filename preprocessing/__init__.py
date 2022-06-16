from typing import Dict, List, Tuple

import pandas as pd

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
    point_list: List[Tuple[float, float]], bng_dat_path: str = "./resources/bng_df.csv"
) -> pd.DataFrame:
    path = pd.DataFrame(point_list, columns=["lat", "lng"])

    stations = pd.read_csv(bng_dat_path)
    _, df = clustering.clustering_algo(path, stations)
    return df


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

    df = get_clustering_data(point_list, bng_dat_path)

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

    for i in lst.keys():
        id = "stop" + str(i)
        markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                    {idd}.addTo(map);".format(
            idd=id,
            latitude=float(lst[i][0]),
            longitude=float(lst[i][1]),
        )
    return (
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
    )
