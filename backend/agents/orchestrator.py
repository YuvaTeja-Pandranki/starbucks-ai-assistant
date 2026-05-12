import operator
import re
from typing import Annotated, List

import boto3
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from backend.agents.prompts import STORE_MANAGER_SYSTEM_PROMPT
from backend.agents.tools import (
    check_refund_eligibility,
    get_inventory_status,
    lookup_order,
    search_policy,
    trigger_hitl_approval,
)
from backend.config import config

_TOOLS = [
    lookup_order,
    check_refund_eligibility,
    search_policy,
    get_inventory_status,
    trigger_hitl_approval,
]


class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    store_id: str
    user_id: str
    requires_approval: bool
    approval_id: str


_llm = None
_llm_with_tools = None


def get_llm():
    if config.USE_BEDROCK and config.AWS_ACCESS_KEY_ID:
        bedrock_client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION,
        )
        return ChatBedrock(
            model_id=config.BEDROCK_MODEL_ID,
            client=bedrock_client,
            model_kwargs={"temperature": 0.1},
        )
    return ChatGroq(
        api_key=config.GROQ_API_KEY,
        model_name=config.GROQ_MODEL,
        temperature=0.1,
    )


def _get_llm_with_tools():
    global _llm, _llm_with_tools
    if _llm is None:
        _llm = get_llm()
        _llm_with_tools = _llm.bind_tools(_TOOLS)
    return _llm_with_tools


def agent_node(state: AgentState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=STORE_MANAGER_SYSTEM_PROMPT)] + list(messages)
    response = _get_llm_with_tools().invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(_TOOLS))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END},
    )
    workflow.add_edge("tools", "agent")
    return workflow.compile()


agent = build_agent()


def run_agent(
    message: str,
    user_id: str,
    store_id: str,
    history: list = [],
) -> dict:
    initial_state: AgentState = {
        "messages": history + [HumanMessage(content=message)],
        "store_id": store_id,
        "user_id": user_id,
        "requires_approval": False,
        "approval_id": "",
    }

    try:
        result = agent.invoke(initial_state)
    except Exception as e:
        if "rate_limit" in str(e).lower() or "429" in str(e):
            return {
                "response": "I am temporarily unavailable due to high demand. Please try again in a few minutes.",
                "requires_approval": False,
                "approval_id": "",
                "message_count": 0,
            }
        raise e

    final_response = result["messages"][-1].content

    requires_approval = False
    approval_id = ""
    for msg in result["messages"]:
        content = getattr(msg, "content", "") or ""
        if isinstance(content, str) and "HITL approval workflow triggered" in content:
            requires_approval = True
            match = re.search(r"HITL-[A-F0-9]{8}", content)
            if match:
                approval_id = match.group(0)
            break

    return {
        "response": final_response,
        "requires_approval": requires_approval,
        "approval_id": approval_id,
        "message_count": len(result["messages"]),
    }
