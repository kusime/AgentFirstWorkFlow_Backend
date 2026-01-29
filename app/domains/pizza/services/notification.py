"""
Pizza Notification Service Interface - 通知服务接口
"""

from abc import ABC, abstractmethod
from app.domains.pizza.sdk import PizzaOrder


class INotificationService(ABC):
    """通知服务接口（可选，用于演示全局 infrastructure 的依赖反转）"""
    
    @abstractmethod
    async def send_order_confirmation(self, order: PizzaOrder) -> None:
        """发送订单确认通知"""
        pass
