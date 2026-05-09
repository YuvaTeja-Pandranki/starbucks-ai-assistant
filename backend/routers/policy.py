from fastapi import APIRouter

from backend.agents.prompts import POLICY_QA_PROMPT
from backend.models.schemas import PolicyQueryRequest, PolicyQueryResponse
from backend.services.llm_service import call_llm_with_context
from backend.services.rag_service import retrieve_context

router = APIRouter(prefix="/api/policy", tags=["Policy"])


@router.post("/ask", response_model=PolicyQueryResponse)
async def ask_policy(request: PolicyQueryRequest):
    context, sources = retrieve_context(request.question)

    answer = call_llm_with_context(POLICY_QA_PROMPT, request.question, context)

    confidence = 0.9 if sources else 0.4

    return PolicyQueryResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
    )
