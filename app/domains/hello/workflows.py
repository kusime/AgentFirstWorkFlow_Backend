from datetime import timedelta
from temporalio import workflow
# Import activity definitions for type safety if needed, 
# but generally we just need the function reference
from app.domains.hello.activities import say_hello

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info(f"GreetingWorkflow started for {name}")
        return await workflow.execute_activity(
            say_hello, 
            name, 
            start_to_close_timeout=timedelta(seconds=5)
        )
