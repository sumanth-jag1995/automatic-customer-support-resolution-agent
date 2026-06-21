import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import SessionLocal
from app.models.crm import Customer, Order, Account
from app.models.kb import KBArticle
from app.rag.embeddings import embed

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

        logger.info("Step 4: Inserting KB articles (this may take 30-60s)...")
        articles = [
            ("Password Reset Guide", "To reset your password, go to Settings > Security > Reset Password. A link will be emailed to you. Links expire in 24 hours.", "authentication"),
            ("Refund Policy", "Refunds are available within 30 days of purchase. To request a refund, provide your order ID. Refunds take 3-5 business days.", "billing"),
            ("Account Locked", "Accounts are locked after 5 failed login attempts. Contact support or wait 30 minutes. Admins can unlock via the admin panel.", "authentication"),
            ("Billing FAQ", "We accept Visa, Mastercard, and PayPal. Invoices are sent monthly. To update payment details, go to Billing > Payment Methods.", "billing"),
            ("API Rate Limits", "Free tier: 100 req/min. Pro: 1000 req/min. Enterprise: unlimited. Rate limit headers are included in each response.", "technical"),
            ("Two-Factor Authentication", "Enable 2FA in Settings > Security. We support TOTP apps (Authenticator, Authy). Backup codes are provided at setup.", "authentication"),
            ("Data Export", "You can export all your data from Settings > Privacy > Export Data. Exports are ready within 24 hours and available for 7 days.", "general"),
            ("Cancel Subscription", "To cancel, go to Billing > Subscription > Cancel. You keep access until the end of the billing period. No refunds for partial months.", "billing"),
        ]

        db.execute(text("DELETE FROM kb_articles"))
        for i, (title, body, category) in enumerate(articles):
            logger.info(f"  Embedding article {i+1}/8: {title}")
            vec = embed(f"{title} {body}")
            article = KBArticle(title=title, body=body, category=category, embedding=vec)
            db.add(article)
        db.commit()
        logger.info("✓ KB articles inserted")

        logger.info("Database seed completed successfully!")
        return {"status": "success", "message": "Database seeded with sample data"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
