from app.domains.hello.workflows import GreetingWorkflow
from app.domains.hello.activities import say_hello

# Define Component Bundles
workflows = [GreetingWorkflow]
activities = [say_hello]
TASK_QUEUE = "hello-task-queue"
