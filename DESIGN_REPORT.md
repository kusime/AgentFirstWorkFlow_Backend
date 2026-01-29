# Holo Asset Management 架构设计报告

**版本**: 1.0.0
**日期**: 2026-01-30
**状态**: 已实施 (Implemented)

---

## 1. 架构概览 (Executive Summary)

Holo Asset Management 系统采用了 **模块化单体 (Modular Monolith)** 架构，结合 **领域驱动设计 (DDD)** 和 **Temporal 分布式工作流**，构建了一个高内聚、低耦合且易于扩展的金融资产管理平台。

核心设计哲学：
*   **物理分离，逻辑统一**：业务通过 Domain 模块化隔离，流程通过 Temporal 统一编排。
*   **契约驱动 (Contract-First)**：主要组件间通过强类型 Contracts (Pydantic DTOs) 交互。
*   **单一事实来源 (Source of Truth)**：数据库设计严格遵循 DBML 定义。

---

## 2. 核心架构模式 (Core Architecture)

### 2.1 领域驱动设计 (DDD)
系统按业务边界划分为独立的 Domains（如 `pizza`），每个 Domain 内部遵循 **整洁架构 (Clean Architecture)** 分层：

*   **SDK (Contracts Layer)**: 
    *   定义 `contracts.py` (Pydantic DTOs) 和常量。
    *   **作用**：这是 Domain 对外暴露的唯一“API”，Workflow 只依赖此层。
*   **Usecases (Application Layer)**:
    *   纯 Python 业务逻辑，不依赖具体数据库或外部服务。
    *   通过 `services.py` 定义的接口与外部交互。
*   **Gateway (Interface Adapter Layer)**:
    *   Temporal Activities 的具体实现载体。
    *   负责装配：将 Infrastructure 实现注入到 Usecases 中。
*   **Infrastructure (Infrastructure Layer)**:
    *   数据库访问 (Repositories)、外部 API 调用 (Payment/Delivery) 的具体实现。

### 2.2 Temporal 工作流集成
我们采用 Temporal 作为系统的中央神经系统，负责跨 Domain 的长流程编排。

*   **流程与执行分离**:
    *   `app/workflows/`: 仅包含流程定义 (Workflow Def)，只引用 `sdk/contracts.py`，**严禁**直接引用 Domain 实现。
    *   `app/domains/<name>/gateway.py`: 包含步骤实现 (Activity Impl)。
*   **强类型数据转换**:
    *   自定义 `PydanticDataConverter` 确保 Object <-> JSON 的自动类型安全转换。
*   **插件式 Worker 架构**:
    *   `app.infrastructure.workflows.worker` 是一个通用宿主。
    *   通过环境变量 `ENABLE_DOMAINS` (如 `app.domains.pizza`) 动态加载业务能力，无需修改 Worker 代码即可扩展新业务。

---

## 3. 数据库基础设施 (Database Infrastructure)

为了解决 Schema 漂移和迁移管理的复杂性，我们引入了 **DBML-First** 工作流：

*   **工具链 (`tools/db_utils/`)**:
    *   `design.dbml`: 数据库设计的**源头**。
    *   `manage_db.py`: 自研 CLI 工具。
        *   `gen-orm`: DBML -> SQLAlchemy 2.0 Models (自动生成的代码，支持 IDE 提示)。
        *   `sync`: DBML -> SQL -> Alembic Migration -> Database Apply (全自动闭环)。
*   **安全性**:
    *   包含交互式安全检查，防止生产环境意外删表/删列。

---

## 4. 部署与隔离策略 (Deployment & Isolation)

基于 Docker Compose 的服务编排支持细粒度的资源隔离：

*   **服务隔离**: 虽然代码在同一个单体仓库，但 `worker-pizza` 和 `worker-hello` (如果启用) 运行在完全独立的容器中。
*   **按需加载**: 每个 Worker 容器只通过 `ENABLE_DOMAINS` 加载其需要的 Domain 代码，实现故障隔离。
*   **统一存储**: 所有服务共享 PostgreSQL 和 Temporal Server 集群。

---

## 5. 项目目录映射 (Directory Map)

```text
.
├── app/
│   ├── domains/           # [DDD] 业务领域 (Pizza, Core, etc.)
│   ├── workflows/         # [Temporal] 流程编排定义
│   ├── infrastructure/    # [Global] 通用 Worker, Config, Converter
│   └── common/            # [Shared] 共享工具类
├── tools/
│   └── db_utils/          # [DB] DBML 工具链 & CLI
│       ├── examples/      # schema 和 scripts
│       └── manage_db.py   # 数据库管理主入口
├── docker-compose.yml     # 全栈环境编排
└── DESIGN_REPORT.md       # 本文档
```
