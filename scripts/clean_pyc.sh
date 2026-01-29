#!/bin/bash

# 获取脚本所在目录的上一级目录（即项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🧹 Cleaning up Python bytecode in: $PROJECT_ROOT"

# 删除 __pycache__ 目录
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + -print

# 删除 .pyc 文件
find "$PROJECT_ROOT" -type f -name "*.pyname" -delete -print
find "$PROJECT_ROOT" -type f -name "*.pyc" -delete -print

echo "✨ Clean up completed!"
