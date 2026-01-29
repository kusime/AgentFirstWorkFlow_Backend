import os
import sys
import datetime
import random
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Proper package import (Requires running from project root via PYTHONPATH=.)
from tools.db_utils.examples.out.models import Base, Currencytype, Account, Holetype, Theholelevel, Hole

# Load env to get connection string components
load_dotenv()

DB_HOST = "localhost"
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "holo_admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "holo_password")
PROD_DB = os.getenv("POSTGRES_DB", "holo_asset_db")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{PROD_DB}"

def get_or_create(session, model, **kwargs):
    """Simple get_or_create helper."""
    instance = session.execute(select(model).filter_by(**kwargs)).scalars().first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush() 
        return instance, True

def create_data():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    session = Session(engine)
    print("--- Creating Financial Test Data (Double Entry / Hole Theory) ---")

    try:
        # 1. Currency Types
        usd, _ = get_or_create(session, Currencytype, name="USD", id=1) # ID explicitly set for example
        eur, _ = get_or_create(session, Currencytype, name="EUR", id=2)
        print(f"✅ Currencies: {usd.name}, {eur.name}")

        # 2. Hole Types & Levels
        h_type, _ = get_or_create(session, Holetype, name="Standard Gap", id=1)
        h_level, _ = get_or_create(session, Theholelevel, name="Surface", level="1", id=1)
        print(f"✅ Metadata: {h_type.name}, Level {h_level.level}")

        # 3. Account
        # Account needs a currency type
        acc_name = f"Main Vault {random.randint(100, 999)}"
        account, created = get_or_create(session, Account, name=acc_name, currency_type=usd.id)
        if created:
            print(f"✅ Created Account: {account.name} (ID: {account.id})")
        else:
            print(f"ℹ️  Found Account: {account.name}")

        # 4. Create a Hole (Transaction/Anomoly)
        # Hole uses UUID for ID
        hole_id = uuid.uuid4()
        hole = Hole(
            id=hole_id,
            detail="Unexpected variance in sector 7",
            amount=1000.50,
            account=account.id,
            currency_type=usd.id,
            hole_type=h_type.id,
            the_hole_level=h_level.id,
            created_at=datetime.datetime.now(),
            is_currency_locked=False
        )
        session.add(hole)
        print(f"✅ Created Hole: {hole.detail} (Amount: {hole.amount})")

        session.commit()
        print("\n--- \u2728 All Data Committed Successfully ---")

    except Exception as e:
        session.rollback()
        print(f"\n\u274c Error creating data: {e}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    create_data()
