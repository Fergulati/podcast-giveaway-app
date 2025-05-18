from flask import Blueprint, render_template, request, redirect, url_for, session
import os
import requests

bp = Blueprint('main', __name__)


# Read API key from environment, if provided
API_KEY = os.environ.get('YOUTUBE_API_KEY')

CHANNEL_IDS = [
    # Example channel IDs can be added here
    'UC_x5XG1OV2P6uZZ5FSM9Ttw',  # Google Developers
]


def init_app(app):
    app.register_blueprint(bp)


@bp.route('/')
def index():
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    channels = get_channel_data()
    return render_template('channels.html', username=username, channels=channels)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('main.index'))
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


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
