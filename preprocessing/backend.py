import pandas as pd
import requests


def get_coordinates(location):
    url = "https://api.geoapify.com/v1/geocode/search"

    params = dict(text=location, apiKey="af361475cd624479ab85363a1893eab1")

    resp = requests.get(url=url, params=params)
    data = resp.json()

    return data

def get_address(lat, lon):
    url = "https://api.geoapify.com/v1/geocode/reverse"
    
    params = dict(lat=lat,
                  lon = lon, 
                  apiKey="af361475cd624479ab85363a1893eab1")

    resp = requests.get(url=url, params=params)
    data = resp.json()

    address1 = data["features"][0]["properties"]["address_line1"]
    address2 = data["features"][0]["properties"]["address_line2"]
    address = address1 + ", " + address2

    return address
    

def get_POI(lat, lon, radius):

    url = "https://api.geoapify.com/v2/places"
    params = dict(
        categories='entertainment,catering,commercial,leisure,tourism',
        filter=f'circle:{lon},{lat},{radius}',
        bias=f'proximity:{lon},{lat}',
        limit=20,
        apiKey='af361475cd624479ab85363a1893eab1'
    )

    resp = requests.get(url=url, params=params)
    data = resp.json()
    features = data["features"]

    POI = []
    for i in range(len(features)):
        try:
            name = features[i]["properties"]["name"]
        except:
            name = features[i]["properties"]["street"]
        category = features[i]["properties"]["categories"][0]
        lat = features[i]["geometry"]["coordinates"][::-1][0]
        lon = features[i]["geometry"]["coordinates"][::-1][1]
        POI.append([name, category, lat, lon])

    df = pd.DataFrame(POI, columns = ["Name","Category","Latitude", "Longitude"])
    return df


def get_Hotel(lat, lon):
    url = "https://api.geoapify.com/v2/places"
    params = dict(
        categories='accommodation',
        filter=f'circle:{lon},{lat},5000',
        bias=f'proximity:{lon},{lat}',
        limit=20,
        apiKey='af361475cd624479ab85363a1893eab1'
    )

    resp = requests.get(url=url, params=params)
    data = resp.json()
    features = data["features"]

    POI = []
    for i in range(len(features)):
        try:
            name = features[i]["properties"]["name"]
        except:
            name = features[i]["properties"]["street"]
        category = features[i]["properties"]["categories"][0]
        lat = features[i]["geometry"]["coordinates"][::-1][0]
        lon = features[i]["geometry"]["coordinates"][::-1][1]
        POI.append([name, category, lat, lon])

    df = pd.DataFrame(POI, columns = ["Name","Category","Latitude", "Longitude"])
    return df




def get_route(orig_lat, orig_lon, dest_lat, dest_lon):
    url = "https://api.geoapify.com/v1/routing"
    querystring = {
        "waypoints": f"{orig_lat},{orig_lon}|{dest_lat},{dest_lon}",
        "mode": "motorcycle",
        "type": "balanced",
        "apiKey": "af361475cd624479ab85363a1893eab1",
    }
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    linestring = data["features"][0]["geometry"]["coordinates"][0]
    df = pd.DataFrame(linestring)
    df.columns = ["lon", "lat"]
    df = df.reindex(["lat", "lon"], axis=1)
    lst = df.values.tolist()
    distance = data["features"][0]["properties"]["distance"]
    time = data["features"][0]["properties"]["time"]
    distance = distance / 1000

    return lst, distance, time

def get_route_short(orig_lat, orig_lon, dest_lat, dest_lon):
    url = "https://api.geoapify.com/v1/routing"
    querystring = {
        "waypoints": f"{orig_lat},{orig_lon}|{dest_lat},{dest_lon}",
        "mode": "motorcycle",
        'type': "short",
        "apiKey": "af361475cd624479ab85363a1893eab1",
    }
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    linestring = data["features"][0]["geometry"]["coordinates"][0]
    df = pd.DataFrame(linestring)
    df.columns = ["lon", "lat"]
    df = df.reindex(["lat", "lon"], axis=1)
    lst = df.values.tolist()
    distance = data["features"][0]["properties"]["distance"]
    time = data["features"][0]["properties"]["time"]
    distance = distance / 1000

    return lst, distance, time

def get_route_less_maneuvers(orig_lat, orig_lon, dest_lat, dest_lon):
    url = "https://api.geoapify.com/v1/routing"
    querystring = {
        "waypoints": f"{orig_lat},{orig_lon}|{dest_lat},{dest_lon}",
        "mode": "motorcycle",
        'type': "less_maneuvers",
        "apiKey": "af361475cd624479ab85363a1893eab1",
    }
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    linestring = data["features"][0]["geometry"]["coordinates"][0]
    df = pd.DataFrame(linestring)
    df.columns = ["lon", "lat"]
    df = df.reindex(["lat", "lon"], axis=1)
    lst = df.values.tolist()
    distance = data["features"][0]["properties"]["distance"]
    time = data["features"][0]["properties"]["time"]
    distance = distance / 1000

    return lst, distance, time


def get_route_geojson(orig_lat, orig_lon, dest_lat, dest_lon):
    url = "https://api.geoapify.com/v1/routing"
    querystring = {
        "waypoints": f"{orig_lat},{orig_lon}|{dest_lat},{dest_lon}",
        "mode": "motorcycle",
        "apiKey": "af361475cd624479ab85363a1893eab1",
    }
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    return data



def get_route_many(*points):
    string = ""
    for i in points[0]:
        lat = i[0]
        lng = i[1]

        string += f"{lat},{lng}|"
    string = string[:-1]
    url = "https://api.geoapify.com/v1/routing"
    querystring = {
        
        "waypoints": string,
        "mode": "motorcycle",
        'type': "short",
        "apiKey": "af361475cd624479ab85363a1893eab1",
    }
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    linestring = []
    for i in range(len(points[0])-1):
        linestring.extend(data["features"][0]["geometry"]["coordinates"][i])
    df = pd.DataFrame(linestring)
    df.columns = ["lon", "lat"]
    df = df.reindex(["lat", "lon"], axis=1)
    lst = df.values.tolist()
    distance = data["features"][0]["properties"]["distance"]
    time = data["features"][0]["properties"]["time"]
    distance = distance / 1000

    return lst, distance, time


def get_route_many_short(*points):
    string = ""
    for i in points[0]:
        lat = i[0]
        lng = i[1]

        string += f"{lat},{lng}|"
    string = string[:-1]
    url = "https://api.geoapify.com/v1/routing"
    querystring = {
        
        "waypoints": string,
        "mode": "motorcycle",
        "apiKey": "af361475cd624479ab85363a1893eab1",
    }
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    linestring = []
    for i in range(len(points[0])-1):
        linestring.extend(data["features"][0]["geometry"]["coordinates"][i])
    df = pd.DataFrame(linestring)
    df.columns = ["lon", "lat"]
    df = df.reindex(["lat", "lon"], axis=1)
    lst = df.values.tolist()
    distance = data["features"][0]["properties"]["distance"]
    time = data["features"][0]["properties"]["time"]
    distance = distance / 1000

    return lst, distance, time
