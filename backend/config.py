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
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile")

    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "starbucks-knowledge")
    PINECONE_DIMENSION: int = 1024
    PINECONE_METRIC: str = "cosine"
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    USE_BEDROCK: bool = os.getenv("USE_BEDROCK", "true").lower() == "true"

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


def load_from_secrets_manager(cfg: "Config") -> None:
    if cfg.APP_ENV != "production":
        return
    try:
        import json
        import boto3
        client = boto3.client("secretsmanager", region_name=cfg.AWS_REGION)
        secret = client.get_secret_value(SecretId="starbucks-ai-assistant/prod")
        secrets = json.loads(secret["SecretString"])
        for key, value in secrets.items():
            if value:
                setattr(cfg, key, value)
        print("Loaded secrets from AWS Secrets Manager")
    except Exception as e:
        print(f"Could not load from Secrets Manager: {e}")


load_from_secrets_manager(config)
