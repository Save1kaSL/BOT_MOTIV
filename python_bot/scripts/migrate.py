#!/usr/bin/env python3
"""Применить миграции БД: python scripts/migrate.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.migrations import run_migrations

if __name__ == "__main__":
    run_migrations()
    print("Migrations OK")
