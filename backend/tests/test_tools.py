import pytest
from unittest.mock import MagicMock
from app.tools.crm_tools import reset_password, issue_refund, update_account, check_order

def test_reset_password_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = reset_password("cust_999", db)
    assert result["success"] is False
    assert "not found" in result["message"]

def test_reset_password_success():
    from app.models.crm import Customer, Account
    customer = MagicMock(spec=Customer)
    account = MagicMock(spec=Account)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [customer, account]
    result = reset_password("cust_1", db)
    assert result["success"] is True

def test_issue_refund_success():
    from app.models.crm import Order
    order = MagicMock(spec=Order)
    order.status = "completed"
    order.amount = 99.0
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = order
    result = issue_refund("ord_1", db)
    assert result["success"] is True
    assert order.status == "refunded"

def test_check_order_found():
    from app.models.crm import Order
    order = MagicMock(spec=Order)
    order.product = "Pro Plan"
    order.amount = 99.0
    order.status = "completed"
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = order
    result = check_order("ord_1", db)
    assert result["success"] is True
    assert result["product"] == "Pro Plan"
