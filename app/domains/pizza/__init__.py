from app.domains.pizza.workflows import DDDPizzaWorkflow
from app.domains.pizza.activities import calculate_bill, charge_credit_card, process_delivery

# Define Component Bundles
workflows = [DDDPizzaWorkflow]
activities = [calculate_bill, charge_credit_card, process_delivery]
TASK_QUEUE = "pizza-task-queue"
