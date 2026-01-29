"""
Pizza Domain SDK - 对外暴露的契约层

导出：
- Activity名称常量
- DTOs
"""

from app.domains.pizza.sdk.contracts import (
    # Activity 名称常量
    ACTIVITY_CALCULATE_BILL,
    ACTIVITY_CHARGE_CREDIT_CARD,
    ACTIVITY_PROCESS_DELIVERY,
    # DTOs
    Address,
    PizzaItem,
    PizzaOrder,
    Bill,
    Receipt,
    # Activity Interface
    PizzaActivities,
)

__all__ = [
    # Activity 名称常量
    "ACTIVITY_CALCULATE_BILL",
    "ACTIVITY_CHARGE_CREDIT_CARD",
    "ACTIVITY_PROCESS_DELIVERY",
    # DTOs
    "Address",
    "PizzaItem",
    "PizzaOrder",
    "Bill",
    "Receipt",
    # Activity Interface
    "PizzaActivities",
]
