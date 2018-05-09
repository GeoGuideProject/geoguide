from flask_login import current_user
from geoguide.server.models import Session, Polygon, IDR
from sqlalchemy import desc
from geoguide.server.geoguide.helpers import haversine_distance


def current_session():
    # TODO: improve to support multiple sessions in different
    # computers at the same time
    session = Session.query.filter_by(
        user_id=current_user.id
    ).order_by(
        desc(Session.created_at)
    ).first()

    return session


def get_next_polygon_and_idr_iteration():
    latest = Polygon.query.filter_by(
        session_id=current_session().id
    ).order_by(
        desc(Polygon.created_at)
    ).first()

    if latest is None:
        return 1

    return latest.iteration + 1


def get_polygons_count(session):
    return Polygon.query.filter_by(
        session_id=session.id
    ).count()


def get_idrs_count(session):
    return IDR.query.filter_by(
        session_id=session.id
    ).count()


def filter_dataset(file):
    import pandas as pd
    LAT = 48.8583736
    LNG = 2.2922873

    df = pd.read_csv(file)
    df['distance'] = df.apply(lambda r: haversine_distance(float(r.latitude), float(r.longitude), LAT, LNG))
    df = df.sort_values('distance', ascending=False)
    df.to_csv('/project/airbnb-tower.csv')
