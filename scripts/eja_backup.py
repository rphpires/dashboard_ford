# scripts/eja_backup.py
# Script for backup and restoration of EJA data with SQLite support
from utils.tracer import trace, report_exception
from data.eja_manager import EJAManager
import os
import sys
import argparse
import datetime
import shutil

# Adicionar o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SQLite database handler if available
try:
    from data.local_db_handler import LocalDatabaseHandler
    _HAS_SQLITE = True
except ImportError:
    _HAS_SQLITE = False


def create_backup():
    """Creates a backup of current EJA data"""
    try:
        # Create backup directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # CSV backup
        eja_manager = EJAManager()
        csv_backup_file = os.path.join(backup_dir, f"eja_backup_{timestamp}.csv")
        csv_path = eja_manager.export_csv(csv_backup_file)

        # SQLite backup (if available)
        db_backup_file = None
        if _HAS_SQLITE:
            db_handler = LocalDatabaseHandler()
            db_backup_file = os.path.join(backup_dir, f"db_backup_{timestamp}.sqlite")
            db_backup_result = db_handler.backup_database(db_backup_file)

            # If the backup failed, report it but continue
            if db_backup_file != db_backup_result:
                print(f"Warning: SQLite backup failed - {db_backup_result}")
                db_backup_file = None

        # Report results
        backup_files = []
        if csv_path and os.path.exists(csv_path):
            backup_files.append(csv_path)
        if db_backup_file and os.path.exists(db_backup_file):
            backup_files.append(db_backup_file)

        if backup_files:
            print("Backup(s) created successfully:")
            for file in backup_files:
                print(f"- {file}")
            return backup_files
        else:
            print("No backups were created successfully.")
            return None
    except Exception as e:
        report_exception(e)
        print(f"Error creating backup: {str(e)}")
        return None


def restore_from_backup(backup_file, overwrite=True):
    """Restores EJA data from a backup file"""
    try:
        if not os.path.exists(backup_file):
            print(f"Backup file not found: {backup_file}")
            return False

        file_ext = os.path.splitext(backup_file)[1].lower()

        # Restore from CSV
        if file_ext == '.csv':
            eja_manager = EJAManager()
            result = eja_manager.import_csv(backup_file, overwrite=overwrite)

            if 'error' in result:
                print(f"Error restoring from CSV: {result['error']}")
                return False

            print("Restored successfully from CSV!")
            if overwrite:
                print(f"- {result.get('imported', 0)} records imported.")
            else:
                print(f"- {result.get('imported', 0)} added.")
                print(f"- {result.get('updated', 0)} updated.")
                print(f"- {result.get('skipped', 0)} skipped.")

            return True

        # Restore from SQLite backup
        elif file_ext == '.sqlite':
            if not _HAS_SQLITE:
                print("SQLite support is not available. Cannot restore from database backup.")
                return False

            db_handler = LocalDatabaseHandler()
            result = db_handler.restore_database(backup_file)

            if result:
                print(f"Database restored successfully from {backup_file}")
                return True
            else:
                print(f"Failed to restore database from {backup_file}")
                return False

        else:
            print(f"Unsupported backup file format: {file_ext}")
            print("Expected .csv or .sqlite file")
            return False

    except Exception as e:
        report_exception(e)
        print(f"Error restoring backup: {str(e)}")
        return False


def list_backups():
    """Lists all available backups"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        if not os.path.exists(backup_dir):
            print("No backups found.")
            return []

        # Find all backup files
        csv_backups = [f for f in os.listdir(backup_dir) if f.startswith("eja_backup_") and f.endswith(".csv")]
        db_backups = [f for f in os.listdir(backup_dir) if f.startswith("db_backup_") and f.endswith(".sqlite")]

        if not csv_backups and not db_backups:
            print("No backups found.")
            return []

        # Print CSV backups
        print("\nAvailable backups:")
        backups = []

        if csv_backups:
            print("\nCSV Backups:")
            for i, backup in enumerate(sorted(csv_backups), 1):
                # Extract timestamp from filename
                timestamp = backup.replace("eja_backup_", "").replace(".csv", "")
                try:
                    date_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_date = date_time.strftime("%d/%m/%Y %H:%M:%S")
                except Exception:
                    formatted_date = timestamp

                print(f"CSV-{i}. {backup} ({formatted_date})")
                backups.append({"type": "csv", "path": os.path.join(backup_dir, backup), "display": f"CSV-{i}"})

        # Print SQLite backups
        if db_backups:
            print("\nSQLite Backups:")
            for i, backup in enumerate(sorted(db_backups), 1):
                # Extract timestamp from filename
                timestamp = backup.replace("db_backup_", "").replace(".sqlite", "")
                try:
                    date_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_date = date_time.strftime("%d/%m/%Y %H:%M:%S")
                except Exception:
                    formatted_date = timestamp

                print(f"DB-{i}. {backup} ({formatted_date})")
                backups.append({"type": "sqlite", "path": os.path.join(backup_dir, backup), "display": f"DB-{i}"})

        print()  # Blank line
        return backups
    except Exception as e:
        report_exception(e)
        print(f"Error listing backups: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(description='EJA Backup Manager with SQLite support')
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Backup command
    # backup_parser = subparsers.add_parser('backup', help='Create a backup of current EJA data')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore EJA data from a backup')
    restore_parser.add_argument('file', nargs='?', help='Backup file to restore from')
    restore_parser.add_argument('--keep-existing', action='store_true',
                                help='Keep existing data and only add new/update existing (CSV only)')

    # List command
    # list_parser = subparsers.add_parser('list', help='List all available backups')

    args = parser.parse_args()

    if args.command == 'backup':
        create_backup()

    elif args.command == 'restore':
        if not args.file:
            # If no file specified, list available backups and ask
            backups = list_backups()
            if not backups:
                return

            while True:
                try:
                    choice = input("Enter the backup ID to restore (e.g., 'CSV-1' or 'DB-2') or 'q' to quit: ")
                    if choice.lower() == 'q':
                        return

                    # Find the selected backup
                    selected_backup = None
                    for backup in backups:
                        if backup["display"] == choice:
                            selected_backup = backup
                            break

                    if selected_backup:
                        backup_path = selected_backup["path"]
                        break
                    else:
                        print("Invalid backup ID. Try again.")
                except ValueError:
                    print("Invalid input. Enter a backup ID or 'q'.")
        else:
            backup_path = args.file

        # Confirm overwrite if necessary
        if backup_path.endswith('.csv') and not args.keep_existing:
            confirm = input("WARNING: This will overwrite all existing data. Continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return

        # Restore from the backup
        restore_from_backup(backup_path, overwrite=not args.keep_existing)

    elif args.command == 'list':
        list_backups()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
