"""Production-Grade Database Backup Utility for DSAapp.

Supports both SQLite (local development / testing) and PostgreSQL (production).
Generates SHA-256 verified, timestamped backup archives with metadata manifest.
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hex digest of a file in streaming chunks."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def backup_sqlite(db_path: Path, output_dir: Path) -> Path:
    """Takes a transaction-consistent live snapshot of SQLite using SQLite backup API."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"dsaapp_backup_{timestamp}.db"
    dest_path = output_dir / backup_filename

    output_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        # Create an empty db file or handle missing
        raise FileNotFoundError(f"Source SQLite database not found at {db_path}")

    # Use SQLite online backup API to ensure transaction consistency without file locking
    src_conn = sqlite3.connect(str(db_path))
    dest_conn = sqlite3.connect(str(dest_path))
    try:
        with dest_conn:
            src_conn.backup(dest_conn, pages=100)
    finally:
        dest_conn.close()
        src_conn.close()

    return dest_path


def backup_postgres(db_url: str, output_dir: Path) -> Path:
    """Executes pg_dump for PostgreSQL database."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"dsaapp_pg_backup_{timestamp}.sql"
    dest_path = output_dir / backup_filename
    output_dir.mkdir(parents=True, exist_ok=True)

    # Standard pg_dump execution
    cmd = ["pg_dump", "--dbname", db_url, "-f", str(dest_path), "--no-owner", "--no-acl"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed with exit code {result.returncode}: {result.stderr}")

    return dest_path


def create_backup(target_dir: str = "backups") -> dict:
    """Executes database backup based on configured DATABASE_URL."""
    output_path = Path(target_dir).resolve()
    db_url = settings.DATABASE_URL

    print(f"[*] Starting DSAapp database backup...")
    print(f"[*] Target Directory: {output_path}")

    dialect = "sqlite" if "sqlite" in db_url.lower() else "postgresql"

    if dialect == "sqlite":
        # Extract relative or absolute sqlite file path
        # sqlite+aiosqlite:///./dsaapp.db -> ./dsaapp.db
        clean_path = db_url.split("///")[-1]
        source_db = Path(clean_path).resolve()
        if not source_db.is_absolute():
            source_db = (ROOT_DIR / clean_path).resolve()
        
        # If source db does not exist, initialize or check root
        if not source_db.exists():
            root_dsaapp_db = ROOT_DIR / "dsaapp.db"
            if root_dsaapp_db.exists():
                source_db = root_dsaapp_db

        backup_file = backup_sqlite(source_db, output_path)
    else:
        backup_file = backup_postgres(db_url, output_path)

    file_size_bytes = backup_file.stat().st_size
    sha256_hash = compute_sha256(backup_file)

    manifest = {
        "backup_file": backup_file.name,
        "backup_path": str(backup_file),
        "dialect": dialect,
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "size_bytes": file_size_bytes,
        "sha256": sha256_hash,
        "app_version": "1.0.0-final",
        "environment": settings.ENVIRONMENT,
    }

    manifest_path = output_path / f"{backup_file.stem}_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Backup completed successfully: {backup_file.name}")
    print(f"[+] Size: {file_size_bytes} bytes | SHA-256: {sha256_hash[:16]}...")
    print(f"[+] Manifest written: {manifest_path.name}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DSAapp Database Backup Utility")
    parser.add_argument("--outdir", default="backups", help="Destination folder for backup files")
    args = parser.parse_args()
    create_backup(args.outdir)
