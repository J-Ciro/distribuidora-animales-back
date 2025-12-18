#!/usr/bin/env python3
"""
Migration Script for Distribuidora Perros y Gatos
Executes all pending database migrations
"""

import sys
import os
import importlib.util

# Calculate paths
# In Docker: script is at /app/app/scripts/migrate.py
# Locally: script is at backend/api/app/scripts/migrate.py
__file__abs = os.path.abspath(__file__)
script_dir = os.path.dirname(__file__abs)  # .../scripts
app_dir = os.path.dirname(os.path.dirname(__file__abs))  # .../app (e.g., /app/app)
parent_dir = os.path.dirname(app_dir)  # .../ (parent of app/, e.g., /app)

# Verify app_dir is correct by checking if shared directory exists
# If not, try to find the correct app directory
if not os.path.exists(os.path.join(app_dir, 'shared')):
    # Try alternative: check if parent_dir/app/shared exists (Docker case)
    alt_app_dir = os.path.join(parent_dir, 'app')
    if os.path.exists(os.path.join(alt_app_dir, 'shared')):
        app_dir = alt_app_dir
        # Update parent_dir accordingly
        parent_dir = os.path.dirname(alt_app_dir)

# Add parent_dir to path so 'app' can be imported as a module
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import migrator directly from file path (more reliable)
# Try multiple possible paths in order of likelihood
possible_paths = [
    os.path.join(app_dir, 'shared', 'migrations', 'migrations', 'migrator.py'),  # /app/app/shared/...
    os.path.join(parent_dir, 'app', 'shared', 'migrations', 'migrations', 'migrator.py'),  # /app/app/shared/... (alternative)
]

migrator_path = None
for path in possible_paths:
    if os.path.exists(path):
        migrator_path = path
        break

# Debug: print paths if environment variable is set
if os.getenv('DEBUG_MIGRATIONS'):
    print(f"DEBUG: script_dir = {script_dir}")
    print(f"DEBUG: app_dir = {app_dir}")
    print(f"DEBUG: parent_dir = {parent_dir}")
    for path in possible_paths:
        print(f"DEBUG: {path} exists = {os.path.exists(path)}")

if not migrator_path:
    error_msg = f"Migrator file not found. Tried paths:\n"
    for path in possible_paths:
        error_msg += f"  - {path} (exists: {os.path.exists(path)})\n"
    error_msg += f"Script location: {__file__}\n"
    error_msg += f"Current working directory: {os.getcwd()}\n"
    error_msg += f"app_dir: {app_dir}\n"
    error_msg += f"parent_dir: {parent_dir}"
    raise FileNotFoundError(error_msg)

spec = importlib.util.spec_from_file_location("migrator", migrator_path)
migrator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrator_module)
DatabaseMigrator = migrator_module.DatabaseMigrator


def main():
    """Run database migrations"""
    migrator = DatabaseMigrator()
    success = migrator.apply_all_migrations()
    exit(0 if success else 1)


if __name__ == '__main__':
    main()
