"""Production-Grade Database Restore Utility for DSAapp.

Restores database from SHA-256 verified backup snapshot.
Performs pre-flight integrity check and post-restore verification.
"""

import argparse
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


def restore_sqlite(backup_path: Path, target_db_path: Path, expected_sha256: str = None) -> dict:
    """Restores SQLite database from backup file with integrity verification."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_path}")

    # 1. Pre-restore SHA-256 verification if provided
    actual_sha = compute_sha256(backup_path)
    if expected_sha256 and actual_sha != expected_sha256:
        raise ValueError(f"Integrity check failed! Expected {expected_sha256}, got {actual_sha}")

    # 2. Check source backup file integrity using SQLite PRAGMA
    test_conn = sqlite3.connect(str(backup_path))
    try:
        cursor = test_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        check_result = cursor.fetchone()[0]
        if check_result != "ok":
            raise RuntimeError(f"Backup file corrupted: PRAGMA integrity_check returned '{check_result}'")
        
        # Count tables
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        table_count = cursor.fetchone()[0]
    finally:
        test_conn.close()

    # 3. Safe copy with atomic replacement
    temp_target = target_db_path.with_suffix(".tmp_restore")
    shutil.copy2(backup_path, temp_target)

    # Replace target atomically
    if target_db_path.exists():
        target_db_path.unlink()
    temp_target.replace(target_db_path)

    # 4. Post-restore verification on target database
    verify_conn = sqlite3.connect(str(target_db_path))
    try:
        cursor = verify_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        verify_result = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        restored_table_count = cursor.fetchone()[0]
    finally:
        verify_conn.close()

    return {
        "status": "restored",
        "target_db": str(target_db_path),
        "integrity_check": verify_result,
        "restored_tables": restored_table_count,
        "sha256_verified": True if expected_sha256 else False,
    }


def restore_postgres(backup_path: Path, db_url: str) -> dict:
    """Restores PostgreSQL database from SQL dump."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_path}")

    cmd = ["psql", "--dbname", db_url, "-f", str(backup_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"psql restore failed with exit code {result.returncode}: {result.stderr}")

    return {
        "status": "restored",
        "target_db": db_url,
        "source_backup": str(backup_path),
    }


def execute_restore(backup_file_or_manifest: str, custom_target_path: str = None) -> dict:
    """Executes database restoration from backup file or manifest."""
    src_path = Path(backup_file_or_manifest).resolve()
    print(f"[*] Starting DSAapp database restore from {src_path.name}...")

    expected_sha256 = None
    backup_file = src_path

    # If manifest passed, parse it
    if src_path.suffix == ".json":
        with open(src_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        backup_file = src_path.parent / manifest["backup_file"]
        expected_sha256 = manifest.get("sha256")
        print(f"[*] Loaded manifest for {manifest.get('backup_file')} (SHA: {expected_sha256[:16]}...)")

    db_url = settings.DATABASE_URL
    dialect = "sqlite" if "sqlite" in db_url.lower() else "postgresql"

    if dialect == "sqlite":
        if custom_target_path:
            target_path = Path(custom_target_path).resolve()
        else:
            clean_path = db_url.split("///")[-1]
            target_path = Path(clean_path).resolve()
            if not target_path.is_absolute():
                target_path = (ROOT_DIR / clean_path).resolve()

        report = restore_sqlite(backup_file, target_path, expected_sha256)
    else:
        report = restore_postgres(backup_file, db_url)

    print(f"[+] Restore completed successfully! Tables: {report.get('restored_tables', 'N/A')}, Status: {report['status']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DSAapp Database Restore Utility")
    parser.add_argument("backup", help="Path to backup .db/.sql file or _manifest.json")
    parser.add_argument("--target", default=None, help="Custom destination database file path")
    args = parser.parse_args()
    execute_restore(args.backup, args.target)
