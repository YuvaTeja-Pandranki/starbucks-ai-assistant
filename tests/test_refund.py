from datetime import datetime, timezone

from backend.services.order_service import evaluate_refund_eligibility, get_order_by_id


def test_order_lookup_found():
    result = get_order_by_id("ORD-001")
    assert result is not None
    assert result["order_id"] == "ORD-001"
    assert result["customer_name"] == "Alice Johnson"


def test_order_lookup_not_found():
    result = get_order_by_id("ORD-FAKE")
    assert result is None


def test_order_lookup_case_insensitive():
    result = get_order_by_id("ord-001")
    assert result is not None


def test_refund_not_requested():
    order = get_order_by_id("ORD-004")
    result = evaluate_refund_eligibility(order)
    assert result["eligible"] is False


def test_refund_changed_mind_rejected():
    order = get_order_by_id("ORD-003")
    result = evaluate_refund_eligibility(order)
    assert result["eligible"] is False
    assert "changed mind" in result["reason"].lower() or "30" in result["reason"]


def test_refund_quality_issue_outside_window():
    order = get_order_by_id("ORD-002")
    result = evaluate_refund_eligibility(order)
    assert result["eligible"] is False


def test_hitl_threshold():
    order = {
        "total_amount": 75.0,
        "refund_requested": True,
        "refund_reason": "Wrong order",
        "order_date": datetime.now(tz=timezone.utc).isoformat(),
    }
    result = evaluate_refund_eligibility(order)
    assert result["eligible"] is True
    assert result["requires_hitl"] is True


def test_below_hitl_threshold():
    order = {
        "total_amount": 25.0,
        "refund_requested": True,
        "refund_reason": "Wrong order",
        "order_date": datetime.now(tz=timezone.utc).isoformat(),
    }
    result = evaluate_refund_eligibility(order)
    assert result["eligible"] is True
    assert result["requires_hitl"] is False
