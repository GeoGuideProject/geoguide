
import datetime
import math
import pandas as pd
import numpy as np
import os
import shutil
from itertools import chain
from geoguide.server import app, db, datasets
from geoguide.server.models import Dataset, Attribute, AttributeType
from geoguide.server.similarity import cosine_similarity_with_nan as cosine_similarity, jaccard_similarity, fuzz_similarity
from threading import Thread

CHUNKSIZE = app.config['CHUNKSIZE']
DEBUG = app.config['DEBUG']


def path_to_hdf(dataset):
    return '{}.h5'.format(datasets.path(dataset.filename).rsplit('.', 1)[0])


def is_latlng_attribute(header):
    return 'latitude' in header or 'longitude' in header


def guess_attributes_types(dataset):
    df = pd.read_hdf(path_to_hdf(dataset), 'data')
    numberic_attributes = list(df.select_dtypes(include=[np.number]).columns)
    string_attributes = list(df.select_dtypes(include=[object]).columns)

    number_attributes = [c for c in numberic_attributes if not is_latlng_attribute(c) and 'id' not in c and df[c].unique().shape[0] > 3]

    categorical_number_attributes = [c for c in numberic_attributes if not is_latlng_attribute(c) and 'id' not in c and df[c].unique().shape[0] <= 3]

    categorical_text_attributes = [c for c in string_attributes if df[c].unique().shape[0] <= 10]

    text_attributes = [c for c in string_attributes if c not in categorical_text_attributes]

    for attr in number_attributes:
        attribute = Attribute(attr, AttributeType.number, dataset.id)
        db.session.add(attribute)

    for attr in categorical_number_attributes:
        attribute = Attribute(attr, AttributeType.categorical_number, dataset.id)
        db.session.add(attribute)

    for attr in categorical_text_attributes:
        attribute = Attribute(attr, AttributeType.categorical_text, dataset.id)
        db.session.add(attribute)

    for attr in text_attributes:
        attribute = Attribute(attr, AttributeType.text, dataset.id)
        db.session.add(attribute)

    db.session.commit()


def save_as_hdf(dataset):
    dataset_id = dataset.id
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
        df.to_csv(csv_path, index_label='geoguide_id', header=is_first, mode='a')
        if is_first:
            store.put('data', df, format='table')
        else:
            store.append('data', df)
        is_first = False

    store.close()
    os.remove(original_csv_path)
    shutil.move(csv_path, original_csv_path)

    guess_attributes_types(dataset)

    Thread(target=lambda: index_dataset(dataset_id)).start()


def index_dataset(dataset_id):
    with app.app_context():
        dataset = Dataset.query.get(dataset_id)
        hdf_path = path_to_hdf(dataset)
        tmp_hdf_path = '{}.tmp'.format(hdf_path)
        ds_datetimes = {}

        def handle_ds_datetimes(ds, row, left_limit, right_limit):
            key = row[0]
            if key not in ds:
                ds[key] = list(chain.from_iterable([[d.hour, d.minute, d.weekday()] for d in row[left_limit:right_limit]])) if right_limit > left_limit else []
            return ds

        store = pd.HDFStore(hdf_path)
        df = store.select('data')

        datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
        number_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.number]
        text_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.text]
        cat_number_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.categorical_number]
        cat_text_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.categorical_text]

        datetime_columns_limits = 3, 3 + len(datetime_columns)
        number_columns_limits = datetime_columns_limits[1], datetime_columns_limits[1] + len(number_columns)
        text_columns_limits = number_columns_limits[1], number_columns_limits[1] + len(text_columns)
        cat_number_columns_limits = text_columns_limits[1], text_columns_limits[1] + len(cat_number_columns)
        cat_text_columns_limits = cat_number_columns_limits[1], cat_number_columns_limits[1] + len(cat_text_columns)

        df = df.loc[:, [dataset.latitude_attr, dataset.longitude_attr, *datetime_columns, *number_columns, *text_columns, *cat_number_columns, *cat_text_columns]]
        greatest_distance = 0
        greatest_similarity = 0

        x, x_chunk, next_chunk = 1, 1, CHUNKSIZE
        n_rows = store.get_storer('data').nrows
        ds = []
        tmp_store = pd.HDFStore(tmp_hdf_path)
        for row_a in df.itertuples():
            ds_datetimes = handle_ds_datetimes(ds_datetimes, row_a, *datetime_columns_limits)

            a_datetimes = ds_datetimes[row_a[0]]
            a_numbers = row_a[number_columns_limits[0]:number_columns_limits[1]]
            a_texts = row_a[text_columns_limits[0]:text_columns_limits[1]]
            a_cat_numbers = row_a[cat_number_columns_limits[0]:cat_number_columns_limits[1]]
            a_cat_texts = row_a[cat_text_columns_limits[0]:cat_text_columns_limits[1]]

            if DEBUG:
                print('%f/%f'.format(row_a[0], n_rows))

            for row_b in df.iloc[x:].itertuples():
                ds_datetimes = handle_ds_datetimes(ds_datetimes, row_b, *datetime_columns_limits)

                b_datetimes = ds_datetimes[row_b[0]]
                b_numbers = row_b[number_columns_limits[0]:number_columns_limits[1]]
                b_texts = row_b[text_columns_limits[0]:text_columns_limits[1]]
                b_cat_numbers = row_b[cat_number_columns_limits[0]:cat_number_columns_limits[1]]
                b_cat_texts = row_b[cat_text_columns_limits[0]:cat_text_columns_limits[1]]

                distance = harvestine_distance(row_a[1], row_a[2],
                                               row_b[1], row_b[2])

                i = cosine_similarity(a_datetimes, b_datetimes) * 1
                ii = cosine_similarity(a_numbers, b_numbers) * 2
                iii = fuzz_similarity(a_texts, b_texts) * 1
                iv = cosine_similarity(a_cat_numbers, b_cat_numbers) * 2
                v = jaccard_similarity(a_cat_texts, b_cat_texts) * 1
                similarity = i + ii + iii + iv + v

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
            store.append('relation', dfr, data_columns=True)

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
