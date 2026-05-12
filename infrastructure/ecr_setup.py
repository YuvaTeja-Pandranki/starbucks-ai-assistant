import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from dotenv import load_dotenv

load_dotenv()

ecr = boto3.client(
    "ecr",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1",
)

try:
    response = ecr.create_repository(
        repositoryName="starbucks-ai-assistant",
        imageScanningConfiguration={"scanOnPush": True},
    )
    repo_uri = response["repository"]["repositoryUri"]
    print("ECR repository created:", repo_uri)
except ecr.exceptions.RepositoryAlreadyExistsException:
    response = ecr.describe_repositories(repositoryNames=["starbucks-ai-assistant"])
    repo_uri = response["repositories"][0]["repositoryUri"]
    print("ECR repository exists:", repo_uri)

print("ECR URI:", repo_uri)
