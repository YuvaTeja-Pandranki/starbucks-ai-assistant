import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def refund_response_block(
    order_id: str,
    status: str,
    amount: float,
    reasoning: str,
    approval_id: str | None = None,
) -> list:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔄 Refund Evaluation Result"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Order ID:*\n{order_id}"},
                {"type": "mrkdwn", "text": f"*Amount:*\n${amount:.2f}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*AI Analysis:*\n{reasoning}"},
        },
    ]

    if approval_id:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "action_id": "approve_refund",
                        "value": approval_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "action_id": "reject_refund",
                        "value": approval_id,
                    },
                ],
            }
        )

    return blocks


def inventory_alert_block(store_id: str, alerts: list, summary: str) -> list:
    """Legacy name kept for backwards compatibility."""
    return inventory_status_block(store_id, alerts, summary)


def inventory_status_block(store_id: str, alerts: list, summary: str) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📦 Inventory Status — Store {store_id}",
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
        },
        {"type": "divider"},
    ]

    if not alerts:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ *All items are at healthy stock levels.*",
                },
            }
        )
        return blocks

    for alert in alerts:
        status = alert.get("status", "UNKNOWN")
        emoji = "🔴" if status == "CRITICAL" else "🟡" if status == "LOW" else "🟢"
        text = (
            f"{emoji} *{alert.get('item_name', alert.get('name', 'Unknown item'))}* — `{status}`\n"
            f"• Stock: *{alert.get('current_stock', '?')}* / Threshold: {alert.get('min_threshold', alert.get('reorder_threshold', '?'))}\n"
            f"• _{alert.get('recommendation', alert.get('notes', ''))}_"
        )
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

    return blocks


def policy_response_block(question: str, answer: str, sources: list) -> list:
    sources_text = (
        "• " + "\n• ".join(f"`{s}`" for s in sources)
        if sources
        else "_No sources found_"
    )
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📋 Policy Answer"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_Question: {question}_"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Sources:*\n{sources_text}",
                }
            ],
        },
    ]
    return blocks


def welcome_home_block() -> list:
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "☕ Starbucks AI Assistant"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Welcome! I'm your *AI-powered store operations assistant*. "
                    "I can help you with refund decisions, inventory checks, policy lookups, "
                    "and compliance questions — all through natural language.\n\n"
                    "Just mention me in a channel or send me a direct message to get started."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*💬 Example questions you can ask:*\n"
                    "• `Should I approve the refund for order ORD-003?`\n"
                    "• `What is the inventory status for STR-101?`\n"
                    "• `What is our refund policy for quality issues?`\n"
                    "• `How do I process a void in the POS system?`\n"
                    "• `What are the dress code requirements for partners?`"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*🏪 Stores Supported:*\nSTR-101, STR-102, STR-103"},
                {"type": "mrkdwn", "text": "*📚 Policy Documents:*\n8 documents, 221 vectors"},
                {"type": "mrkdwn", "text": "*🤖 AI Model:*\nGroq llama-3.3-70b-versatile"},
                {"type": "mrkdwn", "text": "*🔍 Vector Search:*\nPinecone cloud (AWS us-east-1)"},
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Starbucks AI Assistant v1.2.0 • Decisions above $50 require human approval",
                }
            ],
        },
    ]
