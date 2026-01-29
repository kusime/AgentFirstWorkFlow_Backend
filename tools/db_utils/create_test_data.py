import os
import sys
import datetime
import random
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Proper package import (Requires running from project root)
from db_tools.out.models import Base, Users, Locations, Assets, MaintenanceLogs, AssetAssignments

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
        # Flush to get ID, but don't commit yet so we can rollback entire transaction if needed
        session.flush() 
        return instance, True

def create_data():
    engine = create_engine(DATABASE_URL)
    session = Session(engine)
    print("--- Creating Comprehensive Test Data ---")

    try:
        # 1. Location
        loc_name = f"Warehouse Sector {random.randint(1, 99)}"
        location, created = get_or_create(session, Locations, name=loc_name)
        if created:
            location.address = "Industrial Zone 42"
            print(f"✅ Created Location: {location.name} (ID: {location.id})")
        else:
            print(f"ℹ️  Found Location: {location.name} (ID: {location.id})")

        # 2. User
        username = f"technician_{random.randint(100, 999)}"
        user, created = get_or_create(session, Users, username=username)
        if created:
            user.role = "Senior Technician"
            user.created_at = datetime.datetime.now()
            print(f"✅ Created User: {user.username} (ID: {user.id})")
        else:
            print(f"ℹ️  Found User: {user.username} (ID: {user.id})")

        # 3. Asset
        serial_no = f"SN-{random.randint(10000, 99999)}"
        asset, created = get_or_create(session, Assets, serial_number=serial_no)
        if created:
            asset.name = "Holographic Projector X1"
            asset.status = "active"
            asset.location_id = location.id
            asset.cost = 12500.50
            asset.specifications = {"resolution": "8K", "lumens": 5000}
            asset.warranty_info = "3 Years Gold Support"
            print(f"✅ Created Asset: {asset.name} (SN: {asset.serial_number}, ID: {asset.id})")
        else:
            print(f"ℹ️  Found Asset: {asset.name} (SN: {asset.serial_number}, ID: {asset.id})")

        # 4. Asset Assignment
        # Check if already assigned
        assignment = session.execute(select(AssetAssignments).filter_by(asset_id=asset.id, user_id=user.id)).scalars().first()
        if not assignment:
            assignment = AssetAssignments(
                asset_id=asset.id,
                user_id=user.id,
                assigned_at=datetime.datetime.now()
            )
            session.add(assignment)
            print(f"✅ Assigned Asset {asset.id} to User {user.id}")
        else:
            print(f"ℹ️  Asset {asset.id} already assigned to User {user.id}")

        # 5. Maintenance Log
        log = MaintenanceLogs(
            asset_id=asset.id,
            technician_name=user.username,
            description="Initial calibration and firmware update.",
            service_date=datetime.date.today(),
            cost=150.00,
            details={"firmware_version": "2.5.1"}
        )
        session.add(log)
        print(f"✅ Added Maintenance Log for Asset {asset.id}")

        session.commit()
        print("\n--- \u2728 All Data Committed Successfully ---")

    except Exception as e:
        session.rollback()
        print(f"\n\u274c Error creating data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_data()
