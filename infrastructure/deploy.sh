#!/bin/bash
set -e

echo "Deploying Starbucks AI Assistant to AWS Lambda..."

# Check AWS credentials
aws sts get-caller-identity

# Install SAM CLI if not installed
if ! command -v sam &> /dev/null; then
    pip install aws-sam-cli
fi

# Build the application
sam build

# Deploy
sam deploy \
  --stack-name starbucks-ai-assistant \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    PineconeApiKey=$PINECONE_API_KEY \
    GroqApiKey=$GROQ_API_KEY \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

echo "Deployment complete!"
