# mcp_vendor.py (Improved Version)

import time
import uuid
from enum import Enum
from typing import List, Dict, Optional, Literal, Annotated

from mcp_starter import mcp
from pydantic import Field


# --- Enum definitions for clarity and safety ---
class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    READY = "ready"
    ASSIGNED = "assigned"
    DELIVERED = "delivered"
    PAID = "paid"

class PaymentStatus(str, Enum):
    UNREQUESTED = "unrequested"
    REQUESTED = "requested"
    PAID = "paid"


# --- In-memory storage (replace with DB later) ---
orders: Dict[str, Dict] = {}
delivery_agents: Dict[str, Dict] = {
    "agent_1": {"id": "agent_1", "name": "Sam", "phone": "919991112223"},
    "agent_2": {"id": "agent_2", "name": "Asha", "phone": "918881112223"},
    "agent_3": {"id": "agent_3", "name": "Raj", "phone": "917771112223"},
}


# --- Utility Functions ---
def now() -> int:
    return int(time.time())

def get_order(order_id: str) -> Optional[Dict]:
    return orders.get(order_id)

def validate_status(order: Dict, expected_status: OrderStatus) -> Optional[str]:
    if order["status"] != expected_status:
        return f"Order must be '{expected_status}', but is '{order['status']}'."


# --- Order creation helper for demo ---
def new_order(vendor_id: str, customer_name: str, customer_phone: str, address: str, items: List[Dict]) -> str:
    oid = str(uuid.uuid4())[:8]
    orders[oid] = {
        "order_id": oid,
        "vendor_id": vendor_id,
        "customer": {"name": customer_name, "phone": customer_phone},
        "address": address,
        "items": items,
        "status": OrderStatus.PENDING,
        "created_at": now(),
        "accepted_at": None,
        "ready_at": None,
        "assigned_at": None,
        "delivered_at": None,
        "paid_at": None,
        "delivery_agent": None,
        "payment_requested": False,
        "payment_status": PaymentStatus.UNREQUESTED,
    }
    return oid


# --- Seed demo orders ---
if not orders:
    new_order("vendor_1", "Neha", "919876500001", "221B Baker St", [{"sku": "chai", "qty": 2}])
    new_order("vendor_1", "Arjun", "919876500002", "MG Road, BLR", [{"sku": "samosa", "qty": 6}])


# --- Tools ---

@mcp.tool(
    description="Retrieves a list of a vendor's orders. Use this when a user wants to see, view, check, find, or list their orders. Can filter by status like 'pending', 'accepted', or 'completed'."
)
def orders_list(
    vendor_id: Annotated[str, Field(description="Vendor ID to list orders for.")],
    status_filter: Annotated[Optional[str], Field(description="Optional filter (e.g., pending, accepted).")] = None,
) -> Dict:
    result = [o for o in orders.values() if o["vendor_id"] == vendor_id]
    if status_filter:
        result = [o for o in result if o["status"] == status_filter]
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return {"orders": result, "count": len(result)}


@mcp.tool(description="Accept or reject a pending order.")
def order_decide(
    order_id: Annotated[str, Field(description="Order ID to act on.")],
    accept: Annotated[bool, Field(description="Accept (true) or reject (false).")],
) -> Dict:
    o = get_order(order_id)
    if not o:
        return {"ok": False, "error": "order_not_found"}
    if o["status"] != OrderStatus.PENDING:
        return {"ok": False, "error": f"Order already '{o['status']}'."}
    if accept:
        o["status"] = OrderStatus.ACCEPTED
        o["accepted_at"] = now()
        return {
            "ok": True,
            "status": o["status"],
            "vendor_message": f"Order {order_id} accepted.",
            "customer_message": f"Your order {order_id} is confirmed and being processed.",
        }
    else:
        o["status"] = OrderStatus.REJECTED
        return {
            "ok": True,
            "status": o["status"],
            "vendor_message": f"Order {order_id} rejected.",
            "customer_message": "Unfortunately, your order could not be completed.",
        }


@mcp.tool(description="Mark an accepted order as ready for pickup/delivery.")
def order_ready(order_id: Annotated[str, Field(description="Order ID to mark as ready.")]) -> Dict:
    o = get_order(order_id)
    if not o:
        return {"ok": False, "error": "order_not_found"}
    error = validate_status(o, OrderStatus.ACCEPTED)
    if error:
        return {"ok": False, "error": error}
    o["status"] = OrderStatus.READY
    o["ready_at"] = now()
    agents = [{"id": a["id"], "name": a["name"]} for a in delivery_agents.values()]
    return {
        "ok": True,
        "status": o["status"],
        "vendor_message": f"Order {order_id} is ready. Choose a delivery agent.",
        "delivery_agent_options": agents,
    }


@mcp.tool(description="Assign a delivery agent to a ready order.")
def delivery_assign(
    order_id: Annotated[str, Field(description="Order ID.")],
    agent_id: Annotated[str, Field(description="Delivery agent ID.")],
) -> Dict:
    o = get_order(order_id)
    if not o:
        return {"ok": False, "error": "order_not_found"}
    error = validate_status(o, OrderStatus.READY)
    if error:
        return {"ok": False, "error": error}
    agent = delivery_agents.get(agent_id)
    if not agent:
        return {"ok": False, "error": "agent_not_found"}
    o["status"] = OrderStatus.ASSIGNED
    o["assigned_at"] = now()
    o["delivery_agent"] = agent
    return {
        "ok": True,
        "status": o["status"],
        "vendor_message": f"Agent {agent['name']} assigned to order {order_id}.",
        "agent_instructions": {
            "to_agent": {
                "message": f"Please pick up order {order_id} and deliver to {o['customer']['name']} at {o['address']}."
            }
        },
    }


@mcp.tool(description="Simulate requesting payment for an order.")
def payment_request(
    order_id: Annotated[str, Field(description="Order ID to request payment for.")],
    amount: Annotated[Optional[float], Field(description="Amount to request.")] = None,
    currency: str = "INR",
) -> Dict:
    o = get_order(order_id)
    if not o:
        return {"ok": False, "error": "order_not_found"}
    if o["status"] not in [OrderStatus.ASSIGNED, OrderStatus.DELIVERED]:
        return {"ok": False, "error": "Can only request payment for assigned or delivered orders."}
    o["payment_status"] = PaymentStatus.REQUESTED
    return {
        "ok": True,
        "vendor_message": f"Payment request sent for order {order_id}.",
    }


@mcp.tool(description="Mark an order as delivered.")
def order_delivered(order_id: Annotated[str, Field(description="Order ID.")]) -> Dict:
    o = get_order(order_id)
    error = validate_status(o, OrderStatus.ASSIGNED) if o else "order_not_found"
    if error:
        return {"ok": False, "error": error}
    o["status"] = OrderStatus.DELIVERED
    o["delivered_at"] = now()
    return {"ok": True, "status": o["status"]}


@mcp.tool(description="Mark an order as paid.")
def order_paid(order_id: Annotated[str, Field(description="Order ID.")]) -> Dict:
    o = get_order(order_id)
    if not o or o["payment_status"] != PaymentStatus.REQUESTED:
        return {"ok": False, "error": "Order not found or payment not requested."}
    o["payment_status"] = PaymentStatus.PAID
    o["status"] = OrderStatus.PAID
    o["paid_at"] = now()
    return {"ok": True, "status": o["status"]}
