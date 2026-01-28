import asyncio
import os
from temporalio.client import Client
from app.domains.hello import TASK_QUEUE, GreetingWorkflow

async def main():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    print(f"Connecting to Temporal: {temporal_host}")
    client = await Client.connect(temporal_host)

    print(f"Submitting 'GreetingWorkflow' to queue: '{TASK_QUEUE}'...")
    result = await client.execute_workflow(
        GreetingWorkflow.run,
        "World",
        id="hello-workflow-id-1",
        task_queue=TASK_QUEUE,
    )
    print(f"✅ Workflow Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
