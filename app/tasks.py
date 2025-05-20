from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from .models import EventType, Engagement, OAuth, User, get_total_points
from .utils.points import apply_points, DEFAULT_POINT_MATRIX


# Default mapping for tasks when no Flask config is available
RULES = DEFAULT_POINT_MATRIX


def init_scheduler(app, session_factory, socketio=None):
    """Initialize APScheduler job if dependencies are available."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except Exception as exc:  # pragma: no cover - optional dependency
        app.logger.warning("APScheduler not available: %s", exc)
        return None

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: _update_engagements(app, session_factory, socketio),
        "interval",
        seconds=60,
    )
    scheduler.start()
    return scheduler


def _build_youtube_service(token: dict):
    """Create a YouTube service from a stored OAuth token."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except Exception:
        return None
    creds = Credentials(token.get("access_token"))
    return build("youtube", "v3", credentials=creds)


def _fetch_activities(service) -> list:
    try:
        resp = (
            service.activities()
            .list(part="snippet,contentDetails", mine=True)
            .execute()
        )
    except Exception:
        return []
    return resp.get("items", [])


def _update_engagements(app, session_factory, socketio=None):
    if session_factory is None:
        return
    session = session_factory()
    try:
        oauth_rows = (
            session.query(OAuth).filter(OAuth.provider == "youtube").all()
        )
        for oauth in oauth_rows:
            try:
                token = json.loads(oauth.token)
            except Exception:
                continue
            service = _build_youtube_service(token)
            if service is None:
                continue
            # Verify subscription still active
            try:
                service.subscriptions().list(part="id", mine=True).execute()
            except Exception:
                continue
            # Pull activities
            activities = _fetch_activities(service)
            for item in activities:
                event_id = item.get("id")
                if not event_id:
                    continue
                if (
                    session.query(Engagement)
                    .filter_by(event_id=event_id, user_id=oauth.user_id)
                    .first()
                ):
                    continue
                etype = item.get("snippet", {}).get("type", "").upper()
                if etype not in RULES:
                    continue
                engagement = Engagement(
                    user_id=oauth.user_id,
                    event_type=EventType[etype],
                    event_id=event_id,
                    timestamp=datetime.utcnow(),
                    raw_json=json.dumps(item),
                )
                session.add(engagement)
                session.flush()
                apply_points(oauth.user, engagement)
            session.commit()
            total = get_total_points(session, oauth.user_id)
            if socketio is not None:
                socketio.emit(
                    "points_update", {"user_id": oauth.user_id, "total": total}
                )
    finally:
        session.close()
