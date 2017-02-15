import pandas as pd
import math
import arrow


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
    except:
        return 0

df = pd.read_csv('tmp/arquivo.csv')

df = df[((40.495730 < df['start station latitude']) & (df['start station latitude'] < 40.915031)) &
        ((40.495730 < df['end station latitude']) & (df['end station latitude'] < 40.915031)) &
        ((-74.255698 < df['end station longitude']) & (df['end station longitude'] < -73.700208)) &
        ((-74.255698 < df['start station longitude']) & (df['start station longitude'] < -73.700208))]

df['starttime'] = df['starttime'].apply(
    lambda x: arrow.get(x, 'M/D/YYYY HH:mm:ss').isoformat())
df['stoptime'] = df['stoptime'].apply(
    lambda x: arrow.get(x, 'M/D/YYYY HH:mm:ss').isoformat())

df_ends = df.copy()

df = df.loc[:, ['start station latitude',
                'start station longitude',
                'starttime',
                'tripduration']]

df_ends = df_ends.loc[:, ['end station latitude',
                          'end station longitude',
                          'stoptime',
                          'tripduration']]

df = df.rename(columns={
    'start station latitude': 'latitude',
    'start station longitude': 'longitude',
    'starttime': 'datetime',
    'tripduration': 'duration'
}).assign(is_pickup=1)

df_ends = df_ends.rename(columns={
    'end station latitude': 'latitude',
    'end station longitude': 'longitude',
    'stoptime': 'datetime',
    'tripduration': 'duration'
}).assign(is_pickup=0)

df = df.append(df_ends, ignore_index=True)

del df_ends

# df.to_csv('pandas.index.csv', index_label='id')
df.to_hdf('pandas.store.h5', 'index', format='fixed')

bigger_distance = 0

ds = []
df_aux = df.copy()
x = 1
n = len(df)

for row_a in df.itertuples():
    # print('Left:', n - x)
    for row_b in df_aux.loc[x:].itertuples():
        distance = harvestine_distance(row_a[1], row_a[2],
                                       row_b[1], row_b[2])
        ds.append((row_a[0], row_b[0], distance, distance))
        if distance > bigger_distance:
            bigger_distance = distance
    x += 1

del df_aux

df_ds = pd.DataFrame(
    ds, columns=['id_a', 'id_b', 'distance', 'similarity']
).assign(
    distance=lambda x: x.distance / bigger_distance,
    similarity=lambda x: x.similarity / bigger_distance
)

# df_ds.to_csv('pandas.ds.csv', index=False)
df_ds.to_hdf('pandas.store.h5', 'ds', format='fixed')
