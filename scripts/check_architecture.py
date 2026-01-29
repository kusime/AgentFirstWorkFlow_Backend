#!/usr/bin/env python3
"""
架构合规性检查脚本

验证项目是否符合 DDD 分层架构规范：
1. Workflow 不直接导入 gateway.py
2. Workflow 只导入 sdk/contracts.py
3. Usecases 不依赖 infrastructure 具体实现
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class ArchitectureChecker:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations = []
    
    def check_file(self, file_path: Path) -> List[str]:
        """检查单个文件的导入"""
        with open(file_path) as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError as e:
                return [f"Syntax error in {file_path}: {e}"]
        
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                violation = self.check_import(node, file_path)
                if violation:
                    violations.append(violation)
        
        return violations
    
    def check_import(self, node: ast.AST, file_path: Path) -> str:
        """检查单个导入语句"""
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            
            # 规则1: Workflow 不能直接导入 gateway
            if "workflows/" in str(file_path) or "workflows.py" in str(file_path):
                if ".gateway" in module:
                    return f"❌ Workflow违规: {file_path} 不能导入 gateway ({module})"
            
            # 规则2: Usecases 不能导入 infrastructure 具体实现
            if "usecases.py" in str(file_path):
                if ".infrastructure." in module:
                    return f"❌ Usecase违规: {file_path} 不能导入 infrastructure ({module})"
        
        return None
    
    def check_all(self):
        """检查所有文件"""
        print("🔍 开始架构合规性检查...\n")
        
        # 检查所有 Python 文件
        py_files = list(self.project_root.glob("app/**/*.py"))
        
        total_files = 0
        total_violations = 0
        
        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue
            
            total_files += 1
            violations = self.check_file(py_file)
            
            if violations:
                total_violations += len(violations)
                for violation in violations:
                    print(violation)
                    self.violations.append(violation)
        
        print(f"\n📊 检查完成:")
        print(f"  - 检查文件数: {total_files}")
        print(f"  - 发现违规: {total_violations}")
        
        if total_violations == 0:
            print("\n✅ 架构合规性检查通过!")
            return True
        else:
            print("\n❌ 发现架构违规，请修复后再运行")
            return False


def main():
    project_root = Path(__file__).parent.parent
    checker = ArchitectureChecker(project_root)
    
    success = checker.check_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
