from __future__ import annotations

from typing import Any, Callable

from flask_socketio import join_room

from .models import User, get_total_points


def init_socket_events(app, session_factory: Callable[[], Any] | None, socketio=None):
    """Register socket events and start background jobs."""
    if socketio is None or session_factory is None:
        return None

    @socketio.on("connect")
    def on_connect():
        join_room("public")

    def leaderboard_loop():
        while True:
            session = session_factory()
            try:
                users = session.query(User).all()
                board = [
                    {"name": user.username, "points": get_total_points(session, user.id)}
                    for user in users
                ]
                board.sort(key=lambda x: x["points"], reverse=True)
                socketio.emit("leaderboard", board[:10], room="public")
            finally:
                session.close()
            socketio.sleep(15)

    socketio.start_background_task(leaderboard_loop)
    return leaderboard_loop
