import inspect
from temporalio import activity
from app.domains.pizza.gateway import PizzaActivitiesImpl

# 实例化
impl = PizzaActivitiesImpl()

print("Inspecting PizzaActivitiesImpl instance methods:")
for name, method in inspect.getmembers(impl, predicate=inspect.ismethod):
    if name.startswith("_"): continue
    
    print(f"\nMethod: {name}")
    print(f"  Type: {type(method)}")
    print(f"  Dir: {dir(method)}")
    
    # Check for common temporal attributes
    if hasattr(method, "_temporal_activity_definition"):
        print("  FOUND: _temporal_activity_definition")
    if hasattr(method, "__temporal_activity_definition"):
        print("  FOUND: __temporal_activity_definition")
    
    # Try to see if we can detect it via temporalio internals?
    # Actually, let's just dump all attributes that contain 'temporal'
    for attr in dir(method):
        if 'temporal' in attr:
            print(f"  POTENTIAL MARKER: {attr}")

