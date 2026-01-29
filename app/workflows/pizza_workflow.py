"""
Pizza Order Workflow - 披萨订单流程编排

使用 Class-based Activity Interface 实现类型安全调用
"""

from datetime import timedelta
from temporalio import workflow

# 只导入 SDK Contracts
from app.domains.pizza.sdk import (
    # Activity Interface
    PizzaActivities,
    # DTOs
    PizzaOrder,
    Receipt,
)


@workflow.defn
class PizzaOrderWorkflow:
    """披萨订单工作流
    
    流程步骤:
    1. 计算账单
    2. 处理支付
    3. 安排配送
    """
    
    @workflow.run
    async def run(self, order: PizzaOrder) -> Receipt:
        """运行披萨订单流程"""
        workflow.logger.info(f"[Workflow] Starting order for {order.customer_name}")
        
        # 步骤 1: 计算账单
        # 传入接口类的方法 (Unbound Method)，Temporal SDK 会提取元数据
        bill = await workflow.execute_activity(
            PizzaActivities.calculate_bill, 
            order,
            start_to_close_timeout=timedelta(seconds=5)
        )
        workflow.logger.info(f"[Workflow] Bill Total: ${bill.total_amount}")
        
        # 步骤 2: 处理支付
        paid = await workflow.execute_activity(
            PizzaActivities.charge_credit_card,
            bill,
            start_to_close_timeout=timedelta(seconds=10)
        )
        if not paid:
            workflow.logger.error("[Workflow] Payment failed")
            raise ValueError("Payment failed!")
        workflow.logger.info("[Workflow] Payment successful")
        
        # 步骤 3: 安排配送
        delivery_address = await workflow.execute_activity(
            PizzaActivities.process_delivery,
            order,
            start_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"[Workflow] Delivery to: {delivery_address}")
        
        # 返回收据
        return Receipt(
            order_id=order.order_id,
            status="COMPLETED",
            message="Bon Appetit!",
            delivered_to=delivery_address
        )


