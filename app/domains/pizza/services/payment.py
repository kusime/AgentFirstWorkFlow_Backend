"""
Pizza Payment Gateway Interface - 支付网关接口
"""

from abc import ABC, abstractmethod
from app.domains.pizza.sdk import Bill


class IPaymentGateway(ABC):
    """支付网关接口"""
    
    @abstractmethod
    async def charge(self, bill: Bill) -> bool:
        """扣款
        
        Args:
            bill: 账单信息
            
        Returns:
            True 表示扣款成功，False 表示失败
        """
        pass
    
    @abstractmethod
    async def refund(self, order_id: str, amount: float) -> bool:
        """退款"""
        pass
