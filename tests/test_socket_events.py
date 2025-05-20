import pytest
from datetime import datetime

from app.db import init_db
from app.models import User, PointsLedger
from app.socket_events import init_socket_events


class DummySocketIO:
    def __init__(self):
        self.handlers = {}
        self.started = False
        self.emits = []

    def on(self, name):
        def decorator(func):
            self.handlers[name] = func
            return func
        return decorator

    def start_background_task(self, target):
        self.started = True
        self.task = target

    def emit(self, event, data, room=None):
        self.emits.append((event, data, room))

    def sleep(self, sec):
        raise StopIteration


def test_init_socket_events(monkeypatch):
    Session = init_db('sqlite:///:memory:')
    session = Session()
    user1 = User(username='alice')
    user2 = User(username='bob')
    session.add_all([user1, user2])
    session.commit()
    session.add_all([
        PointsLedger(user_id=user1.id, points_delta=10, reason='test', timestamp=datetime.utcnow()),
        PointsLedger(user_id=user2.id, points_delta=5, reason='test', timestamp=datetime.utcnow()),
    ])
    session.commit()
    session.close()

    socketio = DummySocketIO()
    rooms = []
    monkeypatch.setattr('app.socket_events.join_room', lambda room: rooms.append(room))

    loop = init_socket_events(None, Session, socketio)

    assert 'connect' in socketio.handlers
    socketio.handlers['connect']()
    assert rooms == ['public']
    assert socketio.started is True

    with pytest.raises(StopIteration):
        loop()

    assert socketio.emits
    event, data, room = socketio.emits[0]
    assert event == 'leaderboard'
    assert room == 'public'
    assert data[0]['name'] == 'alice'
    assert data[0]['points'] == 10
