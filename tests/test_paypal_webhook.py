import json
import hmac
import hashlib

import pytest

from app import create_app
from app.db import init_db
from app.models import GiveawayWinner


@pytest.fixture()
def app_and_session():
    Session = init_db('sqlite:///:memory:')
    app = create_app()
    app.session_factory = Session
    app.config.update({'TESTING': True, 'PAYPAL_WEBHOOK_SECRET': 'secret'})
    return app, Session


def test_payout_completed_marks_paid(app_and_session):
    app, Session = app_and_session
    session = Session()
    gw = GiveawayWinner(payout_item_id='p1')
    session.add(gw)
    session.commit()
    session.close()

    client = app.test_client()
    event = {
        'event_type': 'PAYOUTS-ITEM.COMPLETED',
        'resource': {'payout_item_id': 'p1'},
    }
    body = json.dumps(event).encode()
    sig = hmac.new(b'secret', body, hashlib.sha256).hexdigest()
    res = client.post(
        '/webhooks/paypal',
        data=body,
        headers={'PayPal-Transmission-Sig': sig},
        content_type='application/json',
    )
    assert res.status_code == 204

    session = Session()
    row = session.query(GiveawayWinner).filter_by(payout_item_id='p1').one()
    assert row.paid is True
    session.close()
