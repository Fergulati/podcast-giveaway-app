from __future__ import annotations

import hmac
import hashlib
import json
from typing import Any

from flask import Blueprint, current_app, request, abort

try:
    from app.models import GiveawayWinner
except Exception:  # pragma: no cover - SQLAlchemy optional
    GiveawayWinner = None  # type: ignore

bp = Blueprint("paypal_webhook", __name__)


def _verify_signature() -> bool:
    """Verify PayPal webhook using a shared secret."""
    secret = current_app.config.get("PAYPAL_WEBHOOK_SECRET")
    if not secret:
        return False
    signature = request.headers.get("PayPal-Transmission-Sig")
    if not signature:
        return False
    expected = hmac.new(secret.encode(), request.get_data(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@bp.route("/webhooks/paypal", methods=["POST"])
def handle_webhook() -> tuple[str, int]:
    if not _verify_signature():
        abort(400)

    payload: dict[str, Any] = request.get_json(silent=True) or {}
    event_type = str(payload.get("event_type", "")).lower()
    if "payout" in event_type and "completed" in event_type:
        resource = payload.get("resource", {}) or {}
        payout_item_id = resource.get("payout_item_id") or resource.get("payout_item", {}).get("payout_item_id")
        if payout_item_id and GiveawayWinner is not None:
            session_factory = getattr(current_app, "session_factory", None)
            if session_factory is not None:
                session = session_factory()
                try:
                    winner = session.query(GiveawayWinner).filter_by(payout_item_id=payout_item_id).first()
                    if winner and not winner.paid:
                        winner.paid = True
                        session.commit()
                finally:
                    session.close()

    return "", 204


def init_paypal_webhook(app) -> None:
    app.register_blueprint(bp)
