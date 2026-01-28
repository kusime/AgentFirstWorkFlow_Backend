from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError

# --- Case 1: Dataclass (Loose) ---
@dataclass
class PizzaItemDC:
    flavor: str
    quantity: int

# --- Case 2: Pydantic (Strict) ---
class PizzaItemPY(BaseModel):
    flavor: str
    quantity: int = Field(gt=0, description="Quantity must be positive")

def demo():
    bad_json_data = {"flavor": "Pineapple", "quantity": -5}

    print("--- 1. Dataclass Behavior ---")
    # Dataclass will happily accept -5
    # The bug will propagate deep into your Activity logic before exploding (or worse, charging negative money)
    try:
        item_dc = PizzaItemDC(**bad_json_data)
        print(f"Danger! Created invalid order: {item_dc}")
        print("Result: Bug propagates to downstream logic.\n")
    except Exception as e:
        print(f"Caught: {e}\n")

    print("--- 2. Pydantic Behavior ---")
    # Pydantic will stop it at the gate
    try:
        item_py = PizzaItemPY(**bad_json_data)
        print(f"Created: {item_py}")
    except ValidationError as e:
        print("Success! Blocked invalid data.")
        print(f"Error: {e}")
        print("Result: Workflow fails fast with clear error, protecting the DB.")

if __name__ == "__main__":
    demo()
