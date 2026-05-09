import httpx
from slack_bolt.async_app import AsyncApp

from backend.config import config
from slack_bot.blocks import inventory_alert_block, refund_response_block

app = AsyncApp(token=config.SLACK_BOT_TOKEN or "xoxb-placeholder")

API_BASE = "http://localhost:8000"


@app.event("app_mention")
async def handle_mention(event, say):
    user = event.get("user", "unknown")
    raw_text = event.get("text", "")
    # Strip the bot mention prefix (<@BOTID> ...)
    message = raw_text.split(">", 1)[-1].strip() if ">" in raw_text else raw_text.strip()

    await say(f"<@{user}> Let me check that for you... 🔍")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/api/agent/chat",
            json={"message": message, "user_id": user, "store_id": "STR-101"},
        )
        data = resp.json()

    await say(f"<@{user}> {data['response']}")


@app.event("message")
async def handle_dm(event, say):
    if event.get("channel_type") != "im":
        return
    if "subtype" in event:
        return

    user = event.get("user", "unknown")
    message = event.get("text", "").strip()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/api/agent/chat",
            json={"message": message, "user_id": user, "store_id": "STR-101"},
        )
        data = resp.json()

    if data.get("requires_approval") and data.get("approval_context", {}).get("approval_id"):
        approval_id = data["approval_context"]["approval_id"]
        blocks = refund_response_block(
            order_id=message,
            status="PENDING_HITL",
            amount=0.0,
            reasoning=data["response"],
            approval_id=approval_id,
        )
        await say(blocks=blocks)
    else:
        await say(data["response"])


@app.action("approve_refund")
async def handle_approve(ack, body, say):
    await ack()
    approval_id = body["actions"][0]["value"]
    user = body["user"]["id"]

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

    await say(f"✅ Refund approved by <@{user}>. Approval ID: `{approval_id}`")


@app.action("reject_refund")
async def handle_reject(ack, body, say):
    await ack()
    approval_id = body["actions"][0]["value"]
    user = body["user"]["id"]

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

    await say(f"❌ Refund rejected by <@{user}>. Approval ID: `{approval_id}`")
