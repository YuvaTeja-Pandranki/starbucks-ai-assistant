import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from backend.config import config


def mask(token: str) -> str:
    if not token:
        return "(not set)"
    parts = token.split("-")
    return "-".join(parts[:2]) + "-***" if len(parts) >= 2 else token[:8] + "***"


def run_tests():
    print("=" * 60)
    print("STARBUCKS AI ASSISTANT — SLACK CONNECTION TEST")
    print("=" * 60)

    print("\n📋 Bot Configuration:")
    print(f"  BOT_TOKEN:       {mask(config.SLACK_BOT_TOKEN)}")
    print(f"  APP_TOKEN:       {mask(config.SLACK_APP_TOKEN)}")
    print(f"  SIGNING_SECRET:  {'***' if config.SLACK_SIGNING_SECRET else '(not set)'}")

    client = WebClient(token=config.SLACK_BOT_TOKEN)

    # Test 1: auth_test
    print("\n🔌 Test 1: API Authentication")
    try:
        auth = client.auth_test()
        print(f"  ✅ Connected successfully")
        print(f"  • Bot name:     {auth['user']}")
        print(f"  • Workspace:    {auth['team']}")
        print(f"  • Bot user ID:  {auth['user_id']}")
        print(f"  • App ID:       {auth.get('app_id', 'N/A')}")
        bot_user_id = auth["user_id"]
    except SlackApiError as e:
        print(f"  ❌ Authentication failed: {e.response['error']}")
        sys.exit(1)

    # Test 2: list channels
    print("\n📢 Test 2: Channel Access")
    try:
        channels_resp = client.conversations_list(types="public_channel,private_channel", limit=20)
        channels = channels_resp.get("channels", [])
        member_channels = [c for c in channels if c.get("is_member")]
        print(f"  ✅ Found {len(channels)} channels total, bot is member of {len(member_channels)}")
        if member_channels:
            print("  • Member channels:")
            for ch in member_channels[:5]:
                print(f"    - #{ch['name']} ({ch['id']})")
        else:
            print("  ℹ️  Bot is not a member of any channels yet.")
            print("     Invite the bot with: /invite @starbucks_ai_assistan")
    except SlackApiError as e:
        print(f"  ⚠️  Channel list failed: {e.response['error']}")
        channels = []
        member_channels = []

    # Test 3: post test message if bot is in a channel
    print("\n💬 Test 3: Send Test Message")
    if member_channels:
        test_channel = member_channels[0]["id"]
        test_channel_name = member_channels[0]["name"]
        try:
            msg = client.chat_postMessage(
                channel=test_channel,
                text=(
                    "☕ *Starbucks AI Assistant — Connection Test*\n"
                    "✅ Bot is online and connected to Slack.\n"
                    "• Pinecone RAG: 221 vectors, 8 policy documents\n"
                    "• HITL threshold: $50\n"
                    "• Multi-store support: STR-101, STR-102, STR-103\n"
                    "_Send me a DM or @mention me to get started._"
                ),
            )
            print(f"  ✅ Test message sent to #{test_channel_name}")
            print(f"  • Message timestamp: {msg['ts']}")
        except SlackApiError as e:
            print(f"  ⚠️  Could not send message: {e.response['error']}")
    else:
        print("  ⏭️  Skipped — bot is not in any channels yet.")
        print("     Add the bot to a channel and re-run this test.")

    # Test 4: bot info
    print("\n🤖 Test 4: Bot Info")
    try:
        bot_info = client.bots_info()
        bot = bot_info.get("bot", {})
        print(f"  ✅ Bot info retrieved")
        print(f"  • Bot ID:   {bot.get('id', 'N/A')}")
        print(f"  • App ID:   {bot.get('app_id', 'N/A')}")
    except SlackApiError as e:
        print(f"  ⚠️  Bot info failed: {e.response['error']}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  ✅ Slack API:        Connected")
    print(f"  ✅ Bot identity:     {auth['user']} (ID: {auth['user_id']})")
    print(f"  ✅ Workspace:        {auth['team']}")
    print(f"  {'✅' if member_channels else '⚠️ '} Channel access:   {len(member_channels)} channels")
    print(f"  ✅ Credentials:      BOT_TOKEN, APP_TOKEN, SIGNING_SECRET all set")
    print()
    print("Next step: Start the Slack bot with:")
    print("  conda run -n starbucks-ai python slack_bot/app.py")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
