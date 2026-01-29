import asyncio
import importlib
from typing import List
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.converter import DataConverter

from app.infrastructure.workflows.config import config
from app.infrastructure.workflows.converter import PydanticDataConverter

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

    # 导入workflow注册表
    from app.workflows import get_workflows_by_queue
    workflows_by_queue = get_workflows_by_queue()
    
    print(f"Loaded {len(workflows_by_queue)} workflow queues from registry")

    # 步骤1: 从domains收集activities（按task_queue分组）
    activities_by_queue = {}
    
    for domain_path in enabled_domains:
        try:
            print(f"  - Loading Domain: '{domain_path}'...")
            module = importlib.import_module(domain_path)
            
            activities = getattr(module, 'activities', [])
            task_queue = getattr(module, 'TASK_QUEUE', None)
            
            if not task_queue:
                print(f"    [ERROR] Domain '{domain_path}' missing TASK_QUEUE. Skipping.")
                continue
            
            if not activities:
                print(f"    [WARN] Domain '{domain_path}' has no activities.")
                continue
            
            # 按task_queue收集activities
            if task_queue not in activities_by_queue:
                activities_by_queue[task_queue] = []
            activities_by_queue[task_queue].extend(activities)
            
            print(f"    [SUCCESS] Registered {len(activities)} activities to '{task_queue}'")
            
        except ImportError as e:
            print(f"    [ERROR] Failed to import domain '{domain_path}': {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"    [ERROR] Unexpected error loading '{domain_path}': {e}")
            import traceback
            traceback.print_exc()

    # 步骤2: 合并workflows和activities，为每个task_queue创建worker
    all_queues = set(workflows_by_queue.keys()) | set(activities_by_queue.keys())
    
    for task_queue in all_queues:
        workflow_classes = workflows_by_queue.get(task_queue, [])
        activities = activities_by_queue.get(task_queue, [])
        
        
        if not workflow_classes and not activities:
            print(f"  [SKIP] Queue '{task_queue}' has no workflows or activities")
            continue
        
        print(f"  [WORKER] Creating worker for '{task_queue}': {len(workflow_classes)} workflows, {len(activities)} activities")
        
        # Worker会从Client继承data_converter配置
        workers.append(
            Worker(
                client,
                task_queue=task_queue,
                workflows=workflow_classes,
                activities=activities,
            )
        )



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
