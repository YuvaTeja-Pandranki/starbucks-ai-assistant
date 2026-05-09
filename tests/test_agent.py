import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)

from backend.agents.orchestrator import run_agent


def test_run_agent_returns_dict():
    result = run_agent("What is the refund policy?", user_id="test_user", store_id="STR-101")
    assert isinstance(result, dict)
    assert "response" in result
    assert "requires_approval" in result


def test_run_agent_response_non_empty():
    result = run_agent("What is the refund policy?", user_id="test_user", store_id="STR-101")
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0


def test_run_agent_no_approval_for_policy_question():
    result = run_agent(
        "What is the refund policy for quality issues?",
        user_id="test_user",
        store_id="STR-101",
    )
    assert result["requires_approval"] is False


def test_run_agent_order_lookup():
    result = run_agent("Look up order ORD-001", user_id="test_user", store_id="STR-101")
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
