from flask_login import current_user
from geoguide.server.models import Session
from sqlalchemy import desc


def current_session():
    session = Session.query.filter_by(
        user_id=current_user.id
    ).order_by(
        desc(Session.created_at)
    ).first()

    return session
