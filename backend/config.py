import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "starbucks-knowledge")

    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.getenv("SLACK_APP_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")

    HITL_THRESHOLD_AMOUNT: float = float(os.getenv("HITL_THRESHOLD_AMOUNT", "50.0"))
    REFUND_WINDOW_DAYS: int = int(os.getenv("REFUND_WINDOW_DAYS", "7"))

    APP_ENV: str = os.getenv("APP_ENV", "local")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
    ORDERS_FILE: str = os.path.join(PROJECT_ROOT, "data", "orders.json")
    INVENTORY_FILE: str = os.path.join(PROJECT_ROOT, "data", "inventory.json")


config = Config()
