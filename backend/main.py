import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if os.getenv("APP_ENV") == "production":
    logging.getLogger().setLevel(logging.INFO)

from backend.agents.orchestrator import run_agent
from backend.models.schemas import (
    AgentRequest,
    AgentResponse,
    HITLApprovalRequest,
    HITLApprovalResponse,
)
from backend.routers import ingestion, inventory, policy, refund
from backend.services.hitl_service import get_all_pending, get_audit_log, resolve_approval

app = FastAPI(
    title="Starbucks AI Assistant API",
    description="AI-powered operations assistant for Starbucks store managers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(refund.router)
app.include_router(inventory.router)
app.include_router(policy.router)
app.include_router(ingestion.router)


@app.get("/")
async def root():
    return {"message": "Starbucks AI Assistant API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/agent/chat", response_model=AgentResponse)
async def agent_chat(request: AgentRequest):
    result = run_agent(
        message=request.message,
        user_id=request.user_id,
        store_id=request.store_id,
        history=request.conversation_history or [],
    )

    approval_context = (
        {"approval_id": result["approval_id"]} if result["requires_approval"] else None
    )

    return AgentResponse(
        response=result["response"],
        actions_taken=[],
        requires_approval=result["requires_approval"],
        approval_context=approval_context,
    )


@app.post("/api/hitl/resolve", response_model=HITLApprovalResponse)
async def resolve_hitl(request: HITLApprovalRequest):
    result = resolve_approval(
        approval_id=request.approval_id,
        decision=request.decision,
        approver_id=request.approver_id,
        notes=request.notes or "",
    )

    if "error" in result:
        return HITLApprovalResponse(
            approval_id=request.approval_id,
            status="error",
            message=result["error"],
        )

    return HITLApprovalResponse(
        approval_id=request.approval_id,
        status=result["status"],
        message=f"Approval {request.approval_id} resolved as {result['status']} by {request.approver_id}.",
    )


@app.get("/api/hitl/pending")
async def get_pending_approvals():
    return {"pending": get_all_pending()}


@app.get("/api/hitl/audit-log")
async def get_hitl_audit_log():
    return {"log": get_audit_log()}
