"""
Pizza Domain SDK - 对外暴露的契约层

包含：
1. DTOs - 数据传输对象
2. Activity名称常量 - **单一真相源**

不包含：
- Activity接口类（已删除）
- 具体实现（在gateway.py中）
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from temporalio import activity


# ============================================================================
# Activity 名称常量 - 单一真相源
# ============================================================================
# 这是定义activity名称的唯一位置
# Gateway 使用这些常量：@activity.defn(name=CONSTANT)
# Workflow 使用这些常量：workflow.execute_activity(CONSTANT, ...)

ACTIVITY_CALCULATE_BILL = "calculate_bill"
ACTIVITY_CHARGE_CREDIT_CARD = "charge_credit_card"
ACTIVITY_PROCESS_DELIVERY = "process_delivery"



# ============================================================================
# DTOs - 数据传输对象
# ============================================================================

# --- Order相关 ---

class Address(BaseModel):
    """配送地址"""
    street: str
    city: str
    zip_code: str


class PizzaItem(BaseModel):
    """披萨条目"""
    flavor: str
    size: str = Field(..., description="Size: S, M, L")
    quantity: int = Field(gt=0, description="Quantity must be positive")


class PizzaOrder(BaseModel):
    """披萨订单"""
    order_id: str
    customer_name: str
    items: List[PizzaItem]
    delivery_address: Address
    is_vip: bool = False


# --- Billing相关 ---

class Bill(BaseModel):
    """账单"""
    order_id: str
    total_amount: float
    currency: str = "USD"


# --- Delivery相关 ---

class Receipt(BaseModel):
    """收据"""
    order_id: str
    status: str
    message: str
    delivered_to: str

# ============================================================================
# Activity Interfaces (Stubs)
# ============================================================================
# 这些接口类用于在 Workflow 中提供类型提示和自动序列化支持。
# 它们不应该包含具体的业务逻辑实现。



# ============================================================================
# Activity Interface (Class-based)
# ============================================================================
class PizzaActivities:
    """Pizza Domain Activity 接口定义 (契约)"""
    
    @activity.defn(name=ACTIVITY_CALCULATE_BILL)
    async def calculate_bill(self, order: PizzaOrder) -> Bill:
        """计算账单"""
        ...

    @activity.defn(name=ACTIVITY_CHARGE_CREDIT_CARD)
    async def charge_credit_card(self, bill: Bill) -> bool:
        """扣款"""
        ...

    @activity.defn(name=ACTIVITY_PROCESS_DELIVERY)
    async def process_delivery(self, order: PizzaOrder) -> str:
        """安排配送"""
        ...

