"""
Pizza Domain Usecases - 纯业务逻辑

这个模块包含 Pizza Domain 的所有业务逻辑。
- 只依赖 services.py 中定义的接口，不依赖具体实现
- 不包含任何基础设施相关代码（DB、S3、HTTP 等）
- 可以进行单元测试而无需外部依赖
"""

from app.domains.pizza.sdk.contracts import PizzaOrder, Bill
from app.domains.pizza.services import IPaymentGateway, IDeliveryService, IPizzaRepository


class CalculateBillUseCase:
    """计算账单用例 - 纯计算逻辑，无外部依赖"""
    
    def execute(self, order: PizzaOrder) -> Bill:
        """根据订单计算账单
        
        Args:
            order: 披萨订单
            
        Returns:
            计算后的账单
        """
        # 计算总价
        total = 0.0
        for item in order.items:
            # 根据尺寸定价
            if item.size == "S":
                price = 10.0
            elif item.size == "M":
                price = 15.0
            else:  # L
                price = 20.0
            
            total += price * item.quantity
        
        # VIP 折扣
        if order.is_vip:
            total *= 0.8
        
        return Bill(
            order_id=order.order_id,
            total_amount=total,
            currency="USD"
        )


class ProcessPaymentUseCase:
    """处理支付用例 - 依赖支付网关接口"""
    
    def __init__(self, payment_gateway: IPaymentGateway):
        """
        Args:
            payment_gateway: 支付网关实现（依赖注入）
        """
        self.payment_gateway = payment_gateway
    
    async def execute(self, bill: Bill) -> bool:
        """处理支付
        
        Args:
            bill: 账单信息
            
        Returns:
            True 表示支付成功
            
        Raises:
            ValueError: 如果支付失败
        """
        success = await self.payment_gateway.charge(bill)
        
        if not success:
            raise ValueError(f"Payment failed for order {bill.order_id}")
        
        return success


class ArrangeDeliveryUseCase:
    """安排配送用例 - 依赖配送服务接口"""
    
    def __init__(self, delivery_service: IDeliveryService):
        """
        Args:
            delivery_service: 配送服务实现（依赖注入）
        """
        self.delivery_service = delivery_service
    
    async def execute(self, order: PizzaOrder) -> str:
        """安排订单配送
        
        Args:
            order: 订单信息
            
        Returns:
            配送地址的格式化字符串
        """
        delivery_address = await self.delivery_service.schedule_delivery(order)
        return delivery_address


class SaveOrderUseCase:
    """保存订单用例 - 依赖仓储接口"""
    
    def __init__(self, repository: IPizzaRepository):
        """
        Args:
            repository: 订单仓储实现（依赖注入）
        """
        self.repository = repository
    
    async def execute(self, order: PizzaOrder) -> None:
        """保存订单到存储
        
        Args:
            order: 订单信息
        """
        await self.repository.save_order(order)
