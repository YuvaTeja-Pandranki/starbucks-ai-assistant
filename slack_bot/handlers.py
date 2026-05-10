import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re

import httpx
from slack_bolt.async_app import AsyncApp

from backend.config import config
from slack_bot.blocks import (
    inventory_status_block,
    policy_response_block,
    refund_response_block,
    welcome_home_block,
)

app = AsyncApp(token=config.SLACK_BOT_TOKEN or "xoxb-placeholder")

API_BASE = "http://localhost:8000"


def _extract_store_id(text: str) -> str:
    match = re.search(r"STR-\d+", text.upper())
    return match.group(0) if match else "STR-101"


def _is_inventory_query(text: str) -> bool:
    keywords = ["inventory", "stock", "reorder", "low stock", "supply", "supplies"]
    return any(k in text.lower() for k in keywords)


def _is_refund_or_order_query(text: str) -> bool:
    keywords = ["refund", "order", "ORD-", "return", "reimburse", "charge"]
    return any(k in text for k in keywords) or any(
        k in text.lower() for k in ["refund", "order", "return", "reimburse", "charge"]
    )


async def _handle_inventory(user: str, text: str, say):
    store_id = _extract_store_id(text)
    loading = await say(f"<@{user}> Checking inventory for *{store_id}*... 📦")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE}/api/inventory/status",
                json={"store_id": store_id},
            )
        data = resp.json()

        alerts = data.get("alerts", [])
        summary = data.get("summary", "Inventory check complete.")
        blocks = inventory_status_block(store_id, alerts, summary)
        await say(blocks=blocks)

    except Exception as e:
        await say(f"<@{user}> ⚠️ Could not retrieve inventory — is the API running? (`{e}`)")


async def _handle_agent(user: str, text: str, store_id: str, say):
    loading_text = (
        "🔍 Looking up that order..." if _is_refund_or_order_query(text)
        else "🤔 Processing your request..."
    )
    await say(f"<@{user}> {loading_text} ⏳")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{API_BASE}/api/agent/chat",
                json={"message": text, "user_id": user, "store_id": store_id},
            )
        data = resp.json()

        if data.get("requires_approval") and data.get("approval_context", {}).get("approval_id"):
            approval_id = data["approval_context"]["approval_id"]
            blocks = refund_response_block(
                order_id=text,
                status="PENDING_APPROVAL",
                amount=0.0,
                reasoning=data["response"],
                approval_id=approval_id,
            )
            await say(blocks=blocks)
        else:
            response_text = data.get("response", "No response received.")
            await say(f"<@{user}> {response_text}")

    except httpx.TimeoutException:
        await say(f"<@{user}> ⚠️ The request timed out. The AI is taking longer than usual — please try again.")
    except Exception as e:
        await say(f"<@{user}> ⚠️ Something went wrong: `{e}`. Make sure the API server is running on port 8000.")


async def _handle_policy(user: str, text: str, say):
    await say(f"<@{user}> Searching policy documents... 📋 ⏳")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE}/api/policy/ask",
                json={"question": text},
            )
        data = resp.json()

        blocks = policy_response_block(
            question=text,
            answer=data.get("answer", "No answer found."),
            sources=data.get("sources", []),
        )
        await say(blocks=blocks)

    except Exception as e:
        await say(f"<@{user}> ⚠️ Could not query policy documents: `{e}`")


@app.event("app_mention")
async def handle_mention(event, say):
    user = event.get("user", "unknown")
    raw_text = event.get("text", "")
    message = raw_text.split(">", 1)[-1].strip() if ">" in raw_text else raw_text.strip()
    store_id = _extract_store_id(message)

    if _is_inventory_query(message):
        await _handle_inventory(user, message, say)
    else:
        await _handle_agent(user, message, store_id, say)


@app.event("message")
async def handle_dm(event, say):
    if event.get("channel_type") != "im":
        return
    if "subtype" in event:
        return

    user = event.get("user", "unknown")
    message = event.get("text", "").strip()
    if not message:
        return

    store_id = _extract_store_id(message)

    if _is_inventory_query(message):
        await _handle_inventory(user, message, say)
    elif "policy" in message.lower() or "what is" in message.lower() or "how do" in message.lower():
        await _handle_policy(user, message, say)
    else:
        await _handle_agent(user, message, store_id, say)


@app.event("app_home_opened")
async def handle_app_home_opened(event, client):
    user = event.get("user")
    try:
        await client.views_publish(
            user_id=user,
            view={
                "type": "home",
                "blocks": welcome_home_block(),
            },
        )
    except Exception as e:
        print(f"Failed to publish app home for {user}: {e}")


@app.action("approve_refund")
async def handle_approve(ack, body, say):
    await ack()
    approval_id = body["actions"][0]["value"]
    user = body["user"]["id"]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                f"{API_BASE}/api/hitl/resolve",
                json={
                    "approval_id": approval_id,
                    "decision": "approved",
                    "approver_id": user,
                    "notes": "Approved via Slack",
                },
            )
        await say(
            f"✅ *Refund approved* by <@{user}>.\n"
            f"• Approval ID: `{approval_id}`\n"
            f"• Decision logged to audit trail."
        )
    except Exception as e:
        await say(f"⚠️ Failed to record approval: `{e}`")


@app.action("reject_refund")
async def handle_reject(ack, body, say):
    await ack()
    approval_id = body["actions"][0]["value"]
    user = body["user"]["id"]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                f"{API_BASE}/api/hitl/resolve",
                json={
                    "approval_id": approval_id,
                    "decision": "rejected",
                    "approver_id": user,
                    "notes": "Rejected via Slack",
                },
            )
        await say(
            f"❌ *Refund rejected* by <@{user}>.\n"
            f"• Approval ID: `{approval_id}`\n"
            f"• Decision logged to audit trail."
        )
    except Exception as e:
        await say(f"⚠️ Failed to record rejection: `{e}`")
