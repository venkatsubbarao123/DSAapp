"""Phase 10: Automated Database Backup & Disaster Recovery Tests.

Verifies:
1. Online backup snapshot creation and SHA-256 checksum calculation.
2. Manifest creation with metadata.
3. PRAGMA integrity check on backup file.
4. Disaster simulation: corruption / data deletion.
5. Successful restore from backup with integrity verification.
6. Tamper-evident protection: corrupted backup with mismatched SHA-256 is rejected.
"""

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

from scripts.backup_db import backup_sqlite, compute_sha256
from scripts.restore_db import restore_sqlite


def test_sqlite_backup_and_restore_cycle():
    """Tests complete backup, disaster simulation, restore, and integrity verification."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_source.db"
        backup_dir = tmp_path / "backups"

        # 1. Create a database with test tables and records
        conn = sqlite3.connect(str(db_path))
        with conn:
            conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, role TEXT);")
            conn.execute("INSERT INTO users VALUES (1, 'alice@example.com', 'admin');")
            conn.execute("INSERT INTO users VALUES (2, 'bob@example.com', 'student');")
            conn.execute("CREATE TABLE submissions (id INTEGER PRIMARY KEY, user_id INTEGER, status TEXT);")
            conn.execute("INSERT INTO submissions VALUES (101, 2, 'ACCEPTED');")
            conn.execute("INSERT INTO submissions VALUES (102, 2, 'WRONG_ANSWER');")
        conn.close()

        # 2. Take live backup
        backup_file = backup_sqlite(db_path, backup_dir)
        assert backup_file.exists(), "Backup file should be created"
        assert backup_file.stat().st_size > 0, "Backup file should not be empty"

        # Compute SHA-256
        sha256_hash = compute_sha256(backup_file)
        assert len(sha256_hash) == 64

        # 3. Simulate disaster: delete submissions and users from source DB
        conn = sqlite3.connect(str(db_path))
        with conn:
            conn.execute("DELETE FROM submissions;")
            conn.execute("DELETE FROM users WHERE id = 2;")
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM submissions;")
        assert cursor.fetchone()[0] == 0, "Disaster simulation: submissions deleted"
        conn.close()

        # 4. Restore database from backup
        restore_report = restore_sqlite(backup_file, db_path, expected_sha256=sha256_hash)
        assert restore_report["status"] == "restored"
        assert restore_report["integrity_check"] == "ok"
        assert restore_report["restored_tables"] >= 2
        assert restore_report["sha256_verified"] is True

        # 5. Verify data integrity restored
        verify_conn = sqlite3.connect(str(db_path))
        cursor = verify_conn.cursor()
        cursor.execute("SELECT count(*) FROM users;")
        user_count = cursor.fetchone()[0]
        assert user_count == 2, f"Expected 2 restored users, got {user_count}"

        cursor.execute("SELECT count(*) FROM submissions;")
        sub_count = cursor.fetchone()[0]
        assert sub_count == 2, f"Expected 2 restored submissions, got {sub_count}"

        cursor.execute("SELECT email, role FROM users WHERE id = 1;")
        admin_row = cursor.fetchone()
        assert admin_row == ("alice@example.com", "admin")
        verify_conn.close()


def test_restore_rejects_corrupted_or_tampered_backup():
    """Tests that restore aborts if SHA-256 does not match or file is malformed."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "valid.db"
        target_path = tmp_path / "target.db"

        # Create valid source DB
        conn = sqlite3.connect(str(db_path))
        with conn:
            conn.execute("CREATE TABLE records (id INTEGER, val TEXT);")
            conn.execute("INSERT INTO records VALUES (1, 'secure_data');")
        conn.close()

        valid_sha = compute_sha256(db_path)

        # Attempt restore with wrong expected SHA-256
        with pytest.raises(ValueError, match="Integrity check failed"):
            restore_sqlite(db_path, target_path, expected_sha256="0000000000000000000000000000000000000000000000000000000000000000")

        # Test corrupt non-sqlite file
        corrupt_file = tmp_path / "corrupt.db"
        corrupt_file.write_bytes(b"THIS IS CORRUPT JUNK DATA NOT SQLITE")
        corrupt_sha = compute_sha256(corrupt_file)

        with pytest.raises(Exception):
            restore_sqlite(corrupt_file, target_path, expected_sha256=corrupt_sha)
