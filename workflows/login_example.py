import asyncio
from datetime import timedelta
from temporalio import activity, workflow

# --- 活动 (Activities) ---
# 这些相当于 Event Bus 中的 "Consumer"
# 以前是: @event_bus.subscribe("UserLoggedIn")
# 现在是: 普通的 Python 函数

@activity.defn
async def send_welcome_email(user_id: str) -> str:
    activity.logger.info(f"Sending email to {user_id}...")
    # 模拟网络调用
    await asyncio.sleep(1) 
    return "Email Sent"

@activity.defn
async def track_analytics(user_id: str) -> str:
    activity.logger.info(f"Tracking login event for {user_id}...")
    # 模拟可能失败的分析服务
    # 在 Temporal 中，如果这个失败了，默认会无限重试，直到服务恢复
    # 或者我们可以配置重试策略，比如只重试 3 次，然后忽略
    return "Analytics Tracked"

@activity.defn
async def add_to_crm(user_id: str) -> str:
    activity.logger.info(f"Adding {user_id} to CRM...")
    return "CRM Updated"

# --- 工作流 (Workflow) ---
# 这个相当于 "Event Bus" 本身，但它是可见的、受控的

@workflow.defn
class UserLoginWorkflow:
    @workflow.run
    async def run(self, user_id: str) -> list[str]:
        workflow.logger.info(f"User {user_id} logged in. Triggering post-login actions.")

        # 核心理念: "Explicit Parallel Orchestration" (显式并行编排)
        # 我们不需要 "发布" 一个事件然后祈祷有人处理
        # 我们直接 "调度" 所有需要做的事情
        
        # asyncio.gather 允许这些任务并行执行 (fire-and-wait-all)
        # 这比 Event Bus 更好，因为:
        # 1. 你能看到到底触发了神马 (White-box)
        # 2. 你能知道它们什么时候都做完了 (Completion)
        results = await asyncio.gather(
            # 任务 1: 发邮件
            workflow.execute_activity(
                send_welcome_email, 
                user_id, 
                start_to_close_timeout=timedelta(seconds=10)
            ),
            # 任务 2: 埋点分析
            workflow.execute_activity(
                track_analytics, 
                user_id, 
                start_to_close_timeout=timedelta(seconds=10)
            ),
            # 任务 3: CRM 更新
            workflow.execute_activity(
                add_to_crm,
                user_id,
                start_to_close_timeout=timedelta(seconds=10)
            )
        )
        
        workflow.logger.info("All post-login actions completed successfully.")
        return results

# --- 进阶: 容错处理 ---
# 如果你希望 "埋点失败不影响主要流程"，可以这样做:
"""
try:
    await workflow.execute_activity(track_analytics, user_id, ...)
except Exception:
    workflow.logger.error("Analytics failed, but ignoring it so workflow can finish.")
"""
