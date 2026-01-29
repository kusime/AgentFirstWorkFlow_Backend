# HoloAsset DB Management Tools

这是一个集成的数据库管理工具箱，用于连接 **Design (DBML)** 与 **Implementation (Database & ORM)**。

核心理念：**Design First**。所有的数据库变更都应首先在 `examples/design.dbml` 中进行，然后通过工具自动同步到代码和数据库中。

## 📂 目录结构

```text
tools/db_utils/
├── manage_db.py         # 🎮 主控台 (Master CLI Tool)
├── alembic/             # 🔧 迁移引擎配置 (env.py, .ini, versions/)
└── examples/            # 📦 示例与默认 Schema
    ├── design.dbml      # ✨ 单一真相源 (DB Design)
    ├── out/             # 🏭 生成的 SQLAlchemy 2.0 ORM 代码
    └── scripts/         # 📜 辅助脚本 (如 create_test_data.py)
```

## 🚀 快速开始

该工具集成了 DBML 编译、ORM 生成和 Alembic 迁移。为了确保环境兼容性，请在项目的 Conda 环境中运行。

### 1. 生成 ORM 代码 (Code Generation)

当您修改了 `design.dbml` 但还不想应用到数据库时，可以仅生成 Python 代码查看效果。

```bash
# 生成默认示例 (tools/db_utils/examples/out/models.py)
python tools/db_utils/manage_db.py gen-orm

# 指定自定义 DBML 和输出路径
python tools/db_utils/manage_db.py gen-orm --dbml my_design.dbml --out app/domains/my_orm.py
```

### 2. 数据库同步 (Full Sync)

这是日常开发中最常用的命令。它执行以下全自动流程：
1. `DBML` -> `Schema.sql`
2. `Schema.sql` -> `Temp DB` -> `SQLAlchemy Models`
3. 比较 `Models` vs `Prod DB` -> 生成 Migration Script
4. 应用 Migration

```bash
# 同步变更并自动应用
python tools/db_utils/manage_db.py sync --msg "add_user_table"
```

> **安全特性**：在生成迁移前，工具会自动执行 `upgrade head` 确保本地数据库是最新的，防止冲突。

## 🛠️ 高级配置

### 环境变量
工具依赖项目根目录的 `.env` 文件（或环境变量）连接数据库：
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`

### Alembic 配置
Alembic 配置文件位于 `tools/db_utils/alembic/alembic.ini`。
如果需要自定义迁移逻辑，请编辑 `tools/db_utils/alembic/env.py`。
