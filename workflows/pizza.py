
import asyncio
from datetime import timedelta
from temporalio import activity, workflow

# 1. Flaky Activity: Make Dough
@activity.defn
async def make_dough(pizza_type: str) -> str:
    import random
    # Simulate randomness
    if random.random() < 0.5:
        activity.logger.error("Oops! Spilled the flour!")
        raise ValueError("Spilled the flour!")
    
    activity.logger.info(f"Dough for {pizza_type} is ready!")
    return f"Dough({pizza_type})"

# 2. Normal Activity: Bake
@activity.defn
async def bake_pizza(dough: str) -> str:
    activity.logger.info(f"Baking {dough}...")
    # Simulate a quick bake for the activity itself
    return f"Baked {dough}"

# 3. Workflow
@workflow.defn
class PizzaWorkflow:
    @workflow.run
    async def run(self, pizza_type: str) -> str:
        workflow.logger.info(f"Order received for {pizza_type}")

        # Step 1: Make Dough (Automatic Retries)
        # We set a short start_to_close_timeout to see retries quickly if it hangs,
        # but here the failure is immediate (exception).
        dough = await workflow.execute_activity(
            make_dough,
            pizza_type,
            start_to_close_timeout=timedelta(seconds=5),
        )

        # Step 2: Proofing/Rising (Durable Timer)
        # Even if you kill the worker now, it will wake up after 10 seconds.
        workflow.logger.info("Letting dough rise for 10 seconds...")
        await asyncio.sleep(10)

        # Step 3: Bake
        final_pizza = await workflow.execute_activity(
            bake_pizza,
            dough,
            start_to_close_timeout=timedelta(seconds=5),
        )

        return final_pizza
