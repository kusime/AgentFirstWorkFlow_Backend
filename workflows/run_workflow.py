import os
import asyncio
from temporalio.client import Client
from workflows.ddd_pizza import DDDPizzaWorkflow
from workflows.domain_models import PizzaOrder, PizzaItem, Address
from workflows.pydantic_converter import PydanticDataConverter
from temporalio.converter import DataConverter
from pydantic import ValidationError

async def main():
    # 1. Connect to Client with Custom Data Converter
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(
        temporal_host,
        data_converter=DataConverter(payload_converter_class=PydanticDataConverter),
    )

    try:
        # 2. Construct Complex Domain Object
        # In a real API, this data comes from the HTTP Request Body
        print("Constructing Order...")
        order = PizzaOrder(
            order_id="order-999",
            customer_name="Alice",
            items=[
                PizzaItem(flavor="Pepperoni", size="L", quantity=1),
                PizzaItem(flavor="Mushroom", size="M", quantity=2)
            ],
            delivery_address=Address(
                street="123 Dataclass Lane",
                city="TypeSafe City",
                zip_code="90210"
            ),
            is_vip=True
        )

        print(f"Submitting DDD Order for {order.customer_name}...")
        
        # 3. Execute Workflow
        # If the DataConverter fails to serialize (e.g. invalid type), it explodes here too.
        result = await client.execute_workflow(
            DDDPizzaWorkflow.run,
            order,
            id=f"ddd-order-{order.order_id}",
            task_queue="hello-task-queue",
        )

        print(f"Workflow result: {result}")

    except ValidationError as e:
        # This is where you notify the Frontend user!
        # In FastAPI/Flask/Django, you would return:
        # return Response(json.dumps(e.errors()), status=400)
        print("\n[CLIENT ERROR CAUGHT] invalid data input!")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\n[SYSTEM ERROR] Unexpected crash: {e}")

if __name__ == "__main__":
    asyncio.run(main())
