# Holo Flow Core - 数据库与基础设施 (Part 1)

本项目是 Holo Asset Management 系统及其演进版本（Financial Flow/Ledger）的核心数据库基础设施模块。
不仅管理传统的资产表，还通过 **DBML 驱动** 的开发模式，实现了复杂的账户流（Account Flow）、资金洞（Holes）与追踪（Trace）的架构设计。

## 核心特性 (Key Features)

- **可视化设计驱动 (DBML-First)**
  - 使用 `db_tools/design.dbml` 作为数据库设计的**单一事实来源 (Source of Truth)**。
  - 支持复杂的表关系可视化与离线编译。

- **全自动化同步工作流 (Auto-Sync Workflow)**
  - 运行 `python -m db_tools.sync_schema` 即可一键完成：
    1. **编译**: 自动调用 `@dbml/cli` 将 DBML 编译为标准 SQL (`schema.sql`)。
    2. **迁移**: 对比当前数据库状态，自动生成 Alembic 迁移脚本。
    3. **ORM 生成**: 根据最新 Schema 自动生成 Python SQLAlchemy Models (`db_tools/out/models.py`)。

- **安全保障 (Safety First)**
  - 包含交互式 **安全检查 (Safe Check)**。
  - 当检测到破坏性操作（如删除表、删除字段）时，会强制要求用户确认，并提供迁移脚本预览，防止数据意外丢失。

- **IDE 友好 (IDE Friendly)**
  - 采用标准的 Python 包结构 (`db_tools` package)。
  - 生成的 `models.py` 支持 IDE 智能提示与类型检查。

## 快速开始 (Quick Start)

### 1. 环境准备 (Prerequisites)

本项目依赖 **Docker**, **Python 3.14+** 和 **Node.js/Yarn**。

```bash
# 1. 启动 PostgreSQL 数据库
docker-compose up -d

# 2. 安装 DBML 编译器 (用于 DBML -> SQL 转换)
# (如果尚未安装)
yarn install

# 3. 安装 Python 依赖
# 推荐使用 uv (速度更快)
uv pip install -r requirements.txt
# 或者使用 pip
pip install -r requirements.txt
```

### 2. 核心工作流 (Workflow)

**步骤 A: 修改设计**
编辑 `db_tools/design.dbml` 文件，调整表结构或字段。

**步骤 B: 同步变更**
运行同步脚本，让系统自动处理 SQL 转换、数据库迁移和代码生成：

```bash
# 注意：必须在项目根目录下，使用 -m 模块方式运行
python -m db_tools.sync_schema
```

**步骤 C: 生成测试数据 (可选)**
验证数据模型是否正常工作：

```bash
python -m db_tools.create_test_data
```

## 目录结构 (Directory Structure)

```text
.
├── db_tools/                  # 数据库工具核心目录
│   ├── design.dbml            # [核心] 数据库设计原稿 (编辑此处)
│   ├── schema.sql             # [自动] 编译后的 SQL 文件 (勿手动编辑)
│   ├── sync_schema.py         # [核心] 自动化同步脚本
│   ├── create_test_data.py    # 测试数据生成脚本
│   └── out/
│       └── models.py          # [自动] SQLAlchemy ORM 模型文件
├── alembic/                   # 数据库迁移历史版本 (Versions)
├── docker-compose.yml         # 数据库容器配置
├── package.json               # Node 依赖配置 (DBML CLI)
└── requirements.txt           # Python 依赖配置
```

---

# Holo Flow Core - Temporal 流程编排 (Part 2)

本项目集成了 **Temporal** 分布式工作流引擎，采用 **模块化单体 (Modular Monolith)** 架构，实现了基于 **领域驱动设计 (DDD)** 和 **整洁架构 (Clean Architecture)** 的业务逻辑编排。

## 核心架构 (Architecture)

### 1. 领域驱动与模块化 (DDD & Modularity)
- **高内聚**: 采用 `app/domains/<domain>/` 结构，将业务逻辑 (`activities.py`) 与流程编排 (`workflows.py`) 物理分离。
- **类型安全**: 全面使用 Pydantic 定义 DTO (Data Transfer Object)，配合自定义 `DataConverter` 实现自动序列化。

### 2. 插件式 Worker (Plugin Pattern)
- **动态发现**: Worker 不硬编码业务模块，而是通过 `importlib` 动态加载。
- **零代码注册**: 新增业务领域只需配置环境变量 `ENABLE_DOMAINS`，无需修改 Worker 代码。

### 3. 物理隔离 (Physical Isolation)
- **环境隔离**: 支持通过 Docker Compose 定义多个 Worker 服务（如 `worker-hello`, `worker-pizza`）。
- **故障隔离**: 即使共享同一个镜像，不同容器只加载指定的业务代码，实现真正的故障隔离与独立扩容。

## 目录结构 (Directory Structure - Part 2)

```text
app/
├── common/                 # 公共组件 (Infrastructure Layer)
├── domains/                # 业务领域层 (Domain Layer)
│   ├── hello/              # 示例领域
│   └── pizza/              # 核心业务领域 (DDD)
│       ├── models.py       # Pydantic DTOs
│       ├── activities.py   # 业务逻辑 (Business Rules)
│       └── workflows.py    # 流程编排 (Use Cases)
└── worker/                 # 接口层 (Interface Layer)
    └── main.py             # 通用 Worker 启动器
infrastructure/             # 部署配置
└── Dockerfile.worker       # Worker 镜像
scripts/                    # 客户端测试脚本
├── test_hello.py
└── test_pizza.py
```

## 快速开始 (Temporal Quick Start)

### 1. 启动全栈服务
```bash
# 启动 PostgreSQL, Temporal Server, UI 及所有 Workers
docker-compose up -d --build
```

### 2. 运行测试流程
```bash
# 运行 Hello World 流程
python -m scripts.test_hello

# 运行 DDD Pizza 订单流程
python -m scripts.test_pizza
```

### 3. 理解隔离策略
查看 `docker-compose.yml` 可以看到我们启动了两个隔离的 Worker：
- `worker-hello`: 只处理 `app.domains.hello`
- `worker-pizza`: 只处理 `app.domains.pizza`

详细架构文档请参考: [docs/temporal/architecture_and_refactor_zh.md](docs/temporal/architecture_and_refactor_zh.md)
