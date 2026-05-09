import uuid
from datetime import datetime, timezone

pending_approvals: dict = {}
approval_log: list = []


def create_approval_request(
    order_id: str,
    amount: float,
    reason: str,
    ai_recommendation: str,
    requested_by: str,
) -> str:
    approval_id = "HITL-" + uuid.uuid4().hex[:8].upper()
    record = {
        "approval_id": approval_id,
        "order_id": order_id,
        "amount": amount,
        "reason": reason,
        "ai_recommendation": ai_recommendation,
        "requested_by": requested_by,
        "status": "pending",
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    pending_approvals[approval_id] = record
    print(f"[HITL] Approval request created: {approval_id} | Order: {order_id} | Amount: ${amount:.2f}")
    return approval_id


def get_pending_approval(approval_id: str) -> dict | None:
    return pending_approvals.get(approval_id)


def resolve_approval(
    approval_id: str,
    decision: str,
    approver_id: str,
    notes: str = "",
) -> dict:
    record = pending_approvals.get(approval_id)
    if not record:
        return {"error": f"Approval ID '{approval_id}' not found in pending approvals."}

    record.update(
        {
            "status": decision,
            "resolved_by": approver_id,
            "resolution_notes": notes,
            "resolved_at": datetime.now(tz=timezone.utc).isoformat(),
        }
    )
    approval_log.append(dict(record))
    del pending_approvals[approval_id]
    return record


def get_all_pending() -> list:
    return list(pending_approvals.values())


def get_audit_log() -> list:
    return approval_log
