import json

from fastapi import APIRouter

from backend.agents.prompts import INVENTORY_ANALYSIS_PROMPT
from backend.models.schemas import InventoryAlert, InventoryQueryRequest, InventoryResponse
from backend.services.llm_service import call_llm
from backend.services.order_service import load_inventory

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.post("/status", response_model=InventoryResponse)
async def get_inventory_status(request: InventoryQueryRequest):
    inventory = load_inventory(request.store_id)

    alerts: list[InventoryAlert] = []
    for item in inventory:
        status = item.get("status", "OK")
        if status == "CRITICAL":
            recommendation = "Emergency order today"
        elif status == "LOW":
            recommendation = "Place order within 24 hours"
        else:
            continue

        alerts.append(
            InventoryAlert(
                item_name=item["name"],
                status=status,
                current_stock=item["current_stock"],
                min_threshold=item["reorder_threshold"],
                recommendation=recommendation,
            )
        )

    ai_summary = call_llm(
        INVENTORY_ANALYSIS_PROMPT,
        json.dumps(inventory, default=str),
    )

    return InventoryResponse(
        store_id=request.store_id,
        alerts=alerts,
        ai_summary=ai_summary,
    )
