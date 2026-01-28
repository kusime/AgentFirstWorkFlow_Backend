import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.hello import GreetingWorkflow, say_hello
from workflows.pizza import PizzaWorkflow, make_dough, bake_pizza
from workflows.login_example import UserLoginWorkflow, send_welcome_email, track_analytics, add_to_crm
from workflows.ddd_pizza import DDDPizzaWorkflow, calculate_bill, charge_credit_card, process_delivery
from workflows.pydantic_converter import PydanticDataConverter
from temporalio.converter import DataConverter

async def main():
    # 1. Connect to Client with Custom Data Converter
    # In Docker, we set TEMPORAL_HOST=temporal:7233
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    print(f"Connecting to Temporal Server at {temporal_host}...")
    
    client = await Client.connect(
        temporal_host,
        data_converter=DataConverter(payload_converter_class=PydanticDataConverter),
    )
    
    # 2. Run Worker
    print("Worker started, listening on 'hello-task-queue'...")
    worker = Worker(
        client,
        task_queue="hello-task-queue",
        workflows=[GreetingWorkflow, PizzaWorkflow, UserLoginWorkflow, DDDPizzaWorkflow],
        activities=[
            say_hello, make_dough, bake_pizza, 
            send_welcome_email, track_analytics, add_to_crm,
            calculate_bill, charge_credit_card, process_delivery
        ],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
