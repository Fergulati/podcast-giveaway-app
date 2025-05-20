import pytest
from datetime import datetime
from flask import Flask

from app.db import init_db
from app.models import User, Engagement, EventType, PointsLedger, get_total_points
from app.utils.points import apply_points


@pytest.fixture()
def session():
    Session = init_db('sqlite:///:memory:')
    sess = Session()
    yield sess
    sess.close()


def test_apply_points(session):
    user = User(username='alice')
    session.add(user)
    session.commit()

    engagement = Engagement(
        user_id=user.id,
        event_type=EventType.COMMENT,
        event_id='e1',
        timestamp=datetime.utcnow(),
    )
    session.add(engagement)
    session.commit()

    app = Flask(__name__)
    app.config['POINT_MATRIX'] = {'COMMENT': 3}
    with app.app_context():
        total = apply_points(user, engagement)

    assert total == 3
    assert session.query(PointsLedger).count() == 1
    assert get_total_points(session, user.id) == 3
