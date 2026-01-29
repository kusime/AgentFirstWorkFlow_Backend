"""
Pizza Delivery Service Interface - 配送服务接口
"""

from abc import ABC, abstractmethod
from app.domains.pizza.sdk import PizzaOrder


class IDeliveryService(ABC):
    """配送服务接口"""
    
    @abstractmethod
    async def schedule_delivery(self, order: PizzaOrder) -> str:
        """安排配送
        
        Args:
            order: 订单信息
            
        Returns:
            配送地址的格式化字符串
        """
        pass
    
    @abstractmethod
    async def track_delivery(self, order_id: str) -> dict:
        """追踪配送状态"""
        pass
