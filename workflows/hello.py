from datetime import timedelta
from temporalio import activity, workflow

# 1. Define Activity
@activity.defn
async def say_hello(name: str) -> str:
    activity.logger.info(f"Running activity with parameter {name}")
    return f"Hello, {name}!"

# 2. Define Workflow
@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        # Execute the activity
        return await workflow.execute_activity(
            say_hello,
            name,
            start_to_close_timeout=timedelta(seconds=5),
        )
