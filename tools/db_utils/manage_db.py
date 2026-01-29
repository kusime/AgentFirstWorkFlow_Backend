#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load env from project root (3 levels up from here if inside tools/db_utils/)
# Or assume run from root. We will handle paths carefully.
load_dotenv()

def run_command(cmd, env=None, cwd=None, capture=True):
    """Executes a shell command."""
    print(f"[CMD] {cmd.replace(os.environ.get('POSTGRES_PASSWORD', 'PASSWORD'), '*****')}")
    result = subprocess.run(
        cmd, 
        shell=True, 
        text=True, 
        capture_output=capture, 
        env=env if env else os.environ.copy(),
        cwd=cwd
    )
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {result.stderr}")
        sys.exit(1)
    return result.stdout

def ensure_temp_db(user, password, host, port, db_name):
    """Creates a clean temporary database."""
    print(f"[INFO] Recreating temp DB: {db_name}")
    safe_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/postgres"
    engine = create_engine(safe_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))
    engine.dispose()

def generate_orm(dbml_path: Path, output_path: Path, db_config: dict):
    """
    Core Logic: DBML -> SQL -> Temp DB -> SQLAlchemy ORM
    Using temp files to keep the workspace clean.
    """
    if not dbml_path.exists():
        print(f"[ERROR] DBML file not found: {dbml_path}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        schema_sql = Path(temp_dir) / "schema.sql"
        
        # 1. DBML -> SQL
        print(f"[STEP 1] Converting DBML to SQL...")
        run_command(f"dbml2sql {dbml_path.absolute()} --postgres > {schema_sql.absolute()}")
        
        # 2. Setup Temp DB
        temp_db = "_holotemp_build"
        ensure_temp_db(
            db_config['user'], db_config['pass'], 
            db_config['host'], db_config['port'], 
            temp_db
        )
        
        # 3. Apply SQL to Temp DB
        print(f"[STEP 2] Applying schema to temp DB...")
        env = os.environ.copy()
        env["PGPASSWORD"] = db_config['pass']
        psql_cmd = (
            f"psql -h {db_config['host']} -p {db_config['port']} "
            f"-U {db_config['user']} -d {temp_db} -f {schema_sql.absolute()}"
        )
        # Using check_call directly for psql ease
        subprocess.check_call(psql_cmd, shell=True, env=env, stdout=subprocess.DEVNULL)
        
        # 4. Generate ORM
        print(f"[STEP 3] Generating SQLAlchemy models via sqlacodegen...")
        db_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['pass']}@{db_config['host']}:{db_config['port']}/{temp_db}"
        
        # Generate to a temp file first
        temp_model = Path(temp_dir) / "models.py"
        
        # Determine strict path to sqlacodegen in current env
        bin_dir = os.path.dirname(sys.executable)
        sqlacodegen_exe = os.path.join(bin_dir, "sqlacodegen")
        
        # Fallback if not found (e.g. windows or weirder setups)
        if not os.path.exists(sqlacodegen_exe):
            sqlacodegen_exe = "sqlacodegen"

        run_command(f"{sqlacodegen_exe} {db_url} > {temp_model.absolute()}")
        
        # 5. Move to validation/output
        # Here we could add post-processing if needed (e.g. strict types)
        # For now, just copy.
        if output_path.exists():
            print(f"[INFO] Overwriting existing: {output_path}")
        
        with open(temp_model, 'r') as src, open(output_path, 'w') as dst:
            dst.write(src.read())
            
        print(f"[SUCCESS] ORM Models generated at: {output_path}")
        
        # Cleanup DB
        ensure_temp_db(
            db_config['user'], db_config['pass'], 
            db_config['host'], db_config['port'], 
            temp_db
        ) # Actually just drop it? reuse the logic to Drop and Create (empty). Or just Drop properly.
        # Simplified: Just leave it, next run cleans it up, or user docker system prune.
        
def run_alembic_sync(alembic_ini: Path, message: str):
    """Refreshes migration script and applies it."""
    
    # Use the current python interpreter to run alembic as a module
    # This guarantees we use the same environment (conda) as this script
    alembic_cmd = f"{sys.executable} -m alembic"

    # 1. Ensure DB is up to date with existing migrations on disk
    print(f"[STEP 4a] Ensuring DB is up-to-date...")
    run_command(f"{alembic_cmd} -c {alembic_ini} upgrade head")

    print(f"[STEP 4b] Running Alembic Auto-Generate...")
    cmd = f"{alembic_cmd} -c {alembic_ini} revision --autogenerate -m '{message}'"
    run_command(cmd)
    
    # 2. Apply the new migration immediately?
    print(f"[STEP 5] Applying new migration...")
    run_command(f"{alembic_cmd} -c {alembic_ini} upgrade head")

def main():
    parser = argparse.ArgumentParser(description="HoloAsset DB Management Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Command: generate-orm
    cmd_gen = subparsers.add_parser("gen-orm", help="Generate SQLAlchemy models from DBML")
    cmd_gen.add_argument("--dbml", default="tools/db_utils/examples/design.dbml", help="Path to DBML file")
    cmd_gen.add_argument("--out", default="tools/db_utils/examples/out/models.py", help="Output path for models.py")
    
    # Command: sync (Full Flow)
    cmd_sync = subparsers.add_parser("sync", help="Generate ORM + Create Migration")
    cmd_sync.add_argument("--dbml", default="tools/db_utils/examples/design.dbml")
    cmd_sync.add_argument("--out", default="tools/db_utils/examples/out/models.py")
    cmd_sync.add_argument("--msg", default="auto_sync", help="Migration message")
    cmd_sync.add_argument("--ini", default="tools/db_utils/alembic/alembic.ini", help="Path to alembic.ini")

    args = parser.parse_args()
    
    # DB Config
    db_config = {
        "host": "localhost",
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "user": os.getenv("POSTGRES_USER", "holo_admin"),
        "pass": os.getenv("POSTGRES_PASSWORD", "holo_password"),
        "name": os.getenv("POSTGRES_DB", "holo_asset_db")
    }

    if args.command in ["gen-orm", "sync"]:
        generate_orm(Path(args.dbml), Path(args.out), db_config)
        
    if args.command == "sync":
        run_alembic_sync(Path(args.ini), args.msg)

if __name__ == "__main__":
    main()
