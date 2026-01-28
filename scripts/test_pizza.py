import asyncio
import os
from temporalio.client import Client
from temporalio.converter import DataConverter
from app.common.converter import PydanticDataConverter
from app.domains.pizza import TASK_QUEUE
from app.domains.pizza.workflows import DDDPizzaWorkflow
from app.domains.pizza.models import PizzaOrder, PizzaItem, Address

async def main():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    print(f"Connecting to Temporal: {temporal_host}")
    
    # Must use PydanticDataConverter
    client = await Client.connect(
        temporal_host,
        data_converter=DataConverter(payload_converter_class=PydanticDataConverter),
    )

    # Construct the complex object
    order = PizzaOrder(
        order_id="order-1001",
        customer_name="Bob",
        items=[
            PizzaItem(flavor="Cheese", size="S", quantity=1),
            PizzaItem(flavor="Veggie", size="L", quantity=1)
        ],
        delivery_address=Address(
            street="456 Python Ave",
            city="PyCity",
            zip_code="10101"
        ),
        is_vip=False
    )

    print(f"Submitting 'DDDPizzaWorkflow' to queue: '{TASK_QUEUE}'...")
    result = await client.execute_workflow(
        DDDPizzaWorkflow.run,
        order,
        id=f"pizza-order-{order.order_id}",
        task_queue=TASK_QUEUE,
    )
    print(f"✅ Workflow Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
