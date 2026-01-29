# Project Context: app

This document contains the source code for the project.

## File: `app/domains/pizza/__init__.py`

```python
"""
Pizza Domain - 领域模块导出

导出 Pizza Domain 的公共 API，供 Worker 注册使用。
- WORKFLOW_CLASSES: Workflow类列表（可以为空，workflow可以跨domain）
- activities: Activity函数列表
- TASK_QUEUE: 任务队列名称

设计理念：
- Domain专注于提供activities（业务能力）
- Workflow是独立的业务流程编排，可能跨多个domain
- 如果某个workflow恰好只使用一个domain的activities，可以在这里声明关联
- 但workflow的管理应该独立于domain
"""

from app.domains.pizza.gateway import PizzaActivitiesImpl
    
# Worker 注册所需的导出（约定）
# WORKFLOW_CLASSES 留空，由 worker 根据 domain 名称自动查找
WORKFLOW_CLASSES = []  # Worker will dynamically import from app.workflows.pizza_workflow

import inspect

# 实例化 Gateway
# ============================================================================
# Composition Root (依赖注入组装)
# ============================================================================
import os
from app.domains.pizza.usecases import (
    CalculateBillUseCase,
    ProcessPaymentUseCase,
    ArrangeDeliveryUseCase,
)
from app.domains.pizza.infrastructure.payment.mock_payment_gateway import MockPaymentGateway
from app.domains.pizza.infrastructure.delivery.mock_delivery_service import MockDeliveryService

# 1. 识别环境
ENV = os.getenv("ENV", "DEV")

# 2. 实例化 Infrastructure Implementations
if ENV == "PROD":
    # PROD 环境下使用真实的实现 (示例，目前留空 placeholders)
    # from app.domains.pizza.infrastructure.payment.stripe_gateway import StripePaymentGateway
    # from app.domains.pizza.infrastructure.delivery.uber_delivery import UberDeliveryService
    # payment_gateway = StripePaymentGateway(...)
    # delivery_service = UberDeliveryService(...)
    # 目前Fallback到Mock避免运行错误
    print(f"[PizzaDomain] Initializing in PROD mode (using Mock for demo)")
    payment_gateway = MockPaymentGateway()
    delivery_service = MockDeliveryService()
else:
    print(f"[PizzaDomain] Initializing in {ENV} mode (using Mocks)")
    payment_gateway = MockPaymentGateway()
    delivery_service = MockDeliveryService()

# 3. 实例化 UseCases (注入 Infrastructure)
calculate_bill_usecase = CalculateBillUseCase()
payment_usecase = ProcessPaymentUseCase(payment_gateway)
delivery_usecase = ArrangeDeliveryUseCase(delivery_service)

# 4. 实例化 Gateway (注入 UseCases)
_impl = PizzaActivitiesImpl(
    calculate_bill_usecase=calculate_bill_usecase,
    payment_usecase=payment_usecase,
    delivery_usecase=delivery_usecase,
)

# 自动发现所有带有 @activity.defn 装饰器的方法 (Reflection)
# 避免手动维护 activities 列表
activities = [
    method for _, method in inspect.getmembers(_impl, predicate=inspect.ismethod)
    if hasattr(method, "__temporal_activity_definition")
]
TASK_QUEUE = "pizza-task-queue"
```

---

## File: `app/domains/pizza/gateway.py`

```python
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

```

---

## File: `app/domains/pizza/usecases.py`

```python
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
```

---

## File: `app/domains/pizza/sdk/__init__.py`

```python
"""
Pizza Domain SDK - 对外暴露的契约层

导出：
- Activity名称常量
- DTOs
"""

from app.domains.pizza.sdk.contracts import (
    # Activity 名称常量
    ACTIVITY_CALCULATE_BILL,
    ACTIVITY_CHARGE_CREDIT_CARD,
    ACTIVITY_PROCESS_DELIVERY,
    # DTOs
    Address,
    PizzaItem,
    PizzaOrder,
    Bill,
    Receipt,
    # Activity Interface
    PizzaActivities,
)

__all__ = [
    # Activity 名称常量
    "ACTIVITY_CALCULATE_BILL",
    "ACTIVITY_CHARGE_CREDIT_CARD",
    "ACTIVITY_PROCESS_DELIVERY",
    # DTOs
    "Address",
    "PizzaItem",
    "PizzaOrder",
    "Bill",
    "Receipt",
    # Activity Interface
    "PizzaActivities",
]
```

---

## File: `app/domains/pizza/sdk/contracts.py`

```python
"""
Pizza Domain SDK - 对外暴露的契约层

包含：
1. DTOs - 数据传输对象
2. Activity名称常量 - **单一真相源**

不包含：
- Activity接口类（已删除）
- 具体实现（在gateway.py中）
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from temporalio import activity


# ============================================================================
# Activity 名称常量 - 单一真相源
# ============================================================================
# 这是定义activity名称的唯一位置
# Gateway 使用这些常量：@activity.defn(name=CONSTANT)
# Workflow 使用这些常量：workflow.execute_activity(CONSTANT, ...)

ACTIVITY_CALCULATE_BILL = "calculate_bill"
ACTIVITY_CHARGE_CREDIT_CARD = "charge_credit_card"
ACTIVITY_PROCESS_DELIVERY = "process_delivery"



# ============================================================================
# DTOs - 数据传输对象
# ============================================================================

# --- Order相关 ---

class Address(BaseModel):
    """配送地址"""
    street: str
    city: str
    zip_code: str


class PizzaItem(BaseModel):
    """披萨条目"""
    flavor: str
    size: str = Field(..., description="Size: S, M, L")
    quantity: int = Field(gt=0, description="Quantity must be positive")


class PizzaOrder(BaseModel):
    """披萨订单"""
    order_id: str
    customer_name: str
    items: List[PizzaItem]
    delivery_address: Address
    is_vip: bool = False


# --- Billing相关 ---

class Bill(BaseModel):
    """账单"""
    order_id: str
    total_amount: float
    currency: str = "USD"


# --- Delivery相关 ---

class Receipt(BaseModel):
    """收据"""
    order_id: str
    status: str
    message: str
    delivered_to: str

# ============================================================================
# Activity Interfaces (Stubs)
# ============================================================================
# 这些接口类用于在 Workflow 中提供类型提示和自动序列化支持。
# 它们不应该包含具体的业务逻辑实现。



# ============================================================================
# Activity Interface (Class-based)
# ============================================================================
class PizzaActivities:
    """Pizza Domain Activity 接口定义 (契约)"""
    
    @activity.defn(name=ACTIVITY_CALCULATE_BILL)
    async def calculate_bill(self, order: PizzaOrder) -> Bill:
        """计算账单"""
        ...

    @activity.defn(name=ACTIVITY_CHARGE_CREDIT_CARD)
    async def charge_credit_card(self, bill: Bill) -> bool:
        """扣款"""
        ...

    @activity.defn(name=ACTIVITY_PROCESS_DELIVERY)
    async def process_delivery(self, order: PizzaOrder) -> str:
        """安排配送"""
        ...

```

---

## File: `app/domains/pizza/infrastructure/__init__.py`

```python
"""
Pizza Domain Infrastructure

这个包包含所有外部服务接口的具体实现，按技术分类组织：
- db/: 数据库相关实现
- payment/: 支付网关实现  
- delivery/: 配送服务实现
"""
```

---

## File: `app/domains/pizza/infrastructure/db/__init__.py`

```python
"""DB Infrastructure Package"""
```

---

## File: `app/domains/pizza/infrastructure/db/pizza_repository.py`

```python
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
```

---

## File: `app/domains/pizza/infrastructure/payment/__init__.py`

```python
"""Payment Infrastructure Package"""
```

---

## File: `app/domains/pizza/infrastructure/payment/mock_payment_gateway.py`

```python
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
```

---

## File: `app/domains/pizza/infrastructure/delivery/__init__.py`

```python
"""Delivery Infrastructure Package"""
```

---

## File: `app/domains/pizza/infrastructure/delivery/mock_delivery_service.py`

```python
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
```

---

## File: `app/domains/pizza/services/__init__.py`

```python
"""
Pizza Domain Services - 服务接口定义层

这个包包含Pizza领域的所有服务接口定义（纯接口，无实现）。
按照职责分离原则，每个接口放在独立的文件中。

设计原则：
- 只定义接口，不包含实现
- 不导入infrastructure具体实现
- 可以被usecases安全导入
"""

from app.domains.pizza.services.repository import IPizzaRepository
from app.domains.pizza.services.payment import IPaymentGateway
from app.domains.pizza.services.delivery import IDeliveryService
from app.domains.pizza.services.notification import INotificationService

__all__ = [
    "IPizzaRepository",
    "IPaymentGateway",
    "IDeliveryService",
    "INotificationService",
]
```

---

## File: `app/domains/pizza/services/delivery.py`

```python
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
```

---

## File: `app/domains/pizza/services/notification.py`

```python
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
```

---

## File: `app/domains/pizza/services/payment.py`

```python
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
```

---

## File: `app/domains/pizza/services/repository.py`

```python
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
```

---

## File: `app/infrastructure/workflows/__init__.py`

```python
"""Infrastructure Workflows Package - Temporal Worker 相关组件"""
```

---

## File: `app/infrastructure/workflows/config.py`

```python
import os
from typing import Optional

class WorkerConfig:
    @property
    def temporal_host(self) -> str:
        return os.getenv("TEMPORAL_HOST", "localhost:7233")
    
    @property
    def enabled_domains(self) -> list[str]:
        """
        Returns a list of python module paths to load as domains.
        Example Env: ENABLE_DOMAINS="app.domains.pizza,app.domains.hello"
        """
        raw = os.getenv("ENABLE_DOMAINS", "")
        if not raw:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

config = WorkerConfig()
```

---

## File: `app/infrastructure/workflows/converter.py`

```python
import json
from typing import Any, Optional, Type
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DefaultPayloadConverter,
    EncodingPayloadConverter,
    PayloadConverter,
)
from pydantic import BaseModel

class PydanticJSONPayloadConverter(EncodingPayloadConverter):
    """
    A custom payload converter that handles Pydantic models.
    It serializes them to JSON and deserializes them back to the specific Pydantic model class.
    """
    
    @property
    def encoding(self) -> str:
        # We use a custom encoding tag to distinguish this from standard JSON
        return "json/pydantic"

    def to_payload(self, value: Any) -> Optional[Payload]:
        """Convert a Pydantic object to a Temporal Payload."""
        if isinstance(value, BaseModel):
            # Serialize Pydantic model to JSON string
            json_str = value.model_dump_json() if hasattr(value, "model_dump_json") else value.json()
            return Payload(
                metadata={"encoding": self.encoding.encode("utf-8")},
                data=json_str.encode("utf-8"),
            )
        return None

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        """Convert a Pydantic JSON payload back to a Pydantic object."""
        # 只处理我们自己编码的payload（"json/pydantic"）
        payload_encoding = payload.metadata.get("encoding", b"").decode("utf-8")
        if payload_encoding != self.encoding:
            return None  # 让其他converter处理
            
        data_str = payload.data.decode("utf-8")
        
        # 如果有type hint且是BaseModel，使用它
        if type_hint and issubclass(type_hint, BaseModel):
            return type_hint.model_validate_json(data_str) if hasattr(type_hint, "model_validate_json") else type_hint.parse_raw(data_str)
        
        # 没有type hint时，返回dict（但这不应该发生在正确配置的workflow中）
        return json.loads(data_str)


class PydanticDataConverter(CompositePayloadConverter):
    """
    The main DataConverter to use in Client and Worker.
    It includes the standard converters PLUS our custom Pydantic one.
    Important: The Pydantic converter must come BEFORE the default JSON converter.
    """
    def __init__(self):
        super().__init__(
            # Start with our custom Pydantic converter
            PydanticJSONPayloadConverter(),
            # Include all default converters (Binary, Protobuf, JSON, etc.)
            *DefaultPayloadConverter.default_encoding_payload_converters,
        )
```

---

## File: `app/infrastructure/workflows/worker.py`

```python
import asyncio
import importlib
from typing import List
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.converter import DataConverter

from app.infrastructure.workflows.config import config
from app.infrastructure.workflows.converter import PydanticDataConverter

async def main():
    print(f"Connecting to Temporal Server at {config.temporal_host}...")
    
    client = await Client.connect(
        config.temporal_host,
        data_converter=DataConverter(payload_converter_class=PydanticDataConverter),
    )

    enabled_domains = config.enabled_domains
    workers = []

    print(f"Starting Worker for Domains: {enabled_domains}")

    if not enabled_domains:
        print("Warning: No domains enabled! Set ENABLE_DOMAINS env var.")
        return

    # 导入workflow注册表
    from app.workflows import get_workflows_by_queue
    workflows_by_queue = get_workflows_by_queue()
    
    print(f"Loaded {len(workflows_by_queue)} workflow queues from registry")

    # 步骤1: 从domains收集activities（按task_queue分组）
    activities_by_queue = {}
    
    for domain_path in enabled_domains:
        try:
            print(f"  - Loading Domain: '{domain_path}'...")
            module = importlib.import_module(domain_path)
            
            activities = getattr(module, 'activities', [])
            task_queue = getattr(module, 'TASK_QUEUE', None)
            
            if not task_queue:
                print(f"    [ERROR] Domain '{domain_path}' missing TASK_QUEUE. Skipping.")
                continue
            
            if not activities:
                print(f"    [WARN] Domain '{domain_path}' has no activities.")
                continue
            
            # 按task_queue收集activities
            if task_queue not in activities_by_queue:
                activities_by_queue[task_queue] = []
            activities_by_queue[task_queue].extend(activities)
            
            print(f"    [SUCCESS] Registered {len(activities)} activities to '{task_queue}'")
            
        except ImportError as e:
            print(f"    [ERROR] Failed to import domain '{domain_path}': {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"    [ERROR] Unexpected error loading '{domain_path}': {e}")
            import traceback
            traceback.print_exc()

    # 步骤2: 合并workflows和activities，为每个task_queue创建worker
    all_queues = set(workflows_by_queue.keys()) | set(activities_by_queue.keys())
    
    for task_queue in all_queues:
        workflow_classes = workflows_by_queue.get(task_queue, [])
        activities = activities_by_queue.get(task_queue, [])
        
        
        if not workflow_classes and not activities:
            print(f"  [SKIP] Queue '{task_queue}' has no workflows or activities")
            continue
        
        print(f"  [WORKER] Creating worker for '{task_queue}': {len(workflow_classes)} workflows, {len(activities)} activities")
        
        # Worker会从Client继承data_converter配置
        workers.append(
            Worker(
                client,
                task_queue=task_queue,
                workflows=workflow_classes,
                activities=activities,
            )
        )



    if not workers:
        print("Error: No workers were successfully registered.")
        return

    # Run all registered workers concurrently
    print(f"Worker process running with {len(workers)} active worker instances...")
    await asyncio.gather(*[w.run() for w in workers])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker stopped by user.")
```

---

## File: `app/workflows/__init__.py`

```python
"""
Business Workflows

这个包包含所有的业务流程编排（Workflow）定义。
- Workflow 只能导入 domains/*/sdk/contracts.py 获取 DTO 和 Activity 接口
- 禁止直接导入 gateway.py 的 activity 函数

Workflow注册：
- Workflows是独立的业务流程编排，可能跨多个domains
- 使用WORKFLOW_REGISTRY集中管理所有workflows
"""

from app.workflows.pizza_workflow import PizzaOrderWorkflow

# Workflow注册表：workflow_class → task_queue映射
WORKFLOW_REGISTRY = {
    PizzaOrderWorkflow: "pizza-task-queue",
    # 未来示例:
    # ComplexOrderWorkflow: "pizza-task-queue",      # 复杂订单流程
    # CrossDomainWorkflow: "multi-domain-queue",     # 跨domain workflow
}

def get_workflows_by_queue():
    """根据task_queue分组workflows（Worker使用）"""
    queue_map = {}
    for workflow_class, task_queue in WORKFLOW_REGISTRY.items():
        if task_queue not in queue_map:
            queue_map[task_queue] = []
        queue_map[task_queue].append(workflow_class)
    return queue_map
```

---

## File: `app/workflows/pizza_workflow.py`

```python
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


```

---

