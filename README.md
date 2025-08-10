# Manglore FishMonger - WhatsApp Ordering System
🚀 A complete solution for fish vendors to manage orders via WhatsApp using MCP & Puch AI.

## 📌 Quick Start Guide
1. Connect to MCP Server
To start using the system, connect Puch to your MCP server:

text
```
/mcp use 1ceqtZUwWh
(Replace with your actual MCP server ID if self-hosted)
```


2. Available Commands for Customers
Command	Example	Description
/menu	/menu	View today's seafood menu
/order	/order 1kg surmai, 2 prawns - Name: John, Contact: +919876543210	Place an order
/location	/location	Get shop address & map link
/help	/help	Show all commands
### 🛠 Vendor (Admin) Features (Future Updates)
1. Update Menu (Vendor-Only)
Command:

text
```
/update_menu [item] [price] [status]  
```
### Example:

text
```
/update_menu surmai 850 available  
*(Updates Seer Fish price to ₹850/kg and marks it available)*
```

2. Accept/Reject Orders
Command:

text
/order_action [order_id] [accept/reject]  
Example:

text
/order_action 23 accept  
(Accepts order #23 and notifies customer via WhatsApp)

3. Assign Delivery Agent
Command:

text
/assign_delivery [order_id] [agent_phone]  
Example:

text
/assign_delivery 23 +919876543210  
(Assigns order #23 to delivery agent & shares customer details)

## ⚙ Setup & Deployment
1. For Customers
No setup needed! Just send commands to Puch in WhatsApp.

2. For Vendors (Self-Hosting)
Deploy on Render (Recommended):

bash
```
pip install -r requirements.txt
python business_server.py
```
Configure .env:

env
```
MCP_TOKEN=your_secret_token
WHATSAPP_NUMBER=your_number
```
Connect to Puch:

text
```
/mcp use YOUR_MCP_ID
```


## 🔮 Planned Features
✅ Payments Integration (UPI, Cash on Delivery)
✅ Order Tracking (/track_order [order_id])
✅ Inventory Alerts (Auto-notify when stock is low)
✅ Multi-Vendor Support (For fish market associations)


## 🐟 Happy Selling!
Powered by Puch AI & MCP<<<<<<< HEAD
