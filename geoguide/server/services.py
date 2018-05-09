from flask_login import current_user
from geoguide.server.models import Session, Polygon
from sqlalchemy import desc


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
