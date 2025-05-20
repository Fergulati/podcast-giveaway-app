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


def test_duplicate_engagement_id(session):
    user = User(username="bob")
    session.add(user)
    session.commit()

    e1 = Engagement(
        user_id=user.id,
        event_type=EventType.COMMENT,
        event_id="dup",
        timestamp=datetime.utcnow(),
    )
    e2 = Engagement(
        user_id=user.id,
        event_type=EventType.COMMENT,
        event_id="dup",
        timestamp=datetime.utcnow(),
    )
    session.add_all([e1, e2])
    session.commit()

    app = Flask(__name__)
    app.config["POINT_MATRIX"] = {"COMMENT": 2}
    with app.app_context():
        first_total = apply_points(user, e1)
        second_total = apply_points(user, e2)

    assert first_total == 2
    assert second_total == 4
    assert session.query(PointsLedger).count() == 2
    assert get_total_points(session, user.id) == 4


def test_matrix_change_immutability(session):
    user = User(username="carol")
    session.add(user)
    session.commit()

    e1 = Engagement(
        user_id=user.id,
        event_type=EventType.COMMENT,
        event_id="e1",
        timestamp=datetime.utcnow(),
    )
    e2 = Engagement(
        user_id=user.id,
        event_type=EventType.COMMENT,
        event_id="e2",
        timestamp=datetime.utcnow(),
    )
    session.add_all([e1, e2])
    session.commit()

    app = Flask(__name__)
    app.config["POINT_MATRIX"] = {"COMMENT": 5}
    with app.app_context():
        total_first = apply_points(user, e1)

    assert total_first == 5
    row = session.query(PointsLedger).filter_by(engagement_id=e1.id).one()
    assert row.points_delta == 5

    app.config["POINT_MATRIX"] = {"COMMENT": 1}
    with app.app_context():
        total_second = apply_points(user, e2)

    assert total_second == 6
    row_first = session.query(PointsLedger).filter_by(engagement_id=e1.id).one()
    assert row_first.points_delta == 5
    assert session.query(PointsLedger).count() == 2
    assert get_total_points(session, user.id) == 6


def test_superchat_multiplier(session):
    user = User(username="dave")
    session.add(user)
    session.commit()

    engagement = Engagement(
        user_id=user.id,
        event_type=EventType.SUPERCHAT,
        event_id="s1",
        timestamp=datetime.utcnow(),
        raw_json="{\"amount\": 4}",
    )
    session.add(engagement)
    session.commit()

    def _multiplier(e):
        import json

        return json.loads(e.raw_json)["amount"] * 10

    app = Flask(__name__)
    app.config["POINT_MATRIX"] = {"SUPERCHAT": _multiplier}
    with app.app_context():
        total = apply_points(user, engagement)

    assert total == 40
    row = session.query(PointsLedger).filter_by(engagement_id=engagement.id).one()
    assert row.points_delta == 40
