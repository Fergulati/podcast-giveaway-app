import pytest
from app import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({'TESTING': True, 'SECRET_KEY': 'test'})
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_login(client):
    res = client.get('/login')
    assert res.status_code == 200
    res = client.post('/login', data={'username': 'tester'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome tester' in res.data
