from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RefundStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING_HITL = "PENDING_HITL"
    ESCALATED = "ESCALATED"


class RefundRequest(BaseModel):
    order_id: str
    reason: str
    requested_by: str


class RefundResponse(BaseModel):
    order_id: str
    status: RefundStatus
    amount: float
    recommendation: str
    requires_human_approval: bool
    ai_reasoning: str
    policy_references: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InventoryQueryRequest(BaseModel):
    store_id: str
    category: Optional[str] = None


class InventoryAlert(BaseModel):
    item_name: str
    status: str
    current_stock: float
    min_threshold: float
    recommendation: str


class InventoryResponse(BaseModel):
    store_id: str
    alerts: List[InventoryAlert]
    ai_summary: str


class PolicyQueryRequest(BaseModel):
    question: str
    context: Optional[str] = None


class PolicyQueryResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float


class AgentRequest(BaseModel):
    message: str
    user_id: str
    store_id: str
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class AgentResponse(BaseModel):
    response: str
    actions_taken: List[str]
    requires_approval: bool
    approval_context: Optional[Dict[str, Any]] = None


class HITLApprovalRequest(BaseModel):
    approval_id: str
    decision: str
    approver_id: str
    notes: Optional[str] = None


class HITLApprovalResponse(BaseModel):
    approval_id: str
    status: str
    message: str
