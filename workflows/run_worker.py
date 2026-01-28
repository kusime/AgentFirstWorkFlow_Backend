import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.hello import GreetingWorkflow, say_hello
from workflows.pizza import PizzaWorkflow, make_dough, bake_pizza
from workflows.login_example import UserLoginWorkflow, send_welcome_email, track_analytics, add_to_crm

async def main():
    # 1. Connect to Client
    client = await Client.connect("localhost:7233")
    
    # 2. Run Worker
    print("Worker started, listening on 'hello-task-queue'...")
    worker = Worker(
        client,
        task_queue="hello-task-queue",
        workflows=[GreetingWorkflow, PizzaWorkflow, UserLoginWorkflow],
        activities=[say_hello, make_dough, bake_pizza, send_welcome_email, track_analytics, add_to_crm],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
