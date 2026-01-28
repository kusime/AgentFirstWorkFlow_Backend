import asyncio
from temporalio.client import Client
from workflows.login_example import UserLoginWorkflow

async def main():
    # 1. Connect to Client
    client = await Client.connect("localhost:7233")

    # 2. Execute Workflow
    print("Simulating User Login...")
    import uuid
    # Logic: User "user-123" just logged in
    result = await client.execute_workflow(
        UserLoginWorkflow.run,
        "user-123", # The user_id
        id=f"login-event-{uuid.uuid4()}",
        task_queue="hello-task-queue",
    )

    print(f"Workflow result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
