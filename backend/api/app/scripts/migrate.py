#!/usr/bin/env python3
"""
Migration Script for Distribuidora Perros y Gatos
Executes all pending database migrations
"""

import sys
import os

# Add the app directory to Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations.migrator import DatabaseMigrator


def main():
    """Run database migrations"""
    migrator = DatabaseMigrator()
    success = migrator.apply_all_migrations()
    exit(0 if success else 1)


if __name__ == '__main__':
    main()
