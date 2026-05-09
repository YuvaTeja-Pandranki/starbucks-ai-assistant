import json
from datetime import datetime, timezone

from backend.config import config


def load_orders() -> list:
    with open(config.ORDERS_FILE, "r") as f:
        return json.load(f)["orders"]


def get_order_by_id(order_id: str) -> dict | None:
    for order in load_orders():
        if order["order_id"].upper() == order_id.upper():
            flat = dict(order)
            flat["customer_name"] = order["customer"]["name"]
            return flat
    return None


def is_within_refund_window(order_date_str: str, window_days: int = 7) -> bool:
    order_date = datetime.fromisoformat(order_date_str).replace(tzinfo=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    return (now - order_date).days <= window_days


def evaluate_refund_eligibility(order: dict) -> dict:
    amount = order.get("total_amount", 0.0)
    reason = (order.get("refund_reason") or "").lower()

    if not order.get("refund_requested", False):
        return {
            "eligible": False,
            "reason": "No refund was requested for this order.",
            "requires_hitl": False,
            "amount": amount,
        }

    if "changed mind" in reason:
        return {
            "eligible": False,
            "reason": (
                "Changed-mind refunds are only eligible within 30 minutes of order "
                "fulfillment. This window has passed."
            ),
            "requires_hitl": False,
            "amount": amount,
        }

    if not is_within_refund_window(order["order_date"], config.REFUND_WINDOW_DAYS):
        return {
            "eligible": False,
            "reason": (
                f"Order is outside the {config.REFUND_WINDOW_DAYS}-day refund window."
            ),
            "requires_hitl": False,
            "amount": amount,
        }

    requires_hitl = amount >= config.HITL_THRESHOLD_AMOUNT
    return {
        "eligible": True,
        "reason": "Order meets refund eligibility criteria.",
        "requires_hitl": requires_hitl,
        "amount": amount,
    }


def load_inventory(store_id: str) -> list:
    with open(config.INVENTORY_FILE, "r") as f:
        data = json.load(f)
    if data.get("store_id") == store_id:
        return data.get("inventory", [])
    return []
