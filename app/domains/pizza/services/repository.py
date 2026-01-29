"""
Pizza Repository Interface - 数据存储接口
"""

from abc import ABC, abstractmethod
from app.domains.pizza.sdk import PizzaOrder


class IPizzaRepository(ABC):
    """披萨订单存储接口"""
    
    @abstractmethod
    async def save_order(self, order: PizzaOrder) -> None:
        """保存订单"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> PizzaOrder:
        """获取订单"""
        pass
    
    @abstractmethod
    async def update_order_status(self, order_id: str, status: str) -> None:
        """更新订单状态"""
        pass
