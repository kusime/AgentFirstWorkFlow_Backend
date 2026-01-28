from datetime import timedelta
from temporalio import activity
from app.domains.pizza.models import PizzaOrder, Bill, Receipt

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
    # Simulate processing (could fail here)
    return True

@activity.defn
async def process_delivery(order: PizzaOrder) -> str:
    # Accessing deep properties naturally
    full_address = f"{order.delivery_address.street}, {order.delivery_address.city}"
    activity.logger.info(f"Delivering to: {full_address}")
    return full_address
