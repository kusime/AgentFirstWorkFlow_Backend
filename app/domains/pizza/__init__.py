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
_impl = PizzaActivitiesImpl()

# 自动发现所有带有 @activity.defn 装饰器的方法 (Reflection)
# 避免手动维护 activities 列表
activities = [
    method for _, method in inspect.getmembers(_impl, predicate=inspect.ismethod)
    if hasattr(method, "__temporal_activity_definition")
]
TASK_QUEUE = "pizza-task-queue"
