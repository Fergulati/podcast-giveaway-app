from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    current_app,
)
from types import SimpleNamespace


from .models import User, get_total_points
try:
    from flask_dance.contrib.google import google
except Exception:  # pragma: no cover - optional dependency
    google = None  # type: ignore
import json
import os
import pathlib
import requests
from .utils.quiz import generate_question, load_transcript

bp = Blueprint('main', __name__)


# Read API key from environment, if provided
API_KEY = os.environ.get('YOUTUBE_API_KEY')

CHANNEL_IDS = [

    'UCZY97wqlKHsx2qFibsMLLtg',
    'UCAI6Gk0R_1aGa76ShKFA78Q',
    'UCJfeceoPn3MSpdNM3n-DIWg',
]

TRANSCRIPTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)


def init_app(app):
    app.register_blueprint(bp)


@bp.route('/')
def index():
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    channels = get_channel_data()
    return render_template('channels.html', username=username, channels=channels)


@bp.route('/channel/<cid>')
def watch_channel(cid):
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    channels = get_channel_data()
    channel = next((c for c in channels if c['id'] == cid), None)
    if channel is None:
        return redirect(url_for('main.index'))
    return render_template('watch.html', username=username, channel=channel)


@bp.route('/api/upload_transcript/<cid>', methods=['POST'])
def upload_transcript(cid):
    """Store transcript text for a channel."""
    text = request.get_data(as_text=True)
    if not text:
        return {"error": "no transcript"}, 400
    path = TRANSCRIPTS_DIR / f"{cid}.txt"
    path.write_text(text, encoding="utf-8")
    return {"status": "ok"}


@bp.route('/api/quiz/<cid>')
def quiz_question(cid):
    """Return a generated quiz question for the channel."""
    path = TRANSCRIPTS_DIR / f"{cid}.txt"
    if not path.exists():
        return {"question": "Transcript not found", "options": []}
    transcript = load_transcript(str(path))
    return generate_question(transcript)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':

        username = request.form['username'].strip()
        if not username:
            error = 'Username required'
        else:
            session['username'] = username
            session['role'] = (
                'ROLE_ADMIN' if username == 'admin' else 'ROLE_USER'
            )
            return redirect(url_for('main.index'))
    return render_template('login.html', username=None, error=error)



@bp.route('/oauth-login')
def oauth_login():
    if google is None:
        return redirect(url_for('main.login'))
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/oauth2/v2/userinfo')

    if not resp.ok:

        return redirect(url_for('main.login'))
    info = resp.json()
    username = info.get('name') or info.get('email')
    session['username'] = username

    session['role'] = 'ROLE_USER'
    token = google.blueprint.token
    session_factory = getattr(current_app, 'session_factory', None)
    if session_factory is not None:
        db_session = session_factory()
        try:
            user = db_session.query(User).filter_by(username=username).first()
            if user is None:
                user = User(username=username)
                db_session.add(user)
                db_session.commit()

            from .models import OAuth

            oauth = (
                db_session.query(OAuth)
                .filter_by(provider='youtube', user_id=user.id)
                .first()
            )

            token_json = json.dumps(token)
            if oauth:
                oauth.token = token_json
            else:
                oauth = OAuth(
                    provider='youtube', token=token_json, user_id=user.id
                )
                db_session.add(oauth)
            db_session.commit()
        finally:
            db_session.close()
    return redirect(url_for('main.dashboard'))


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


@bp.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))

    points_total = 0
    user_id = None
    session_factory = getattr(current_app, 'session_factory', None)
    if session_factory is not None:
        db_session = session_factory()
        try:
            user = db_session.query(User).filter_by(username=username).first()
            if user is None:
                user = User(username=username)
                db_session.add(user)
                db_session.commit()
            user_id = user.id
            points_total = get_total_points(db_session, user.id)
        finally:
            db_session.close()

    current_user = SimpleNamespace(id=user_id, username=username, points_total=points_total)
    return render_template('dashboard.html', current_user=current_user, username=username)


def get_channel_data():
    if not API_KEY:
        # Without an API key, return simple channel URLs
        return [
            {
                'id': cid,
                'title': f'Channel {cid}',
                'url': f'https://www.youtube.com/channel/{cid}',
            }
            for cid in CHANNEL_IDS
        ]
    data = []
    for cid in CHANNEL_IDS:
        resp = requests.get(
            'https://www.googleapis.com/youtube/v3/channels',
            params={'part': 'snippet', 'id': cid, 'key': API_KEY},
            timeout=10,
        )
        if resp.ok:
            items = resp.json().get('items')
            if items:
                snippet = items[0]['snippet']
                data.append(
                    {
                        'id': cid,
                        'title': snippet['title'],
                        'url': f'https://www.youtube.com/channel/{cid}',
                    }
                )
    return data
