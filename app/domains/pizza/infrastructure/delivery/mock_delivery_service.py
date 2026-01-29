"""
Mock Delivery Service Implementation - 配送服务模拟实现

实现 IDeliveryService 接口，模拟真实的配送服务。
实际项目中会集成第三方配送平台 API。
"""

import asyncio
from app.domains.pizza.services import IDeliveryService
from app.domains.pizza.sdk.contracts import PizzaOrder


class MockDeliveryService(IDeliveryService):
    """模拟配送服务（用于演示和测试）"""
    
    async def schedule_delivery(self, order: PizzaOrder) -> str:
        """模拟安排配送
        
        Args:
            order: 订单信息
            
        Returns:
            格式化的配送地址
        """
        # 模拟处理延迟
        await asyncio.sleep(0.1)
        
        # 格式化地址
        address = order.delivery_address
        full_address = f"{address.street}, {address.city}, {address.zip_code}"
        
        print(f"[MockDelivery] Scheduled delivery to: {full_address}")
        
        # 实际实现示例：
        # delivery_response = await delivery_api.create_delivery(
        #     address=full_address,
        #     customer_name=order.customer_name,
        #     ...
        # )
        # return delivery_response.tracking_url
        
        return full_address
    
    async def track_delivery(self, order_id: str) -> dict:
        """模拟追踪配送状态"""
        await asyncio.sleep(0.1)
        return {
            "order_id": order_id,
            "status": "IN_TRANSIT",
            "eta": "30 minutes"
        }


# TODO: 实际项目中的第三方配送服务集成示例
# class UberDeliveryService(IDeliveryService):
#     def __init__(self, api_key: str):
#         self.client = uber_client.Client(api_key)
#     
#     async def schedule_delivery(self, order: PizzaOrder) -> str:
#         response = await self.client.create_delivery(...)
#         return response.tracking_url
