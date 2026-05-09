import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.order_service import load_inventory, load_orders

if __name__ == "__main__":
    orders = load_orders()
    print(f"\nTotal orders: {len(orders)}")
    print("-" * 40)
    for order in orders:
        print(
            f"  {order['order_id']} | "
            f"{order['customer']['name']} | "
            f"${order['total_amount']:.2f}"
        )

    print("\nInventory for STR-101:")
    print("-" * 40)
    inventory = load_inventory("STR-101")
    for item in inventory:
        print(f"  {item['name']} | {item['status']}")
