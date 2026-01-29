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
