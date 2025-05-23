from flask import Flask
import os


try:
    from flask_dance.contrib.google import make_google_blueprint, google
except Exception:  # pragma: no cover - optional dependency
    make_google_blueprint = None  # type: ignore
    google = None  # type: ignore


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

# ``make_google_blueprint`` is already imported above together with ``google``.
# Older versions of this module duplicated the import which caused the
# variable to be reassigned and made the intent harder to follow.  The
# duplicate import is no longer needed and has been removed to avoid any
# confusion.

try:
    from .admin.routes import init_admin
except Exception:
    init_admin = None  # type: ignore

try:
    from .socket_events import init_socket_events
except Exception:
    init_socket_events = None  # type: ignore

try:
    from services.paypal_webhook import init_paypal_webhook
except Exception:
    init_paypal_webhook = None  # type: ignore


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_mapping(SECRET_KEY='dev')


    # The Google OAuth blueprint is configured later in this function once we
    # know whether valid credentials are available.  The original implementation
    # registered it unconditionally here which resulted in the blueprint being
    # added twice and caused Flask to raise a `ValueError` about the name
    # "google" already being registered.  Removing the early registration keeps
    # the blueprint setup in a single place.

    from . import routes
    routes.init_app(app)
    if init_paypal_webhook:
        try:
            init_paypal_webhook(app)
        except Exception as exc:  # pragma: no cover - optional dependency
            app.logger.warning("PayPal webhook init failed: %s", exc)

    session_factory = None
    if init_db:
        try:
            session_factory = init_db()
        except Exception as exc:  # pragma: no cover - optional dependency
            app.logger.warning("Database unavailable: %s", exc)

    google_bp = None
    if make_google_blueprint is not None:
        cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        if cid and secret:
            google_bp = make_google_blueprint(
                client_id=cid,
                client_secret=secret,
                scope=[
                    "https://www.googleapis.com/auth/youtube.readonly",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ],
                redirect_url="/oauth-login",
            )
            app.register_blueprint(google_bp, url_prefix="/login")
        else:
            app.logger.warning("Google OAuth credentials not configured")

    if init_admin and session_factory is not None:
        try:
            init_admin(app, session_factory)
        except Exception as exc:  # pragma: no cover - optional dependency
            app.logger.warning("Admin init failed: %s", exc)

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
    app.google_bp = google_bp

    return app
