from collections import defaultdict, Counter

import pandas as pd

from flask_login import current_user
from sqlalchemy import desc
from tabulate import tabulate
from sqlalchemy import create_engine

from geoguide.server import app, logging
from geoguide.server.models import Dataset, Session, Polygon, AttributeType


SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']


def current_session():
    # TODO: improve to support multiple sessions in different
    # computers at the same time
    session = Session.query.filter_by(
        user_id=current_user.id
    ).order_by(
        desc(Session.created_at)
    ).first()

    return session


def get_session_by_id(id):
    session = Session.query.get(id)
    return session


def get_dataset_by_id(id):
    dataset = Dataset.query.get(id)
    return dataset


def get_polygon_by_id(id):
    polygon = Polygon.query.get(id)
    return polygon


def get_next_polygon_and_idr_iteration():
    latest = Polygon.query.filter_by(
        session_id=current_session().id
    ).order_by(
        desc(Polygon.created_at)
    ).first()

    if latest is None:
        return 1

    return latest.iteration + 1


def get_points_id_in_polygon(dataset, polygon):
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    table_name = 'datasets.' + dataset.filename.rsplit('.', 1)[0]

    query ='''
    SELECT d.geoguide_id
    FROM "{}" AS d
    JOIN polygons AS p ON ST_Contains(p.geom, d.geom)
    WHERE p.id = {}
    '''.format(table_name, polygon.id)

    cursor = engine.execute(query)

    return [r[0] for r in cursor]


def create_polygon_profile(polygon_id):
    if polygon_id is None:
        raise ValueError("polygon_id should not be None")

    polygon = get_polygon_by_id(polygon_id)
    session = get_session_by_id(polygon.session_id)
    dataset = get_dataset_by_id(session.dataset_id)

    # numbers
    number_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.number]

    # texts
    text_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.text]

    # categorial
    # TODO: incremental per session
    cat_number_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.categorical_number]
    cat_text_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.categorical_text]

    # datetimes
    datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]

    with app.app_context():
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        table_name = 'datasets.' + dataset.filename.rsplit('.', 1)[0]

        df = pd.read_sql_table(table_name, engine, index_col='geoguide_id')
        df = df.loc[[*get_points_id_in_polygon(dataset, polygon)], :]

        # numbers
        numbers_summary = []
        for col in number_columns:
            numbers_summary.append(dict(attribute=col, **df[col].describe().to_dict()))
        logging.info('\n' + tabulate(numbers_summary, headers="keys", tablefmt="grid"))

        # texts
        rank = defaultdict(Counter)
        for col in text_columns:
            for _, value in df[col].str.lower().str.split(" ").items():
                if value is None:
                    continue
                for v in value:
                    if len(v) < 3:
                        continue
                    rank[col][v] += 1
            logging.info(col + ': \n' + tabulate(rank[col].most_common(10), headers=["term", "counter"], tablefmt="grid"))

        # categorical
        cat_map = defaultdict(int)
        for col in cat_number_columns + cat_text_columns:
            for _, value in df[col].items():
                if pd.isnull(value):
                    continue
                cat_map["<{}, {}>".format(col, str(value))] += 1
        logging.info('\n' + tabulate(cat_map.items(), headers=["category", "counter"], tablefmt="grid"))

        # datetimes
        # TODO
