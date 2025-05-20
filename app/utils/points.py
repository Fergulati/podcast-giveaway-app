from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import object_session

from ..models import EventType, PointsLedger, get_total_points

# Default matrix if not provided via Flask config
DEFAULT_POINT_MATRIX: Dict[str, Any] = {
    "COMMENT": 5,
    "LIKE": 2,
    "SUPERCHAT": 10,
    "LIVESTREAM_CHAT": 1,
}


def _get_matrix() -> Dict[str, Any]:
    """Fetch the points matrix from Flask config if available."""
    try:  # Only available when Flask is installed and an app context is active
        from flask import current_app

        matrix = current_app.config.get("POINT_MATRIX")
        if matrix:
            return matrix
    except Exception:  # pragma: no cover - Flask not available or no context
        pass
    return DEFAULT_POINT_MATRIX


def apply_points(user, engagement) -> int:
    """Apply points for an engagement.

    A ledger row is created based on the POINT_MATRIX configuration. The row is
    persisted immediately to preserve immutability. The user's new total is
    returned.
    """

    session = object_session(user)
    if session is None:
        raise RuntimeError("User object is not attached to a session")

    matrix = _get_matrix()
    rule = matrix.get(engagement.event_type.name)
    if rule is None:
        delta = 0
    elif callable(rule):
        delta = int(rule(engagement))
    else:
        delta = int(rule)

    ledger = PointsLedger(
        user_id=user.id,
        engagement=engagement,
        points_delta=delta,
        reason=engagement.event_type.name,
        timestamp=datetime.utcnow(),
    )
    session.add(ledger)
    session.commit()
    return get_total_points(session, user.id)
