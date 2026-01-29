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
