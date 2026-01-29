"""
Pizza Repository Implementation - 数据库存储实现

实现 IPizzaRepository 接口，负责订单的持久化存储。
这里使用内存存储作为演示，实际项目中会连接真实数据库。
"""

from typing import Dict
from app.domains.pizza.services import IPizzaRepository
from app.domains.pizza.sdk.contracts import PizzaOrder


class InMemoryPizzaRepository(IPizzaRepository):
    """内存存储的 Pizza Repository 实现（用于演示）"""
    
    def __init__(self):
        self._storage: Dict[str, PizzaOrder] = {}
        self._status: Dict[str, str] = {}
    
    async def save_order(self, order: PizzaOrder) -> None:
        """保存订单到内存"""
        self._storage[order.order_id] = order
        self._status[order.order_id] = "CREATED"
    
    async def get_order(self, order_id: str) -> PizzaOrder:
        """从内存获取订单"""
        if order_id not in self._storage:
            raise ValueError(f"Order {order_id} not found")
        return self._storage[order_id]
    
    async def update_order_status(self, order_id: str, status: str) -> None:
        """更新订单状态"""
        if order_id not in self._storage:
            raise ValueError(f"Order {order_id} not found")
        self._status[order_id] = status


# TODO: 实际项目中的 SQLAlchemy 实现示例
# class SQLAlchemyPizzaRepository(IPizzaRepository):
#     def __init__(self, session: AsyncSession):
#         self.session = session
#     
#     async def save_order(self, order: PizzaOrder) -> None:
#         db_order = OrderModel(**order.dict())
#         self.session.add(db_order)
#         await self.session.commit()
#     ...
