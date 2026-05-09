import json

from langchain_core.tools import tool

from backend.services.hitl_service import create_approval_request
from backend.services.order_service import evaluate_refund_eligibility, get_order_by_id, load_inventory
from backend.services.rag_service import retrieve_context


@tool
def lookup_order(order_id: str) -> str:
    """Look up order details by order ID. Use when a manager asks about a specific order."""
    order = get_order_by_id(order_id)
    if order is None:
        return f"Order '{order_id}' not found."
    return json.dumps(order, default=str)


@tool
def check_refund_eligibility(order_id: str) -> str:
    """Check whether a specific order is eligible for a refund based on business rules."""
    order = get_order_by_id(order_id)
    if order is None:
        return f"Order '{order_id}' not found."
    result = evaluate_refund_eligibility(order)
    return json.dumps(result)


@tool
def search_policy(query: str) -> str:
    """Search Starbucks policy documents for answers. Use for policy questions, compliance, and rules."""
    context, sources = retrieve_context(query)
    return (
        "POLICY CONTEXT:\n"
        "---------------\n"
        f"{context}\n\n"
        f"SOURCES: {', '.join(sources)}"
    )


@tool
def get_inventory_status(store_id: str) -> str:
    """Get current inventory status for a store. Returns items and their stock levels."""
    inventory = load_inventory(store_id)
    if not inventory:
        return f"No inventory data found for store '{store_id}'."
    return json.dumps(inventory, default=str)


@tool
def trigger_hitl_approval(order_id: str, amount: float, reason: str, requested_by: str) -> str:
    """Trigger a human-in-the-loop approval workflow for high-value or sensitive decisions. \
Use when a refund exceeds the auto-approval threshold."""
    approval_id = create_approval_request(
        order_id=order_id,
        amount=amount,
        reason=reason,
        ai_recommendation=(
            f"AI recommends manager review for order {order_id} "
            f"refund of ${amount:.2f}. Reason: {reason}."
        ),
        requested_by=requested_by,
    )
    return (
        f"HITL approval workflow triggered. Approval ID: {approval_id}. "
        f"Amount: ${amount:.2f}. Order: {order_id}. Awaiting human review."
    )
