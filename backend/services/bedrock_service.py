import json

import boto3
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.config import config


def get_bedrock_client():
    kwargs = {"region_name": config.AWS_REGION}
    if config.AWS_ACCESS_KEY_ID and config.APP_ENV != "production":
        kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    return boto3.client("bedrock-runtime", **kwargs)


def call_bedrock(
    system_prompt: str,
    user_message: str,
    conversation_history: list = [],
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> str:
    try:
        bedrock = get_bedrock_client()

        messages = []
        for item in conversation_history[-6:]:
            if item.get("role") == "user":
                messages.append({"role": "user", "content": item["content"]})
            elif item.get("role") == "assistant":
                messages.append({"role": "assistant", "content": item["content"]})
        messages.append({"role": "user", "content": user_message})

        response = bedrock.invoke_model(
            modelId=config.BEDROCK_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": messages,
            }),
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
    except Exception as e:
        return f"I am temporarily unavailable. Please try again. ({e})"


def call_bedrock_with_context(
    system_prompt: str,
    user_message: str,
    retrieved_context: str,
    temperature: float = 0.1,
) -> str:
    augmented_message = (
        f"RETRIEVED CONTEXT:\n"
        f"---\n"
        f"{retrieved_context}\n"
        f"---\n"
        f"USER QUESTION:\n"
        f"{user_message}\n\n"
        f"Answer based ONLY on the retrieved context above. "
        f"If the answer is not in the context, say so clearly."
    )
    return call_bedrock(system_prompt, augmented_message, temperature=temperature)
