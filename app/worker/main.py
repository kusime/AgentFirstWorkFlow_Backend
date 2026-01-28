import asyncio
import importlib
from typing import List
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.converter import DataConverter

from app.common.config import config
from app.common.converter import PydanticDataConverter

async def main():
    print(f"Connecting to Temporal Server at {config.temporal_host}...")
    
    client = await Client.connect(
        config.temporal_host,
        data_converter=DataConverter(payload_converter_class=PydanticDataConverter),
    )

    enabled_domains = config.enabled_domains
    workers = []

    print(f"Starting Worker for Domains: {enabled_domains}")

    if not enabled_domains:
        print("Warning: No domains enabled! Set ENABLE_DOMAINS env var.")
        return

    # --- Strategy: Dynamic Discovery ---
    for domain_path in enabled_domains:
        try:
            print(f"  - Loading Domain: '{domain_path}'...")
            module = importlib.import_module(domain_path)
            
            # Convention: Each domain module must export TASK_QUEUE, workflows, activities
            if not hasattr(module, "TASK_QUEUE") or not hasattr(module, "workflows") or not hasattr(module, "activities"):
                print(f"    [ERROR] Domain '{domain_path}' is missing required exports (TASK_QUEUE, workflows, activities). Skipping.")
                continue

            print(f"    [SUCCESS] Registering Worker on '{module.TASK_QUEUE}'")
            workers.append(
                Worker(
                    client,
                    task_queue=module.TASK_QUEUE,
                    workflows=module.workflows,
                    activities=module.activities,
                )
            )
        except ImportError as e:
            print(f"    [ERROR] Failed to import domain '{domain_path}': {e}")
        except Exception as e:
            print(f"    [ERROR] Unexpected error loading '{domain_path}': {e}")

    if not workers:
        print("Error: No workers were successfully registered.")
        return

    # Run all registered workers concurrently
    print(f"Worker process running with {len(workers)} active worker instances...")
    await asyncio.gather(*[w.run() for w in workers])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker stopped by user.")
