from datetime import datetime
from sqlalchemy.orm import Session
from app.models.crm import Customer, Order, Account

def reset_password(customer_id: str, db: Session) -> dict:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {"success": False, "message": f"Customer {customer_id} not found"}
    account = db.query(Account).filter(Account.customer_id == customer_id).first()
    if account:
        account.last_reset_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": f"Password reset link sent to {customer.email}"}

def issue_refund(order_id: str, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "message": f"Order {order_id} not found"}
    if order.status == "refunded":
        return {"success": False, "message": "Order already refunded"}
    order.status = "refunded"
    db.commit()
    return {"success": True, "message": f"Refund of ${order.amount} issued for order {order_id}"}

def update_account(customer_id: str, notes: str, db: Session) -> dict:
    account = db.query(Account).filter(Account.customer_id == customer_id).first()
    if not account:
        account = Account(customer_id=customer_id, notes=notes)
        db.add(account)
    else:
        account.notes = notes
    db.commit()
    return {"success": True, "message": "Account updated"}

def check_order(order_id: str, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "message": f"Order {order_id} not found"}
    return {
        "success": True,
        "order_id": order_id,
        "product": order.product,
        "amount": order.amount,
        "status": order.status,
    }

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Send a password reset link to the customer's email",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Refund a specific order",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_account",
            "description": "Update notes or metadata on a customer account",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["customer_id", "notes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_order",
            "description": "Look up status and details of an order",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "reset_password": reset_password,
    "issue_refund": issue_refund,
    "update_account": update_account,
    "check_order": check_order,
}
