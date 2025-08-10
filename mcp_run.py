from typing import Annotated, List, Dict
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os
from dotenv import load_dotenv
PORT = int(os.environ.get("PORT", 8085))

load_dotenv()


TOKEN = os.getenv("MCP_TOKEN")
MY_NUMBER = os.getenv("WHATSAPP_NUMBER")

# Database with Manglore FishMonger's complete menu
business_db = {
    "manglore_fishmonger": {
        "name": "Manglore FishMonger",
        "owner": "Rajesh Pai",
        "contact": "+919876543210",
        "location": "Fish Market Road, Mangalore, Karnataka 575001",
        "menu": {
            "Seer Fish (Surmai)": {"price": 800, "unit": "kg", "available": True},
            "Pomfret (White)": {"price": 650, "unit": "kg", "available": True},
            "Pomfret (Black)": {"price": 550, "unit": "kg", "available": True},
            "Sardines (Tarle)": {"price": 200, "unit": "kg", "available": True},
            "Mackerel (Bangda)": {"price": 300, "unit": "kg", "available": True},
            "Kingfish (Viswon)": {"price": 700, "unit": "kg", "available": False},
            "Silver Fish (Kane)": {"price": 400, "unit": "kg", "available": True},
            "Pearl Spot (Karimeen)": {"price": 900, "unit": "kg", "available": True},
            "Tiger Prawns": {"price": 1200, "unit": "kg", "available": True},
            "White Prawns": {"price": 1000, "unit": "kg", "available": True},
            "Crabs (Medium)": {"price": 600, "unit": "kg", "available": True},
            "Squid": {"price": 500, "unit": "kg", "available": False},
            "Mussels": {"price": 250, "unit": "kg", "available": True},
            "Clams": {"price": 300, "unit": "kg", "available": True},
        },
        "orders": [],
    }
}

class SimpleBearerAuthProvider(BearerAuthProvider):
    """Simple authentication provider"""
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(
            public_key=k.public_key, jwks_uri=None, issuer=None, audience=None
        )
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="unknown",
                scopes=[],
                expires_at=None,
            )
        return None

class BusinessOrder(BaseModel):
    customer_name: str
    customer_contact: str
    items: Dict[str, float]
    special_instructions: str = ""
    timestamp: str = datetime.now().isoformat()

mcp = FastMCP(
    "Manglore FishMonger MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

@mcp.tool
async def validate() -> str:
    """Validation tool required by Puch"""
    return MY_NUMBER

@mcp.tool(description="Get today's menu. Usage: `/menu` or `/menu [item]` to search")
async def get_menu(item: str = None) -> dict:
    """
    Returns the full menu or searches for a specific item.
    Example: `/menu` or `/menu pomfret`
    """
    menu = business_db["manglore_fishmonger"]["menu"]
    
    if item:
        item_lower = item.lower()
        results = {
            name: details
            for name, details in menu.items()
            if item_lower in name.lower()
        }
        if not results:
            raise McpError(ErrorData(
                code=INVALID_PARAMS,
                message=f"No items found matching '{item}'"
            ))
        menu = results
    
    formatted_menu = [
        {
            "item": name,
            "price": f"₹{details['price']}/{details['unit']}",
            "status": "✅ Available" if details["available"] else "❌ Out of Stock"
        }
        for name, details in menu.items()
    ]
    
    return {
        "business": business_db["manglore_fishmonger"]["name"],
        "menu": formatted_menu,
        "contact": business_db["manglore_fishmonger"]["contact"],
        "note": "Use '/order [items]' to place an order. Example: '/order 1kg surmai, 2kg bangda'"
    }

@mcp.tool(description="Place an order. Usage: `/order [items]`. Example: `/order 1kg surmai, 2 prawns`")
async def place_order(
    customer_name: str,
    customer_contact: str,
    items: str,
    special_instructions: str = ""
) -> dict:
    """
    Places an order with Manglore FishMonger.
    Example: `/order 1kg surmai, 2 prawns - Name: John, Contact: +919876543210, Notes: Clean and cut`
    """
    business_id = "manglore_fishmonger"
    menu = business_db[business_id]["menu"]
    
    # Parse items (e.g., "1kg surmai, 2 prawns" → {"Seer Fish (Surmai)": 1, "Tiger Prawns": 2})
    parsed_items = {}
    errors = []
    
    for item_str in items.split(","):
        item_str = item_str.strip()
        if not item_str:
            continue
            
        # Handle both "1kg surmai" and "2 prawns" formats
        if "kg" in item_str:
            parts = item_str.split("kg", 1)
            qty = float(parts[0].strip())
            item_name = parts[1].strip()
        else:
            parts = item_str.split(" ", 1)
            qty = float(parts[0].strip())
            item_name = parts[1].strip()
        
        # Find matching menu item (case insensitive, partial match)
        matched_item = None
        for menu_item in menu.keys():
            if item_name.lower() in menu_item.lower():
                matched_item = menu_item
                break
                
        if not matched_item:
            errors.append(f"❌ '{item_name}' not found in menu")
            continue
            
        if not menu[matched_item]["available"]:
            errors.append(f"❌ '{matched_item}' is out of stock")
            continue
            
        parsed_items[matched_item] = qty
    
    if errors:
        raise McpError(ErrorData(
            code=INVALID_PARAMS,
            message="\n".join(errors)
        ))
    
    if not parsed_items:
        raise McpError(ErrorData(
            code=INVALID_PARAMS,
            message="No valid items in order"
        ))
    
    # Calculate total
    total = sum(
        menu[item]["price"] * qty
        for item, qty in parsed_items.items()
    )
    
    # Create and store order
    order = BusinessOrder(
        customer_name=customer_name,
        customer_contact=customer_contact,
        items=parsed_items,
        special_instructions=special_instructions
    )
    business_db[business_id]["orders"].append(order.model_dump())
    
    # Format order summary
    order_summary = [
        f"- {item}: {qty}{menu[item]['unit']} × ₹{menu[item]['price']} = ₹{menu[item]['price'] * qty}"
        for item, qty in parsed_items.items()
    ]
    
    return {
        "status": "✅ Order Placed Successfully!",
        "business": business_db[business_id]["name"],
        "contact": business_db[business_id]["contact"],
        "your_details": f"{customer_name} ({customer_contact})",
        "items": order_summary,
        "total": f"₹{total}",
        "instructions": special_instructions or "None",
        "next_steps": [
            "💰 Payment: Cash on delivery",
            "📞 You'll receive a confirmation call",
            "⏱️ Delivery within 2 hours"
        ]
    }

@mcp.tool(description="Get business location. Usage: `/location`")
async def get_location() -> dict:
    """Returns the business address and map link"""
    return {
        "business": business_db["manglore_fishmonger"]["name"],
        "address": business_db["manglore_fishmonger"]["location"],
        "map_link": "https://maps.app.goo.gl/EXAMPLE",  # Replace with actual Google Maps link
        "hours": "Open daily 6AM-8PM"
    }

@mcp.tool(description="Show help. Usage: `/help`")
async def show_help() -> dict:
    """Returns available commands"""
    return {
        "commands": [
            {"command": "/menu", "description": "Show full menu or search items"},
            {"command": "/order [items]", "description": "Place an order (e.g., /order 1kg surmai, 2 prawns)"},
            {"command": "/location", "description": "Get shop address and hours"},
            {"command": "/help", "description": "Show this help message"},
        ],
        "example_order": "/order 1kg surmai, 2 prawns - Name: John, Contact: +919876543210, Notes: Clean and cut"
    }

async def main():
    await mcp.run_async(
        "streamable-http",
        host="0.0.0.0",
        port=8085,
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())