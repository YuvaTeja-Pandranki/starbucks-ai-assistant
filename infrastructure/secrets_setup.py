import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from dotenv import load_dotenv

load_dotenv()

secrets_client = boto3.client(
    "secretsmanager",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1",
)

secrets = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
    "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY", ""),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
    "SLACK_APP_TOKEN": os.getenv("SLACK_APP_TOKEN", ""),
    "SLACK_SIGNING_SECRET": os.getenv("SLACK_SIGNING_SECRET", ""),
}

secret_name = "starbucks-ai-assistant/prod"

try:
    secrets_client.create_secret(
        Name=secret_name,
        Description="Starbucks AI Assistant production secrets",
        SecretString=json.dumps(secrets),
    )
    print("Created secret:", secret_name)
except secrets_client.exceptions.ResourceExistsException:
    secrets_client.update_secret(
        SecretId=secret_name,
        SecretString=json.dumps(secrets),
    )
    print("Updated secret:", secret_name)

print("Secrets stored in AWS Secrets Manager")
