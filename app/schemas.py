# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class CustomerBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    email: EmailStr
    phone_number: str

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

    class Config:
        orm_mode = True
