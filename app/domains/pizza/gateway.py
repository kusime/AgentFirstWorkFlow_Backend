"""
Pizza Domain Gateway - Activity定义层

实现Temporal Activities，调用Usecases执行业务逻辑。

重要：
- Activity名称从SDK常量中获取（单一真相源）
- 函数名可以自由命名，不需要匹配常量
- 使用 @activity.defn(name=CONSTANT) 显式指定名称
"""

from temporalio import activity


from app.domains.pizza.sdk import (
    # Activity Interface
    PizzaActivities,
    # Activity 名称常量（单一真相源）
    ACTIVITY_CALCULATE_BILL,
    ACTIVITY_CHARGE_CREDIT_CARD,
    ACTIVITY_PROCESS_DELIVERY,
    # DTOs
    PizzaOrder,
    Bill,
)

# 导入 Usecases
from app.domains.pizza.usecases import (
    CalculateBillUseCase,
    ProcessPaymentUseCase,
    ArrangeDeliveryUseCase,
)

# 导入 Infrastructure 实现（用于依赖注入）
from app.domains.pizza.infrastructure.payment.mock_payment_gateway import MockPaymentGateway
from app.domains.pizza.infrastructure.delivery.mock_delivery_service import MockDeliveryService


# ============================================================================
# Activity 实现 (Class-based Gateway)
# ============================================================================
class PizzaActivitiesImpl(PizzaActivities):
    """
    Pizza Domain Activity 的具体实现。
    显式继承 Contracts 中的接口契约。
    使用依赖注入初始化 UseCases。
    """
    
    def __init__(
        self,
        calculate_bill_usecase: CalculateBillUseCase,
        payment_usecase: ProcessPaymentUseCase,
        delivery_usecase: ArrangeDeliveryUseCase,
    ):
        """
        Args:
            calculate_bill_usecase: 计算账单 UseCase (依赖注入)
            payment_usecase: 支付 UseCase (依赖注入)
            delivery_usecase: 配送 UseCase (依赖注入)
        """
        self.calculate_bill_usecase = calculate_bill_usecase
        self.payment_usecase = payment_usecase
        self.delivery_usecase = delivery_usecase

    @activity.defn(name=ACTIVITY_CALCULATE_BILL)
    async def calculate_bill(self, order: PizzaOrder) -> Bill:
        """计算订单账单"""
        activity.logger.info(f"Calculating bill for order {order.order_id}")
        return self.calculate_bill_usecase.execute(order)

    @activity.defn(name=ACTIVITY_CHARGE_CREDIT_CARD)
    async def charge_credit_card(self, bill: Bill) -> bool:
        """处理支付"""
        activity.logger.info(f"Charging ${bill.total_amount} for order {bill.order_id}")
        try:
            return await self.payment_usecase.execute(bill)
        except ValueError:
            return False

    @activity.defn(name=ACTIVITY_PROCESS_DELIVERY)
    async def process_delivery(self, order: PizzaOrder) -> str:
        """安排配送"""
        activity.logger.info(f"Processing delivery for order {order.order_id}")
        return await self.delivery_usecase.execute(order)

