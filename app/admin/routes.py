from __future__ import annotations

from typing import Callable, Any

from flask import session

try:
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView
except Exception:  # pragma: no cover - optional dependency
    Admin = None  # type: ignore
    ModelView = object  # type: ignore

from ..models import PointsMatrix, EventType
from ..tasks import schedule_points_recalc


class PointsMatrixAdmin(ModelView):
    column_list = ["event_type", "value"]

    def is_accessible(self) -> bool:  # pragma: no cover - simple session check
        return session.get("role") == "ROLE_ADMIN"

    def after_model_change(self, form, model, is_created):
        etype = model.event_type
        if isinstance(etype, EventType):
            etype = etype.name
        schedule_points_recalc(etype)


def init_admin(app, session_factory: Callable[[], Any] | None):
    """Initialize Flask-Admin views."""
    if Admin is None or session_factory is None:
        return None
    admin = Admin(app, name="Admin", template_mode="bootstrap3")
    admin.add_view(PointsMatrixAdmin(PointsMatrix, session_factory()))
    return admin
