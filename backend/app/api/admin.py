import logging
from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.crm import Customer, Order, Account

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/seed")
def seed_database():
    """One-time endpoint to populate database with sample data."""
    db = SessionLocal()
    try:
        logger.info("Starting database seed...")
        logger.info("Step 1: Inserting customers...")
        customers = [
            Customer(id="cust_1", name="Alice Chen", email="alice@example.com", plan="pro", status="active"),
            Customer(id="cust_2", name="Bob Smith", email="bob@example.com", plan="free", status="active"),
            Customer(id="cust_3", name="Carol White", email="carol@example.com", plan="enterprise", status="active"),
        ]
        for c in customers:
            db.merge(c)
        db.commit()
        logger.info("✓ Customers inserted")

        logger.info("Step 2: Inserting orders...")
        orders = [
            Order(id="ord_1", customer_id="cust_1", product="Pro Plan", amount=99.0, status="completed"),
            Order(id="ord_2", customer_id="cust_2", product="Add-on Pack", amount=19.0, status="completed"),
            Order(id="ord_3", customer_id="cust_3", product="Enterprise Suite", amount=499.0, status="completed"),
        ]
        for o in orders:
            db.merge(o)
        db.commit()
        logger.info("✓ Orders inserted")

        logger.info("Step 3: Inserting accounts...")
        accounts = [Account(customer_id=c.id, notes="") for c in customers]
        for a in accounts:
            db.merge(a)
        db.commit()
        logger.info("✓ Accounts inserted")

        logger.info("Database seed completed successfully!")
        return {"status": "success", "message": "Customers, orders, and accounts seeded. (KB articles require manual seeding due to memory constraints)"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
