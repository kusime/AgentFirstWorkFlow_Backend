from datetime import timedelta
from temporalio import activity, workflow
from workflows.domain_models import PizzaOrder, Bill, Receipt

# --- Activities (Domain Services) ---

@activity.defn
async def calculate_bill(order: PizzaOrder) -> Bill:
    activity.logger.info(f"Calculating bill for {order.order_id}")
    
    # Simple logic accessing nested objects
    total = 0.0
    for item in order.items:
        price = 10.0 if item.size == "S" else 15.0 if item.size == "M" else 20.0
        total += price * item.quantity
    
    # VIP discount
    if order.is_vip:
        activity.logger.info("Applying VIP discount")
        total *= 0.8
        
    return Bill(order_id=order.order_id, total_amount=total)

@activity.defn
async def charge_credit_card(bill: Bill) -> bool:
    activity.logger.info(f"Charging {bill.total_amount} {bill.currency} for Order {bill.order_id}")
    # Simulate processing
    return True

@activity.defn
async def process_delivery(order: PizzaOrder) -> str:
    # Accessing deep properties naturally
    full_address = f"{order.delivery_address.street}, {order.delivery_address.city}"
    activity.logger.info(f"Delivering to: {full_address}")
    return full_address

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
