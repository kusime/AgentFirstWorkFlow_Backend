from typing import List, Optional
from pydantic import BaseModel, Field

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class PizzaItem(BaseModel):
    flavor: str
    size: str  # S, M, L
    quantity: int = Field(gt=0, description="Quantity must be positive")

class PizzaOrder(BaseModel):
    order_id: str
    customer_name: str
    items: List[PizzaItem]
    delivery_address: Address
    is_vip: bool = False

class Bill(BaseModel):
    order_id: str
    total_amount: float
    currency: str = "USD"

class Receipt(BaseModel):
    order_id: str
    status: str
    message: str
    delivered_to: str
