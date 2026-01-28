from datetime import timedelta
from temporalio import activity

@activity.defn
async def say_hello(name: str) -> str:
    activity.logger.info(f"Saying hello to {name}")
    return f"Hello, {name}!"
