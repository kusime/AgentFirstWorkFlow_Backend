import os
import subprocess
import sys
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Proper package import
# (Assumes script is run from project root)
sys.path.append(os.getcwd()) # Still needed to put root in path if running from subdir? 
# Actually if we run `python db_tools/sync_schema.py` from root, root IS in path.
# But just in case, let's look at `create_test_data.py`... 
# "sys.path.append(os.getcwd())" was removed there? 
# No, I removed the hack for db_tools/out. I still need root in path if it's not there.
# But standard python behavior puts the Current Working Directory in path.
# So if user runs from root, it works.

from db_tools.out.models import Base 


# Load environment variables
load_dotenv()

# Configuration
DB_HOST = "localhost" # Docker mapped to localhost
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "holo_admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "holo_password")
PROD_DB = os.getenv("POSTGRES_DB", "holo_asset_db")
TEMP_DB = "_temp_schema_build"
DBML_FILE = "db_tools/design.dbml"      # Path relative to project root
SCHEMA_FILE = "db_tools/schema.sql"     # Path relative to project root
MODELS_FILE = "db_tools/out/models.py"  # Path relative to project root

SAFE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}"

def run_command(cmd, shell=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(result.stdout)

def main():
    # 0. Compile DBML to SQL (Offline Tool)
    # This ensures schema.sql is always in sync with design.dbml
    print(f"--- Compiling {DBML_FILE} to {SCHEMA_FILE} ---")
    run_command(f"dbml2sql {DBML_FILE} --postgres > {SCHEMA_FILE}")

    # 1. Ensure Local DB is Up-to-Date
    # If a previous run failed/crashed, we might have an unapplied migration on disk.
    print(f"--- Ensuring {PROD_DB} is up-to-date (alembic upgrade head) ---")
    run_command(f"alembic upgrade head")

    # 2. Prepare Temporary Database
    print(f"--- Preparing Temporary Database: {TEMP_DB} ---")
    engine = create_engine(f"{SAFE_URL}/postgres")
    conn = engine.connect()
    conn.execution_options(isolation_level="AUTOCOMMIT")
    
    try:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEMP_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEMP_DB}"))
    finally:
        conn.close()
    
    # 2. Apply Schema to Temp DB
    print(f"--- Applying {SCHEMA_FILE} to {TEMP_DB} ---")
    # Use psql to execute the SQL file
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    # We use subprocess to call psql directly for robust SQL file handling
    cmd = (
        f"psql -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {TEMP_DB} -f {SCHEMA_FILE}"
    )
    # run_command logic slightly adjusted for psql which might not be in shell path if not careful, 
    # but we assume psql is available since we used it before.
    subprocess.check_call(cmd, shell=True, env=env)

    # 3. Generate Models from Temp DB
    print(f"--- Generating {MODELS_FILE} from {TEMP_DB} ---")
    temp_db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{TEMP_DB}"
    
    # sqlacodegen command
    # We redirect output to models.py
    cmd = f"sqlacodegen {temp_db_url} > {MODELS_FILE}"
    # Note: We need to run this in the same conda env, assuming python is in path
    run_command(cmd)

    # 4. Run Alembic Auto-Generate
    # Alembic will load models.py (Desired State) and compare against PROD_DB (Current State)
    print(f"--- Generating Migration (Auto-Generate) ---")
    # We need to capture the output to find the generated file, but alembic prints to stderr/stdout.
    # A simpler way is to check the 'alembic/versions' dir for the newest file, 
    # or just trust the user to look at the logs.
    # Let's run it and then find the new file.
    run_command(f"alembic revision --autogenerate -m 'sync_schema_{int(time.time())}'")

    # Find the latest migration file
    versions_dir = "alembic/versions"
    files = [os.path.join(versions_dir, f) for f in os.listdir(versions_dir) if f.endswith(".py")]
    latest_file = max(files, key=os.path.getmtime) if files else None

    if latest_file:
        print(f"\n\u26a0\ufe0f  Safe Check: Migration file generated at: {latest_file}")
        print("    Please review this file to ensure NO DATA LOSS (e.g., check for 'op.drop_table').")
        
        # In a real script we might cat the file here, but for now just prompt.
        print(f"    Content preview (upgrade function):")
        with open(latest_file, 'r') as f:
            content = f.read()
            # Simple heuristic to show upgrade part
            if "def upgrade" in content:
                start = content.index("def upgrade")
                print(content[start:start+500] + "...\n")
            else:
                print("    (Could not parse upgrade function, please check file manually)\n")

        confirmation = input(">>> Do you want to apply these changes to the PRODUCTION database? (y/N): ")
        if confirmation.lower() != 'y':
            print("--- \u274c Operation Cancelled. Migration created but NOT applied. ---")
            sys.exit(0)

    # 5. Apply Migration to Prod DB
    print(f"--- Applying Migration to {PROD_DB} ---")
    run_command(f"alembic upgrade head")

    # 6. Cleanup
    print(f"--- Cleaning up {TEMP_DB} ---")
    conn = engine.connect()
    conn.execution_options(isolation_level="AUTOCOMMIT")
    try:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEMP_DB}"))
    finally:
        conn.close()

    print("--- \u2705 Sync Complete ---")

if __name__ == "__main__":
    main()
