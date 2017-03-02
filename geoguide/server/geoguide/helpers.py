
import datetime
import math
import pandas as pd
import numpy as np
import os
import shutil
from itertools import chain
from geoguide.server import app, db, datasets
from geoguide.server.models import AttributeType
from geoguide.server.similarity import cosine_similarity, jaccard_similarity
from threading import Thread

CHUNKSIZE = app.config['CHUNKSIZE']


def path_to_hdf(dataset):
    return '{}.h5'.format(datasets.path(dataset.filename).rsplit('.', 1)[0])


def save_as_hdf(dataset):
    datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
    original_csv_path = datasets.path(dataset.filename)
    csv_path = '{}.normalized.csv'.format(original_csv_path.rsplit('.', 1)[0])
    hdf_path = '{}.h5'.format(original_csv_path.rsplit('.', 1)[0])
    is_first = True
    store = pd.HDFStore(hdf_path)
    for df in pd.read_csv(original_csv_path, parse_dates=datetime_columns, infer_datetime_format=True, chunksize=CHUNKSIZE):
        if len(app.config['GEOGUIDE_BOUNDARIES']) == 4:
            lat_min, lat_max, lng_min, lng_max = app.config['GEOGUIDE_BOUNDARIES']
            df = df[((lat_min < df[dataset.latitude_attr]) & (df[dataset.latitude_attr] < lat_max)) &
                    ((lng_min < df[dataset.longitude_attr]) & (df[dataset.longitude_attr] < lng_max))]
        else:
            df = df[(df[dataset.latitude_attr] != 0) & (df[dataset.longitude_attr] != 0)]
        df.to_csv(csv_path, index_label='id', header=is_first, mode='a')
        if is_first:
            store.put('data', df, format='table')
        else:
            print(df.columns)
            store.append('data', df)
        is_first = False

    store.close()
    os.remove(original_csv_path)
    shutil.move(csv_path, original_csv_path)

    Thread(target=lambda: index_dataset(dataset)).start()


def index_dataset(dataset):
    with app.app_context():
        hdf_path = path_to_hdf(dataset)
        tmp_hdf_path = '{}.tmp'.format(hdf_path)

        ds_datetimes = {}
        ds_numerics = {}

        store = pd.HDFStore(hdf_path)
        df = store.select('data')


        datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
        len_datetime_columns = len(datetime_columns)
        numeric_columns = list(df.select_dtypes(include=[np.number]).columns)
        numeric_columns = [c for c in numeric_columns if 'latitude' not in c and 'longitude' not in c and not df[c].isnull().any()]
        df = df.loc[:, [dataset.latitude_attr, dataset.longitude_attr, *numeric_columns, *datetime_columns]]
        greatest_distance = 0
        greatest_similarity = 0

        x, x_chunk, next_chunk = 1, 1, CHUNKSIZE
        n_rows = store.get_storer('data').nrows
        ds = []
        tmp_store = pd.HDFStore(tmp_hdf_path)
        for row_a in df.itertuples():
            print('Current:', x)
            if row_a[1] == 0 or row_a[2] == 0:
                x += 1
                continue
            if row_a[0] not in ds_datetimes:
                ds_datetimes[row_a[0]] = list(chain.from_iterable([[d.hour, d.minute, d.weekday()] for d in row_a[-len_datetime_columns:]]))
            if row_a[0] not in ds_numerics:
                ds_numerics[row_a[0]] = row_a[3:-len_datetime_columns]
            for row_b in df.iloc[x:].itertuples():
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
            x_chunk += n_rows - x
            if x_chunk > next_chunk:
                tmp_store.append('relation/pure', pd.DataFrame(
                    ds, columns=['id_a', 'id_b', 'similarity', 'distance']
                ))
                next_chunk += CHUNKSIZE
                ds = []

        if ds:
            tmp_store.append('relation/pure', pd.DataFrame(
                ds, columns=['id_a', 'id_b', 'similarity', 'distance']
            ))

        for dfr in tmp_store.select('relation/pure', chunksize=CHUNKSIZE):
            dfr = dfr.assign(
                similarity=lambda x: x.similarity / greatest_similarity,
                distance=lambda x: x.distance / greatest_distance
            )
            store.append('relation', dfr)

        tmp_store.close()
        store.close()

        os.remove(tmp_hdf_path)

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
