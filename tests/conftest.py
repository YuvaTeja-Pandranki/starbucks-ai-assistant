from datetime import datetime, timezone

import pytest


@pytest.fixture
def sample_order():
    return {
        "order_id": "TEST-001",
        "customer_name": "Test User",
        "store_id": "STR-101",
        "total_amount": 25.0,
        "refund_requested": True,
        "refund_reason": "Wrong order received",
        "order_date": datetime.now(tz=timezone.utc).isoformat(),
        "status": "delivered",
    }


@pytest.fixture
def high_value_order():
    return {
        "order_id": "TEST-002",
        "customer_name": "Test User",
        "store_id": "STR-101",
        "total_amount": 75.0,
        "refund_requested": True,
        "refund_reason": "Wrong order received",
        "order_date": datetime.now(tz=timezone.utc).isoformat(),
        "status": "delivered",
    }
