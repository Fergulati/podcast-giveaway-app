import os
from app import create_app


def test_quiz_generation(tmp_path):
    app = create_app()
    app.config.update({'TESTING': True})
    from app import routes
    routes.TRANSCRIPTS_DIR = tmp_path
    client = app.test_client()
    cid = 'test123'

    # Upload transcript
    transcript = 'This is a sample transcript for testing purposes.'
    res = client.post(f'/api/upload_transcript/{cid}', data=transcript)
    assert res.status_code == 200

    # Request quiz question
    res = client.get(f'/api/quiz/{cid}')
    assert res.status_code == 200
    data = res.get_json()
    assert 'question' in data
    assert 'options' in data
    assert isinstance(data['options'], list)
