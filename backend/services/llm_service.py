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


def call_llm_with_context(
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
    return call_llm(system_prompt, augmented_message, temperature=temperature)
