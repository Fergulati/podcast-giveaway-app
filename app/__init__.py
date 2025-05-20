from flask import Flask

try:
    from .db import init_db
except Exception:
    init_db = None  # type: ignore

try:
    from flask_socketio import SocketIO
except Exception:
    SocketIO = None  # type: ignore

try:
    from .tasks import init_scheduler
except Exception:
    init_scheduler = None  # type: ignore

try:
    from .socket_events import init_socket_events
except Exception:
    init_socket_events = None  # type: ignore


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_mapping(SECRET_KEY='dev')

    from . import routes
    routes.init_app(app)

    session_factory = None
    if init_db:
        try:
            session_factory = init_db()
        except Exception as exc:  # pragma: no cover - optional dependency
            app.logger.warning("Database unavailable: %s", exc)

    socketio = None
    if SocketIO:
        socketio = SocketIO(app)
        if init_scheduler and session_factory is not None:
            try:
                init_scheduler(app, session_factory, socketio)
            except Exception as exc:  # pragma: no cover
                app.logger.warning("Scheduler failed: %s", exc)
        if init_socket_events and session_factory is not None:
            try:
                init_socket_events(app, session_factory, socketio)
            except Exception as exc:  # pragma: no cover
                app.logger.warning("Socket events failed: %s", exc)

    app.session_factory = session_factory
    app.socketio = socketio

    return app
