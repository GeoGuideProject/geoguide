import time
import pandas as pd
import datetime
from collections import defaultdict
from random import randint
from geoguide.server import app, diversity, logging
from geoguide.server.services import current_session
from geoguide.server.geoguide.helpers import path_to_hdf, haversine_distance
from statistics import mean
from sqlalchemy import create_engine

CHUNKSIZE = app.config['CHUNKSIZE']
DEBUG = app.config['DEBUG']
USE_SQL = app.config['USE_SQL']
SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']


def get_proximities_of(elements, k, proximity_by_id):
    return [proximity_by_id[elements[i]] for i in range(k)]


def get_distances_of(elements, k, distance_by_id):
    my_distances = [distance_by_id[elements[i]] for i in range(k)]
    return my_distances


def make_new_records(elements, new_element, k, records):
    output = {}
    for i in range(k):
        output[i] = elements[i]
    replacement = randint(0, k - 1)
    output[replacement] = records[new_element]
    return output


def read_input_from_hdf(dataset, input_g, filtered_points=[], clusters=[]):
    similarities = {}
    distances = {}
    proximities = {}

    store = pd.HDFStore(path_to_hdf(dataset))
    for df in store.select('data', chunksize=CHUNKSIZE):
        if filtered_points:
            df = df[df.index.isin(filtered_points)]
        df = df.loc[:, [dataset.latitude_attr, dataset.longitude_attr]]
        for row in df.itertuples():
            key = row[0]
            for cluster in clusters:
                if cluster and cluster[2] == 0:
                    continue
                proximity = haversine_distance(*cluster[:2], *row[1:])
                if DEBUG:
                     print(proximity, cluster[2], proximity/cluster[2])
                proximity = proximity / cluster[2]
                proximities[key] = min([proximity, proximities.get(key, proximity)])

    for df in store.select('relation', chunksize=CHUNKSIZE, where='id_a=input_g or id_b=input_g'):
        if filtered_points:
            df = df[((df['id_a'].isin(filtered_points)) & (df['id_b'].isin(filtered_points)))]
        for row in df.itertuples():
            id_a = int(row[1])
            id_b = int(row[2])
            if id_a == id_b:
                continue
            key = id_a if id_b == input_g else id_b
            similarities[key] = float(row[3])
            distances[key] = float(row[4])
    store.close()

    return similarities, distances, proximities


def read_input_from_sql(dataset, input_g, filtered_points=[], clusters=[]):
    similarities = {}
    distances = {}
    idr_scores = {}

    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    table_name = 'datasets.' + dataset.filename.rsplit('.', 1)[0]
    table_rel_name = '{}-rel'.format(table_name)

    idr_score_query = '''
    select idr.geoguide_id, (count_idr + count_polygon) as score
    from (
        select d.geoguide_id, COUNT(r.id) as count_idr
        from "{table_name}" as d
        left join idrs as r on (st_contains(r.geom, d.geom)) and r.session_id = {session_id}
        group by d.geoguide_id
        order by count_idr desc, d.geoguide_id
    ) as idr join (
        select d.geoguide_id, COUNT(r.id) as count_polygon
        from "{table_name}" as d
        left join polygons as r on (st_contains(r.geom, d.geom)) and r.session_id = {session_id}
        group by d.geoguide_id
        order by count_polygon desc, d.geoguide_id
    ) as polygon on idr.geoguide_id = polygon.geoguide_id
    order by score desc, geoguide_id
    '''.format(
        table_name=table_name,
        session_id=current_session().id
    )

    cursor = engine.execute(idr_score_query)
    for row in cursor:
        geoguide_id, score = row
        if filtered_points and geoguide_id in filtered_points:
            continue
        idr_scores[geoguide_id] = score

    for df in pd.read_sql_table(table_rel_name, engine, index_col='index', chunksize=CHUNKSIZE):
        df = df[((df['id_a'] == input_g) | (df['id_b'] == input_g))]
        if filtered_points:
            df = df[((df['id_a'].isin(filtered_points)) & (df['id_b'].isin(filtered_points)))]
        for row in df.itertuples():
            id_a = int(row[1])
            id_b = int(row[2])
            if id_a == id_b:
                continue
            key = id_a if id_b == input_g else id_b
            similarities[key] = float(row[3])
            distances[key] = float(row[4])

    return similarities, distances, idr_scores


def run_iuga(input_g, k_value, time_limit, lowest_acceptable_similarity, dataset, *args, **kwargs):
    # parameters
    k = k_value

    filtered_points = kwargs.get('filtered_points', [])
    clusters = kwargs.get('clusters', [])

    # indexing file
    # should the algorithm stop if it reaches the end of the index (i.e.,
    # scanning all records once)
    STOP_VISITING_ONCE = False

    # Note that in case of user group analysis, each group is a record. In
    # case of spatiotemporal data, each geo point is a record.

    # variables
    # the ID of current k records will be recorded in this object.
    current_records = {}

    # ths ID of next potential k records will be recorded in this object.
    new_records = {}

    # total execution time
    total_time = 0.0

    # read input data frame
    start = time.time()
    if USE_SQL:
        similarities, distances, idr_scores = read_input_from_sql(dataset, input_g, filtered_points, clusters)
    else:
        similarities, distances, proximities = read_input_from_hdf(dataset, input_g, filtered_points, clusters)
    if DEBUG:
        logging.info('[IUGA] {} seconds'.format(time.time() - start))

    # sorting similarities and distances in descending order
    similarities_sorted = sorted(
        similarities.items(), key=lambda x: x[1], reverse=True)
    distances_sorted = sorted(
        distances.items(), key=lambda x: x[1], reverse=True)

    # begin - prepare lists for easy retrieval
    records = {}
    similarity_by_id = defaultdict(float)
    distance_by_id = defaultdict(float)
    idr_score_by_id = defaultdict(float)

    # cnt = 0
    for value in similarities_sorted:
        # records[cnt] = value[0]
        similarity_by_id[value[0]] = value[1]
        # cnt += 1

    for value in distances_sorted:
        distance_by_id[value[0]] = value[1]

    for value in idr_scores.items():
        idr_score_by_id[value[0]] = value[1]

    records_sorted = sorted(
        similarities.items(), key=lambda x: (-idr_score_by_id[x[0]], -x[1])
    )
    print('[records_sorted]', records_sorted)
    cnt = 0
    for key, _ in records_sorted:
        records[cnt] = key
        cnt += 1

    # begin - prepare lists for easy retrieval

    # print(len(records), "records retrieved and indexed.")

    # begin - retrieval functions

    # end - retrieval functions

    # initialization by k most similar records
    for i in range(k):
        current_records[i] = records[i]

    # print("begin:", show(current_records, k, similarity_by_id, distance_by_id))

    # greedy algorithm
    pointer = k - 1
    nb_iterations = 0
    pointer_limit = len(records) - 1
    while total_time < time_limit and pointer < pointer_limit:
        nb_iterations += 1
        pointer += 1
        redundancy_flag = False
        for i in range(k):
            if current_records[i] == records[pointer]:
                redundancy_flag = True
                break
        if redundancy_flag:
            continue
        begin_time = datetime.datetime.now()

        current_distances = get_distances_of(current_records, k, distance_by_id)
        current_diversity = diversity.diversity(current_distances)
        # current_proximities = get_proximities_of(current_records, k, proximity_by_id)
        # current_clustering_mean = mean(current_proximities)

        new_records = make_new_records(current_records, pointer, k, records)

        new_distances = get_distances_of(new_records, k, distance_by_id)
        new_diversity = diversity.diversity(new_distances)
        # new_proximities = get_proximities_of(new_records, k, proximity_by_id)
        # new_clustering_mean = mean(new_proximities)

        if new_diversity > current_diversity:
            if DEBUG:
                print((current_diversity, new_diversity))
            current_records = new_records

        end_time = datetime.datetime.now()
        duration = (end_time - begin_time).microseconds / 1000.0
        total_time += duration
        if similarity_by_id[records[pointer]] < lowest_acceptable_similarity:
            if STOP_VISITING_ONCE:
                break
            else:
                pointer = k

    # print("end:", show(current_records, k, similarity_by_id, distance_by_id))
    # print("execution time (ms)", total_time)
    # print("# iterations", nb_iterations)

    min_similarity = 1
    dicToArray = []
    for i in range(k):
        if similarity_by_id[current_records[i]] < min_similarity:
            min_similarity = similarity_by_id[current_records[i]]
        dicToArray.append(current_records[i])
    my_distances = get_distances_of(current_records, k, distance_by_id)
    my_diversity = diversity.diversity(my_distances)
    return [min_similarity, round(my_diversity, 3), sorted(dicToArray)]
