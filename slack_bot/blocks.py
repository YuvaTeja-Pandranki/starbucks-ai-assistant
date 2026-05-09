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
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📦 Inventory Alert — Store {store_id}",
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
        },
    ]

    for alert in alerts:
        emoji = "🔴" if alert["status"] == "CRITICAL" else "🟡"
        text = (
            f"{emoji} *{alert['item_name']}* — {alert['status']}\n"
            f"Stock: {alert['current_stock']} / Min: {alert['min_threshold']}\n"
            f"_{alert['recommendation']}_"
        )
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": text}}
        )

    return blocks
