from fastapi import APIRouter, HTTPException

from backend.agents.prompts import REFUND_EVALUATION_PROMPT
from backend.models.schemas import RefundRequest, RefundResponse, RefundStatus
from backend.services.hitl_service import create_approval_request
from backend.services.llm_service import call_llm_with_context
from backend.services.order_service import evaluate_refund_eligibility, get_order_by_id
from backend.services.rag_service import retrieve_context

router = APIRouter(prefix="/api/refund", tags=["Refund"])


@router.post("/evaluate", response_model=RefundResponse)
async def evaluate_refund(request: RefundRequest):
    order = get_order_by_id(request.order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order '{request.order_id}' not found.")

    eligibility = evaluate_refund_eligibility(order)

    context, sources = retrieve_context(request.reason)

    order_summary = (
        f"Order ID: {order['order_id']}\n"
        f"Amount: ${order['total_amount']:.2f}\n"
        f"Refund Reason: {request.reason}\n"
        f"Order Date: {order['order_date']}\n"
        f"Status: {order['status']}\n"
        f"Eligibility Result: eligible={eligibility['eligible']}, "
        f"requires_hitl={eligibility['requires_hitl']}, "
        f"reason={eligibility['reason']}"
    )

    ai_reasoning = call_llm_with_context(REFUND_EVALUATION_PROMPT, order_summary, context)

    if not eligibility["eligible"]:
        status = RefundStatus.REJECTED
    elif eligibility["requires_hitl"]:
        status = RefundStatus.PENDING_HITL
    else:
        status = RefundStatus.APPROVED

    approval_id = ""
    recommendation = ai_reasoning
    if eligibility["requires_hitl"]:
        approval_id = create_approval_request(
            order_id=order["order_id"],
            amount=eligibility["amount"],
            reason=request.reason,
            ai_recommendation=ai_reasoning,
            requested_by=request.requested_by,
        )
        recommendation = f"[Approval ID: {approval_id}] {ai_reasoning}"

    return RefundResponse(
        order_id=order["order_id"],
        status=status,
        amount=eligibility["amount"],
        recommendation=recommendation,
        requires_human_approval=eligibility["requires_hitl"],
        ai_reasoning=ai_reasoning,
        policy_references=sources,
    )
