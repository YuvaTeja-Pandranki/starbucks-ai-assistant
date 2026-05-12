import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.config import config


def call_llm(
    system_prompt: str,
    user_message: str,
    conversation_history: list = [],
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> str:
    if config.USE_BEDROCK and config.AWS_ACCESS_KEY_ID:
        from backend.services.bedrock_service import call_bedrock
        return call_bedrock(system_prompt, user_message, conversation_history, temperature, max_tokens)

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            client = ChatGroq(
                api_key=config.GROQ_API_KEY,
                model_name=config.GROQ_MODEL,
                temperature=temperature,
            )
            messages = [SystemMessage(content=system_prompt)]
            for item in conversation_history[-6:]:
                if item.get("role") == "user":
                    messages.append(HumanMessage(content=item["content"]))
                elif item.get("role") == "assistant":
                    messages.append(AIMessage(content=item["content"]))
            messages.append(HumanMessage(content=user_message))
            response = client.invoke(messages)
            return response.content
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit, waiting {retry_delay}s before retry {attempt + 1}...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return "I am temporarily unavailable due to high demand. Please try again in a few minutes."
            else:
                raise e


def call_llm_with_context(
    system_prompt: str,
    user_message: str,
    retrieved_context: str,
    temperature: float = 0.1,
) -> str:
    if config.USE_BEDROCK and config.AWS_ACCESS_KEY_ID:
        from backend.services.bedrock_service import call_bedrock_with_context
        return call_bedrock_with_context(system_prompt, user_message, retrieved_context, temperature)

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
    return call_llm(system_prompt, augmented_message, temperature=temperature)
