import datetime
import math
import pandas as pd
import numpy as np
from itertools import chain
from geoguide.server import app, db, datasets
from geoguide.server.models import AttributeType
from geoguide.server.iuga import run_iuga
from geoguide.server.similarity import cosine_similarity, jaccard_similarity


def path_to_hdf(dataset):
    return '{}.h5'.format(datasets.path(dataset.filename).rsplit('.', 1)[0])


def save_as_hdf(dataset):
    datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
    path_to_csv = datasets.path(dataset.filename)
    df = pd.read_csv(path_to_csv, parse_dates=datetime_columns, infer_datetime_format=True)
    path_to_h5 = '{}.h5'.format(path_to_csv.rsplit('.', 1)[0])
    df.to_hdf(path_to_h5, 'data')


def index_dataset(dataset):
    with app.app_context():
        hdf_path = path_to_hdf(dataset)

        ds = []
        ds_datetimes = {}
        ds_numerics = {}

        df = pd.read_hdf(hdf_path, 'data')

        datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
        len_datetime_columns = len(datetime_columns)
        # point = df.loc[index]
        numeric_columns = list(df.select_dtypes(include=[np.number]).columns)
        numeric_columns = [c for c in numeric_columns if 'latitude' not in c and 'longitude' not in c and not df[c].isnull().any()]
        df = df.loc[:, [dataset.latitude_attr, dataset.longitude_attr, *numeric_columns, *datetime_columns]]
        # point_numerics = [point[c] for c in numeric_columns]
        # point_datetimes = list(chain.from_iterable([[point[c].hour, point[c].minute, point[c].weekday()] for c in datetime_columns]))
        greatest_distance = 0
        greatest_similarity = 0

        x = 1
        for row_a in df.itertuples():
            print('Current:', x)
            if row_a[1] == 0 or row_a[2] == 0:
                x += 1
                continue
            if row_a[0] not in ds_datetimes:
                ds_datetimes[row_a[0]] = list(chain.from_iterable([[d.hour, d.minute, d.weekday()] for d in row_a[-len_datetime_columns:]]))
            if row_a[0] not in ds_numerics:
                ds_numerics[row_a[0]] = row_a[3:-len_datetime_columns]
            for row_b in df.loc[x:].itertuples():
                if row_b[1] == 0 or row_b[2] == 0:
                    continue
                if row_b[0] not in ds_datetimes:
                    ds_datetimes[row_b[0]] = list(chain.from_iterable([[d.hour, d.minute, d.weekday()] for d in row_b[-len_datetime_columns:]]))
                if row_b[0] not in ds_numerics:
                    ds_numerics[row_b[0]] = row_b[3:-len_datetime_columns]
                distance = harvestine_distance(row_a[1], row_a[2],
                                               row_b[1], row_b[2])
                similarity_i = (1 + jaccard_similarity(ds_datetimes[row_a[0]], ds_datetimes[row_b[0]]))
                similarity_ii = (1 + cosine_similarity(ds_numerics[row_a[0]], ds_numerics[row_b[0]]))
                similarity = similarity_i + similarity_ii
                ds.append((row_a[0], row_b[0], similarity, distance))
                if distance > greatest_distance:
                    greatest_distance = distance
                if similarity > greatest_similarity:
                    greatest_similarity = similarity
            x += 1

        df_relation = pd.DataFrame(
            ds, columns=['index_a', 'index_b', 'similarity', 'distance']
        ).assign(
            similarity=lambda x: x.similarity / greatest_similarity,
            distance=lambda x: x.distance / greatest_distance
        )

        df_relation.to_hdf(hdf_path, 'relation')
        dataset.indexed_at = datetime.datetime.now()
        db.session.add(dataset)
        db.session.commit()


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
