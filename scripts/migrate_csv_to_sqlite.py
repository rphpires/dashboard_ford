# scripts/migrate_csv_to_sqlite.py
# Script to migrate EJA data from CSV to SQLite database
from data.local_db_handler import LocalDatabaseHandler
from utils.tracer import trace, report_exception
import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate_csv_to_sqlite(csv_path=None, overwrite=True):
    """
    Migrates EJA data from CSV to SQLite database.

    Args:
        csv_path (str, optional): Path to the CSV file.
                                 If None, uses the default CSV file.
        overwrite (bool): Whether to overwrite existing data in the database.

    Returns:
        bool: True if migration was successful, False otherwise.
    """
    try:
        # Get default CSV path if not provided
        if csv_path is None:
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "aux_files", "eja_simplificado.csv")

        # Check if CSV file exists
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return False

        print(f"Starting migration from '{csv_path}' to SQLite database...")

        # Create database handler
        db_handler = LocalDatabaseHandler()

        # Create backup of database before migration
        print("Creating database backup...")
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"db_backup_before_migration_{timestamp}.sqlite")

        # Only create backup if the database already exists
        db_path = db_handler.db_path
        if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
            db_handler.backup_database(backup_file)
            print(f"Database backup created: {backup_file}")

        # Import CSV data
        print(f"Importing data with overwrite={overwrite}...")
        result = db_handler.import_ejas_from_csv(csv_path, overwrite=overwrite)

        if 'error' in result:
            print(f"Error during migration: {result['error']}")
            return False

        print("\nMigration summary:")
        if overwrite:
            print(f"- {result.get('imported', 0)} records imported (replaced all existing data).")
        else:
            print(f"- {result.get('imported', 0)} new records added.")
            print(f"- {result.get('updated', 0)} existing records updated.")
            print(f"- {result.get('skipped', 0)} records skipped.")

        print("\nMigration completed successfully!")
        return True

    except Exception as e:
        report_exception(e)
        print(f"Error during migration: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Migrate EJA data from CSV to SQLite database')
    parser.add_argument('--csv', help='Path to the CSV file (defaults to aux_files/eja_simplificado.csv)')
    parser.add_argument('--keep-existing', action='store_true',
                        help='Keep existing data and only add new/update existing records')

    args = parser.parse_args()

    # Confirm before proceeding
    if not args.keep_existing:
        confirm = input("WARNING: This will overwrite all existing data in the database. Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return

    # Run migration
    success = migrate_csv_to_sqlite(args.csv, overwrite=not args.keep_existing)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
