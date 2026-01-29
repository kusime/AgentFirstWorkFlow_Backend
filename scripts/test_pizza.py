import asyncio
import os
import time
from temporalio.client import Client
from temporalio.converter import DataConverter
from app.infrastructure.workflows.converter import PydanticDataConverter
from app.domains.pizza import TASK_QUEUE
# 从新的 workflows 目录导入 workflow
from app.workflows.pizza_workflow import PizzaOrderWorkflow
# 从 SDK contracts 导入 DTOs
from app.domains.pizza.sdk.contracts import PizzaOrder, PizzaItem, Address

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

    # 使用时间戳避免ID冲突
    workflow_id = f"pizza-order-{int(time.time())}"
    print(f"Submitting 'PizzaOrderWorkflow' to queue: '{TASK_QUEUE}' with ID: {workflow_id}")
    result = await client.execute_workflow(
        PizzaOrderWorkflow.run,
        order,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    print(f"✅ Workflow Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
