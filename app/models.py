# app/models.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    last_name = Column(String)
    prefix = Column(String, nullable=True)
    suffix = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
