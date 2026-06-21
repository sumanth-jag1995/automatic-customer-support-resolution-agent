from sqlalchemy import Column, String, Float, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    plan = Column(String, default="free")
    status = Column(String, default="active")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False)
    product = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime, server_default=func.now())

class Account(Base):
    __tablename__ = "accounts"
    customer_id = Column(String, primary_key=True)
    password_reset_count = Column(String, default="0")
    last_reset_at = Column(DateTime)
    notes = Column(Text)
