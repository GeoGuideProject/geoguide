import math
import pandas as pd
from geoguide.server import datasets
from geoguide.server.models import AttributeType

def path_to_hdf5(filename):
    return '{}.h5'.format(datasets.path(filename).rsplit('.', 1)[0])


def save_as_hdf5(dataset):
    datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
    path_to_csv = datasets.path(dataset.filename)
    df = pd.read_csv(path_to_csv, parse_dates=datetime_columns, infer_datetime_format=True)
    path_to_h5 = '{}.h5'.format(path_to_csv.rsplit('.', 1)[0])
    df.to_hdf(path_to_h5, 'data')


def harvestine_distance(lat1, lng1, lat2, lng2):
    try:
        dept_lat_rad = math.radians(lat1)
        dept_lng_rad = math.radians(lng1)
        arr_lat_rad = math.radians(lat2)
        arr_lng_rad = math.radians(lng2)
        earth_radius = 3963.1
        d = math.acos(math.cos(dept_lat_rad) * math.cos(dept_lng_rad) * math.cos(arr_lat_rad) * math.cos(arr_lng_rad) + math.cos(dept_lat_rad) *
                      math.sin(dept_lng_rad) * math.cos(arr_lat_rad) * math.sin(arr_lng_rad) + math.sin(dept_lat_rad) * math.sin(arr_lat_rad)) * earth_radius
        return round(d, 2)
    except ValueError:
        return 0
