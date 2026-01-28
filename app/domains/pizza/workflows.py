from datetime import timedelta
from temporalio import activity, workflow
from app.domains.pizza.models import PizzaOrder, Bill, Receipt

# Import activity definitions for type safety
from app.domains.pizza.activities import calculate_bill, charge_credit_card, process_delivery

# --- Workflow (Orchestrator) ---

@workflow.defn
class DDDPizzaWorkflow:
    @workflow.run
    async def run(self, order: PizzaOrder) -> Receipt:
        workflow.logger.info(f"Received DDD Order for {order.customer_name}")

        # 1. Calculate Bill (Pass Object -> Return Object)
        bill = await workflow.execute_activity(
            calculate_bill,
            order,
            start_to_close_timeout=timedelta(seconds=5)
        )
        
        # 2. Charge Payment
        paid = await workflow.execute_activity(
            charge_credit_card,
            bill,
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        if not paid:
            raise ValueError("Payment failed!")

        # 3. Delivery
        delivery_address = await workflow.execute_activity(
            process_delivery,
            order,
            start_to_close_timeout=timedelta(seconds=10)
        )

        return Receipt(
            order_id=order.order_id,
            status="COMPLETED",
            message="Bon Appetit!",
            delivered_to=delivery_address
        )
