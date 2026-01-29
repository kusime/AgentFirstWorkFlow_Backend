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
