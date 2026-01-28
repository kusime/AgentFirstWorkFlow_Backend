# Temporal 架构设计与重构报告

## 1. 项目演进与重构背景

本项目（HoloAssetManagement）经历了从原本的“扁平化脚本堆叠”到现在的“领域驱动模块化架构”的彻底重构。

### 1.1 曾存在的问题
在重构之前，所有的 Workflow 和 Activity 都堆叠在 `workflows/` 根目录下。随着业务逻辑（Pizza, Login 等）的增加，我们遇到了以下痛点：
*   **代码耦合严重**：业务逻辑与 Temporal 基础设施代码混杂。
*   **注册逻辑僵化**：每次新增一个 Workflow，都需要手动修改 `run_worker.py`，导致 Worker 入口文件臃肿且难以维护。
*   **单点风险**：所有业务运行在同一个 Worker 进程中，一旦某个业务逻辑导致崩溃，整个系统都会停摆。
*   **部署不灵活**：无法针对高频业务（如 Pizza 订单）单独扩容。

### 1.2 重构目标
我们确立了以下架构目标：
1.  **高内聚低耦合**：采用 Clean Architecture / DDD 思想组织代码。
2.  **开闭原则 (OCP)**：新增业务领域时，**不需要修改**现有的 Worker 基础设施代码。
3.  **弹性伸缩**：支持物理层级的服务隔离与独立扩容。

---

## 2. 新架构：目录结构说明

重构后的项目结构清晰地分离了“业务域”与“基础设施域”：

```text
HoloAssetManagement/
├── app/                        # [核心应用源码]
│   ├── common/                 # 公共基础设施层
│   │   ├── config.py           # 配置管理 (读取环境变量)
│   │   └── converter.py        # Pydantic 数据转换器 (Infrastructure)
│   ├── domains/                # 业务领域层 (Domain Layer)
│   │   ├── hello/              # 示例领域
│   │   │   ├── activities.py   # 纯业务逻辑 (Business Logic)
│   │   │   ├── workflows.py    # 流程编排 (Orchestration)
│   │   │   └── __init__.py     # 领域导出 (Export Bundle)
│   │   └── pizza/              # 核心业务领域
│   │       ├── models.py       # 数据模型 (DTOs / Pydantic)
│   │       ├── ...
│   └── worker/                 # 接口层 (Interface Layer)
│       └── main.py             # 通用 Worker 启动器 (无需修改即可运行任何领域)
├── infrastructure/             # 运维配置
│   └── Dockerfile.worker       # 标准化 Worker 镜像构建文件
├── scripts/                    # 客户端脚本
│   ├── test_hello.py           # Hello 业务集成测试
│   └── test_pizza.py           # Pizza 业务集成测试
└── docker-compose.yml          # 容器编排 (定义隔离策略)
```

---

## 3. 核心设计模式

### 3.1 插件式 Worker 注册 (The Plugin Pattern)
这是本次重构最核心的技术突破。为了解耦 Worker 与具体业务，我们实现了**动态发现机制**。

*   **原理**：`app/worker/main.py` 不再硬编码 `import` 语句，而是通过 Python 的 `importlib` 动态加载模块。
*   **约定 (Convention)**：每个 Domain 的 `__init__.py` 必须导出以下变量：
    - `TASK_QUEUE`: 该领域监听的任务队列名称。
    - `workflows`: 该领域的 Workflow 类列表。
    - `activities`: 该领域的 Activity 函数列表。
*   **配置**：通过环境变量 `ENABLE_DOMAINS` 控制加载哪些插件。

### 3.2 容器化隔离策略 (Container Isolation)
利用上述的“插件模式”，我们可以在 `docker-compose.yml` 中定义多个**完全隔离**的服务，但使用**同一个 Docker 镜像**。

| 服务名称 (Service) | 环境变量 (`ENABLE_DOMAINS`) | 监听队列 | 隔离级别 |
| :--- | :--- | :--- | :--- |
| `worker-hello` | `app.domains.hello` | `hello-task-queue` | 物理隔离 (独立容器) |
| `worker-pizza` | `app.domains.pizza` | `pizza-task-queue` | 物理隔离 (独立容器) |

**优势**：
1.  **故障隔离**：Pizza 业务内存泄漏崩溃，绝不会影响 Hello 业务。
2.  **独立扩容**：如果 Pizza 订单量大，可以单独设置 `deploy: replicas: 10`，而保持 Hello 为 1。

### 3.3 领域驱动设计 (DDD) 与 类型安全
*   **模型分离**：使用 `Pydantic` 定义强类型的 DTO (Data Transfer Objects)，如 `PizzaOrder`。
*   **自动序列化**：实现了 `PydanticDataConverter`，确保复杂对象在 Temporal 传递过程中自动序列化为 JSON，取出时自动还原为对象。

---

## 4. 开发指南：如何新增一个业务？

得益于新架构，新增业务变得非常简单且规范。假设我们要新增一个 `Shipping`（物流）服务：

### 步骤 1：创建领域目录
```bash
mkdir -p app/domains/shipping
touch app/domains/shipping/{__init__.py,workflows.py,activities.py}
```

### 步骤 2：实现业务逻辑 (`activities.py`)
```python
from temporalio import activity
@activity.defn
async def ship_item(item_id: str) -> str:
    return f"Shipped {item_id}"
```

### 步骤 3：实现编排流程 (`workflows.py`)
```python
from temporalio import workflow
from .activities import ship_item
@workflow.defn
class ShippingWorkflow:
    @workflow.run
    async def run(self, item_id: str):
        return await workflow.execute_activity(ship_item, item_id, ...)
```

### 步骤 4：导出组件 (`__init__.py`)
```python
from .workflows import ShippingWorkflow
from .activities import ship_item

TASK_QUEUE = "shipping-task-queue"
workflows = [ShippingWorkflow]
activities = [ship_item]
```

### 步骤 5：注册与部署
**你不需要修改任何 Python 代码！**
只需在 `docker-compose.yml` 中加一段配置，或者直接复用现有的 Worker 并修改环境变量：
```yaml
worker-shipping:
  environment:
    - ENABLE_DOMAINS=app.domains.shipping
```

---

## 5. 维护与测试

*   **运行所有测试**：
    ```bash
    python -m scripts.test_hello
    python -m scripts.test_pizza
    ```
*   **查看 Worker 日志**：
    ```bash
    docker logs holo_worker_pizza
    ```

这份文档应作为项目架构的“真理来源”，任何架构变更请同步更新本文档。
