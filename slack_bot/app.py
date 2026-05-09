import asyncio

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from backend.config import config
from slack_bot.handlers import app


async def main():
    print("Starting Starbucks AI Assistant Slack Bot...")
    handler = AsyncSocketModeHandler(app, config.SLACK_APP_TOKEN)
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
