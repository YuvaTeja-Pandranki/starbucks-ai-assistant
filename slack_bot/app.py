import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk import WebClient
from backend.config import config
import httpx

API_BASE = "http://localhost:8000"

BOT_USER_ID = None

app = AsyncApp(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET,
    ignoring_self_events_enabled=False
)

@app.event({"type": "message", "subtype": None})
async def handle_direct_message(event, say, logger):
    if event.get("user") == BOT_USER_ID:
        return
    if event.get("bot_id"):
        return
    if event.get("subtype") == "bot_message":
        return

    logger.info(f"HANDLER FIRED: {event}")
    text = event.get("text", "")
    user = event.get("user", "unknown")

    if not text:
        return

    logger.info(f"Processing message from {user}: {text}")

    try:
        await say("Processing your request... ⏳")

        async def _call_api():
            async with httpx.AsyncClient(timeout=120.0) as client:
                return await client.post(f"{API_BASE}/api/agent/chat", json={
                    "message": text,
                    "user_id": user,
                    "store_id": "STR-101",
                    "conversation_history": []
                })

        api_task = asyncio.create_task(_call_api())
        try:
            response = await asyncio.wait_for(asyncio.shield(api_task), timeout=30.0)
        except asyncio.TimeoutError:
            await say("Still working on it, complex queries take a moment... 🔍")
            response = await api_task

        if response.status_code == 200:
            data = response.json()
            reply = data.get("response", "Sorry I could not process that.")
            requires_approval = data.get("requires_approval", False)
            approval_context = data.get("approval_context")

            if requires_approval and approval_context:
                approval_id = approval_context.get("approval_id", "")
                await say(
                    blocks=[
                        {
                            "type": "header",
                            "text": {"type": "plain_text", "text": "⚠️ Manager Approval Required"}
                        },
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*AI Analysis:*\n{reply}"}
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Approval ID:*\n{approval_id}"},
                                {"type": "mrkdwn", "text": "*Status:*\nPending Review"}
                            ]
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "✅ Approve"},
                                    "style": "primary",
                                    "action_id": "approve_refund",
                                    "value": approval_id
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "❌ Reject"},
                                    "style": "danger",
                                    "action_id": "reject_refund",
                                    "value": approval_id
                                }
                            ]
                        }
                    ],
                    text=reply
                )
            else:
                await say(reply)
        else:
            await say(f"⚠️ API error: {response.status_code}")

    except httpx.TimeoutException:
        await say("⚠️ Request timed out. The AI is taking too long. Please try again.")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await say("⚠️ Error processing request. Please try again in a moment.")


@app.action("approve_refund")
async def handle_approve(ack, body, say):
    await ack()
    approval_id = body["actions"][0]["value"]
    user = body["user"]["id"]
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/api/hitl/resolve", json={
                "approval_id": approval_id,
                "decision": "approved",
                "approver_id": user,
                "notes": "Approved via Slack"
            })
        await say(f"✅ Refund *{approval_id}* approved by <@{user}>. Audit log updated.")
    except Exception as e:
        await say(f"Error: {str(e)}")


@app.action("reject_refund")
async def handle_reject(ack, body, say):
    await ack()
    approval_id = body["actions"][0]["value"]
    user = body["user"]["id"]
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_BASE}/api/hitl/resolve", json={
                "approval_id": approval_id,
                "decision": "rejected",
                "approver_id": user,
                "notes": "Rejected via Slack"
            })
        await say(f"❌ Refund *{approval_id}* rejected by <@{user}>. Audit log updated.")
    except Exception as e:
        await say(f"Error: {str(e)}")


async def main():
    global BOT_USER_ID

    print("=" * 60)
    print("☕ Starbucks AI Assistant - Slack Bot Starting")
    print(f"Bot token set: {bool(config.SLACK_BOT_TOKEN)}")
    print(f"App token set: {bool(config.SLACK_APP_TOKEN)}")

    client = WebClient(token=config.SLACK_BOT_TOKEN)
    auth = client.auth_test()
    BOT_USER_ID = auth["user_id"]
    print(f"Bot User ID set: {BOT_USER_ID}")
    print("=" * 60)

    handler = AsyncSocketModeHandler(app, config.SLACK_APP_TOKEN)
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
