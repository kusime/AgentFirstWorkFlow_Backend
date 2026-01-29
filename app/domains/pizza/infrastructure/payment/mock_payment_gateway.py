"""
Mock Payment Gateway Implementation - 支付网关模拟实现

实现 IPaymentGateway 接口，模拟真实的支付网关行为。
实际项目中会集成 Stripe, PayPal 等真实支付服务。
"""

import asyncio
from app.domains.pizza.services import IPaymentGateway
from app.domains.pizza.sdk.contracts import Bill


class MockPaymentGateway(IPaymentGateway):
    """模拟支付网关（用于演示和测试）"""
    
    async def charge(self, bill: Bill) -> bool:
        """模拟扣款操作
        
        模拟网络延迟，始终返回成功。
        实际实现会调用真实支付API。
        """
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        print(f"[MockPayment] Charging ${bill.total_amount} for order {bill.order_id}")
        
        # 实际实现示例：
        # response = await stripe_client.charge(
        #     amount=int(bill.total_amount * 100),  # cents
        #     currency=bill.currency.lower(),
        #     ...
        # )
        # return response.status == "succeeded"
        
        return True  # 模拟成功
    
    async def refund(self, order_id: str, amount: float) -> bool:
        """模拟退款操作"""
        await asyncio.sleep(0.1)
        print(f"[MockPayment] Refunding ${amount} for order {order_id}")
        return True


# TODO: 实际项目中的 Stripe 实现示例
# class StripePaymentGateway(IPaymentGateway):
#     def __init__(self, api_key: str):
#         self.client = stripe_client.Client(api_key)
#     
#     async def charge(self, bill: Bill) -> bool:
#         try:
#             response = await self.client.charge(...)
#             return response.status == "succeeded"
#         except stripe.errors.CardError:
#             return False
