import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)

from backend.services.rag_service import retrieve_context


def test_retrieve_returns_tuple():
    result = retrieve_context("refund policy")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_retrieve_context_non_empty():
    context, _ = retrieve_context("refund threshold for manager approval")
    assert isinstance(context, str)
    assert len(context) > 0


def test_retrieve_sources_are_list():
    _, sources = retrieve_context("refund threshold")
    assert isinstance(sources, list)


def test_retrieve_inventory_policy():
    _, sources = retrieve_context("CRITICAL inventory emergency order")
    assert len(sources) > 0


def test_retrieve_compliance_rules():
    context, _ = retrieve_context("audit logging compliance")
    assert isinstance(context, str)
    assert len(context) > 0
