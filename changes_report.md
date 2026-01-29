# Code Changes Report
**Date:** 2026-01-30 01:06:45
**Target:** `working_dir`

---
**Tracked Files Changed:** 3
**Untracked Files:** 1

## 📝 Diff Output
```diff
diff --git a/app/domains/pizza/__init__.py b/app/domains/pizza/__init__.py
index 3ce86d5..175a41d 100644
--- a/app/domains/pizza/__init__.py
+++ b/app/domains/pizza/__init__.py
@@ -22,7 +22,48 @@ WORKFLOW_CLASSES = []  # Worker will dynamically import from app.workflows.pizza
 import inspect
 
 # 实例化 Gateway
-_impl = PizzaActivitiesImpl()
+# ============================================================================
+# Composition Root (依赖注入组装)
+# ============================================================================
+import os
+from app.domains.pizza.usecases import (
+    CalculateBillUseCase,
+    ProcessPaymentUseCase,
+    ArrangeDeliveryUseCase,
+)
+from app.domains.pizza.infrastructure.payment.mock_payment_gateway import MockPaymentGateway
+from app.domains.pizza.infrastructure.delivery.mock_delivery_service import MockDeliveryService
+
+# 1. 识别环境
+ENV = os.getenv("ENV", "DEV")
+
+# 2. 实例化 Infrastructure Implementations
+if ENV == "PROD":
+    # PROD 环境下使用真实的实现 (示例，目前留空 placeholders)
+    # from app.domains.pizza.infrastructure.payment.stripe_gateway import StripePaymentGateway
+    # from app.domains.pizza.infrastructure.delivery.uber_delivery import UberDeliveryService
+    # payment_gateway = StripePaymentGateway(...)
+    # delivery_service = UberDeliveryService(...)
+    # 目前Fallback到Mock避免运行错误
+    print(f"[PizzaDomain] Initializing in PROD mode (using Mock for demo)")
+    payment_gateway = MockPaymentGateway()
+    delivery_service = MockDeliveryService()
+else:
+    print(f"[PizzaDomain] Initializing in {ENV} mode (using Mocks)")
+    payment_gateway = MockPaymentGateway()
+    delivery_service = MockDeliveryService()
+
+# 3. 实例化 UseCases (注入 Infrastructure)
+calculate_bill_usecase = CalculateBillUseCase()
+payment_usecase = ProcessPaymentUseCase(payment_gateway)
+delivery_usecase = ArrangeDeliveryUseCase(delivery_service)
+
+# 4. 实例化 Gateway (注入 UseCases)
+_impl = PizzaActivitiesImpl(
+    calculate_bill_usecase=calculate_bill_usecase,
+    payment_usecase=payment_usecase,
+    delivery_usecase=delivery_usecase,
+)
 
 # 自动发现所有带有 @activity.defn 装饰器的方法 (Reflection)
 # 避免手动维护 activities 列表
diff --git a/app/domains/pizza/gateway.py b/app/domains/pizza/gateway.py
index 2ace103..25751b8 100644
--- a/app/domains/pizza/gateway.py
+++ b/app/domains/pizza/gateway.py
@@ -46,16 +46,21 @@ class PizzaActivitiesImpl(PizzaActivities):
     使用依赖注入初始化 UseCases。
     """
     
-    def __init__(self):
-        # 在这里进行依赖注入 (Dependency Injection)
-        # 在真实应用中，这些依赖可能由外部容器传入
-        self.calculate_bill_usecase = CalculateBillUseCase()
-        
-        payment_gateway = MockPaymentGateway()
-        self.payment_usecase = ProcessPaymentUseCase(payment_gateway)
-        
-        delivery_service = MockDeliveryService()
-        self.delivery_usecase = ArrangeDeliveryUseCase(delivery_service)
+    def __init__(
+        self,
+        calculate_bill_usecase: CalculateBillUseCase,
+        payment_usecase: ProcessPaymentUseCase,
+        delivery_usecase: ArrangeDeliveryUseCase,
+    ):
+        """
+        Args:
+            calculate_bill_usecase: 计算账单 UseCase (依赖注入)
+            payment_usecase: 支付 UseCase (依赖注入)
+            delivery_usecase: 配送 UseCase (依赖注入)
+        """
+        self.calculate_bill_usecase = calculate_bill_usecase
+        self.payment_usecase = payment_usecase
+        self.delivery_usecase = delivery_usecase
 
     @activity.defn(name=ACTIVITY_CALCULATE_BILL)
     async def calculate_bill(self, order: PizzaOrder) -> Bill:
diff --git a/project_context.md b/project_context.md
index 8580f4e..19bdea0 100644
--- a/project_context.md
+++ b/project_context.md
@@ -29,7 +29,48 @@ WORKFLOW_CLASSES = []  # Worker will dynamically import from app.workflows.pizza
 import inspect
 
 # 实例化 Gateway
-_impl = PizzaActivitiesImpl()
+# ============================================================================
+# Composition Root (依赖注入组装)
+# ============================================================================
+import os
+from app.domains.pizza.usecases import (
+    CalculateBillUseCase,
+    ProcessPaymentUseCase,
+    ArrangeDeliveryUseCase,
+)
+from app.domains.pizza.infrastructure.payment.mock_payment_gateway import MockPaymentGateway
+from app.domains.pizza.infrastructure.delivery.mock_delivery_service import MockDeliveryService
+
+# 1. 识别环境
+ENV = os.getenv("ENV", "DEV")
+
+# 2. 实例化 Infrastructure Implementations
+if ENV == "PROD":
+    # PROD 环境下使用真实的实现 (示例，目前留空 placeholders)
+    # from app.domains.pizza.infrastructure.payment.stripe_gateway import StripePaymentGateway
+    # from app.domains.pizza.infrastructure.delivery.uber_delivery import UberDeliveryService
+    # payment_gateway = StripePaymentGateway(...)
+    # delivery_service = UberDeliveryService(...)
+    # 目前Fallback到Mock避免运行错误
+    print(f"[PizzaDomain] Initializing in PROD mode (using Mock for demo)")
+    payment_gateway = MockPaymentGateway()
+    delivery_service = MockDeliveryService()
+else:
+    print(f"[PizzaDomain] Initializing in {ENV} mode (using Mocks)")
+    payment_gateway = MockPaymentGateway()
+    delivery_service = MockDeliveryService()
+
+# 3. 实例化 UseCases (注入 Infrastructure)
+calculate_bill_usecase = CalculateBillUseCase()
+payment_usecase = ProcessPaymentUseCase(payment_gateway)
+delivery_usecase = ArrangeDeliveryUseCase(delivery_service)
+
+# 4. 实例化 Gateway (注入 UseCases)
+_impl = PizzaActivitiesImpl(
+    calculate_bill_usecase=calculate_bill_usecase,
+    payment_usecase=payment_usecase,
+    delivery_usecase=delivery_usecase,
+)
 
 # 自动发现所有带有 @activity.defn 装饰器的方法 (Reflection)
 # 避免手动维护 activities 列表
@@ -93,16 +134,21 @@ class PizzaActivitiesImpl(PizzaActivities):
     使用依赖注入初始化 UseCases。
     """
     
-    def __init__(self):
-        # 在这里进行依赖注入 (Dependency Injection)
-        # 在真实应用中，这些依赖可能由外部容器传入
-        self.calculate_bill_usecase = CalculateBillUseCase()
-        
-        payment_gateway = MockPaymentGateway()
-        self.payment_usecase = ProcessPaymentUseCase(payment_gateway)
-        
-        delivery_service = MockDeliveryService()
-        self.delivery_usecase = ArrangeDeliveryUseCase(delivery_service)
+    def __init__(
+        self,
+        calculate_bill_usecase: CalculateBillUseCase,
+        payment_usecase: ProcessPaymentUseCase,
+        delivery_usecase: ArrangeDeliveryUseCase,
+    ):
+        """
+        Args:
+            calculate_bill_usecase: 计算账单 UseCase (依赖注入)
+            payment_usecase: 支付 UseCase (依赖注入)
+            delivery_usecase: 配送 UseCase (依赖注入)
+        """
+        self.calculate_bill_usecase = calculate_bill_usecase
+        self.payment_usecase = payment_usecase
+        self.delivery_usecase = delivery_usecase
 
     @activity.defn(name=ACTIVITY_CALCULATE_BILL)
     async def calculate_bill(self, order: PizzaOrder) -> Bill:
```

## 🆕 Untracked Files Content
### File: `scripts/export_changes.py`
```python
#!/usr/bin/env python3
import subprocess
import sys
import os
import argparse
from datetime import datetime

def run_git_command(args):
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return None, result.stderr
        return result.stdout.strip(), None
    except Exception as e:
        return None, str(e)

def generate_changes_report(target="working_dir", output_file="changes_report.md"):
    print(f"🔍 Analyzing changes for: {target}")
    
    report_content = []
    report_content.append(f"# Code Changes Report")
    report_content.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append(f"**Target:** `{target}`")
    report_content.append("\n---")
    
    diff_content = ""
    err = None

    # Logic to get the diff
    if target == "working_dir":
        # 1. Diff of tracked files (Staged + Unstaged vs HEAD)
        diff_content, err = run_git_command(["diff", "HEAD"])
        if err:
            print(f"Error running git diff: {err}")
            return

        # 2. Identify untracked files
        untracked_out, _ = run_git_command(["ls-files", "--others", "--exclude-standard"])
        untracked_files = untracked_out.splitlines() if untracked_out else []
        
    else:
        # Target passed directly to git (e.g. "HEAD~1", "main..branch")
        # For a single commit hash, use "show", for ranges use "diff"
        if ".." in target:
             diff_content, err = run_git_command(["diff", target])
        else:
             # Assuming single commit or ref
             # Check if it's a range or a point. git diff works for both usually if distinct ref.
             # But git show is better for "what changed in this specific commit"
             # Let's try git diff target^! if it looks like a commit, but safest is just git diff target (which compares target vs working dir? No. 
             # git diff commit compares working tree with commit.
             # git show commit shows the commit's patch.
             
             # Let's simplisticly assume if user passes args, they know git syntax, 
             # BUT we want to capture the patch.
             # If target is "HEAD~1", git diff HEAD~1 compares HEAD~1 with Working Dir (bad).
             # We probably want "git show" if it's a single point, or "git diff" if it's a range.
             
             # Let's just use what user gives if it contains ".." else use format-patch style or show
             # Actually, best for AI is likely: "What changed in the working directory" (default)
             # Or "What changed in the last commit" => HEAD~1..HEAD
             
             # Let's stick to: if arg provided, treat as git diff arg.
             # NOTE: `git diff commit` shows difference between commit and working tree.
             # `git diff commit1 commit2` shows diff between commits.
             diff_content, err = run_git_command(["diff", target])

        untracked_files = [] 
        if err:
            print(f"Error: {err}")
            return

    # Add Stats
    if diff_content:
        # Count changed files roughly
        changed_files_count = diff_content.count("diff --git")
        report_content.append(f"**Tracked Files Changed:** {changed_files_count}")
    else:
        report_content.append(f"**Tracked Files Changed:** 0")
        
    if untracked_files:
        report_content.append(f"**Untracked Files:** {len(untracked_files)}")

    report_content.append("\n## 📝 Diff Output")
    if diff_content:
        report_content.append("```diff")
        report_content.append(diff_content)
        report_content.append("```")
    else:
        report_content.append("*No changes in tracked files.*")

    # Add content of untracked files
    if untracked_files:
        report_content.append("\n## 🆕 Untracked Files Content")
        for f_path in untracked_files:
            if os.path.isfile(f_path):
                try:
                    with open(f_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Detect Language
                    ext = os.path.splitext(f_path)[1]
                    lang = "text"
                    if ext == ".py": lang = "python"
                    elif ext == ".md": lang = "markdown"
                    elif ext in [".json", ".js"]: lang = "json"
                    
                    report_content.append(f"### File: `{f_path}`")
                    report_content.append(f"```{lang}")
                    report_content.append(content)
                    report_content.append("```\n")
                except Exception as e:
                    report_content.append(f"> Error reading {f_path}: {e}")

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    
    print(f"✅ Report successfully generated: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export git changes to Markdown for AI context.")
    parser.add_argument("target", nargs="?", default="working_dir", 
                        help="Git diff target (e.g., 'HEAD~1..HEAD' or default 'working_dir' for uncommitted changes)")
    parser.add_argument("-o", "--output", default="changes_report.md", help="Output Markdown filename")
    
    args = parser.parse_args()
    generate_changes_report(args.target, args.output)

```
