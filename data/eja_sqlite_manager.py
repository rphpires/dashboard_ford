# data/eja_sqlite_manager.py
# SQLite-based implementation of EJA Manager for zeentech VEV Dashboard
from data.local_db_handler import LocalDatabaseHandler
from utils.tracer import trace, report_exception
import os
import pandas as pd
import datetime


class EJASQLiteManager:
    """
    SQLite-based implementation for managing EJA data.
    This class provides the same interface as the original EJAManager,
    but stores data in SQLite instead of CSV.
    """

    def __init__(self):
        """Initialize the SQLite-based EJA manager."""
        self.db = LocalDatabaseHandler()
        self._ensure_db_initialized()

    def _ensure_db_initialized(self):
        """Ensure the database is initialized and has the correct schema."""
        # Check if the database already has data
        ejas = self.db.get_all_ejas()
        if not ejas:
            # Database is empty, try to import from the CSV file
            self._import_from_legacy_csv()

    def _import_from_legacy_csv(self):
        """Import data from the legacy CSV file if it exists."""
        try:
            # Check for the legacy CSV file
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    "aux_files", "eja_simplificado.csv")
            if os.path.exists(csv_path):
                trace(f"Importing data from legacy CSV file: {csv_path}", color="yellow")
                # Import the CSV data into the database
                self.import_csv(csv_path, overwrite=True)
                trace("Legacy CSV data successfully imported to SQLite database", color="green")
            else:
                trace("No legacy CSV file found, starting with empty database", color="yellow")
        except Exception as e:
            report_exception(e)
            trace(f"Error importing legacy CSV data: {str(e)}", color="red")

    def get_all_ejas(self):
        """Retrieve all EJAs from the database."""
        try:
            ejas = self.db.get_all_ejas()
            # Transform field names to match the expected format
            for eja in ejas:
                # Rename fields to match the original format
                if 'id' in eja:
                    eja['Nº'] = eja['id']
                if 'eja_code' in eja:
                    eja['EJA CODE'] = eja['eja_code']
                if 'title' in eja:
                    eja['TITLE'] = eja['title']
                if 'new_classification' in eja:
                    eja['NEW CLASSIFICATION'] = eja['new_classification']
                if 'classification' in eja:
                    eja['CLASSIFICATION'] = eja['classification']
            return ejas
        except Exception as e:
            report_exception(e)
            trace(f"Error retrieving EJAs from database: {str(e)}", color="red")
            return []

    def search_ejas(self, search_term=None, eja_code=None):
        """
        Search for EJAs by title or code.

        Args:
            search_term (str): Term to search for in the title
            eja_code (int/str): Specific EJA code to search for

        Returns:
            list: List of matching EJA records
        """
        try:
            # Convert to integers if needed
            if eja_code and not isinstance(eja_code, int):
                try:
                    eja_code = int(eja_code)
                except (ValueError, TypeError):
                    eja_code = None

            # Use the database search function
            results = self.db.search_ejas(
                search_term=search_term,
                eja_code=eja_code
            )

            # Transform field names to match the expected format
            for eja in results:
                if 'id' in eja:
                    eja['Nº'] = eja['id']
                if 'eja_code' in eja:
                    eja['EJA CODE'] = eja['eja_code']
                if 'title' in eja:
                    eja['TITLE'] = eja['title']
                if 'new_classification' in eja:
                    eja['NEW CLASSIFICATION'] = eja['new_classification']
                if 'classification' in eja:
                    eja['CLASSIFICATION'] = eja['classification']

            return results
        except Exception as e:
            report_exception(e)
            trace(f"Error searching EJAs: {str(e)}", color="red")
            return []

    def get_eja_by_id(self, row_id):
        """
        Get an EJA by its ID.

        Args:
            row_id (int): ID of the EJA record

        Returns:
            dict: EJA record or None if not found
        """
        try:
            # Convert to integer if needed
            if not isinstance(row_id, int):
                try:
                    row_id = int(row_id)
                except (ValueError, TypeError):
                    return None

            eja = self.db.get_eja_by_id(row_id)
            if eja:
                # Transform field names to match the expected format
                if 'id' in eja:
                    eja['Nº'] = eja['id']
                if 'eja_code' in eja:
                    eja['EJA CODE'] = eja['eja_code']
                if 'title' in eja:
                    eja['TITLE'] = eja['title']
                if 'new_classification' in eja:
                    eja['NEW CLASSIFICATION'] = eja['new_classification']
                if 'classification' in eja:
                    eja['CLASSIFICATION'] = eja['classification']
            return eja
        except Exception as e:
            report_exception(e)
            trace(f"Error retrieving EJA by ID: {str(e)}", color="red")
            return None

    def get_eja_by_code(self, eja_code):
        """
        Get an EJA by its code.

        Args:
            eja_code (int): EJA code

        Returns:
            dict: EJA record or None if not found
        """
        try:
            # Convert to integer if needed
            if not isinstance(eja_code, int):
                try:
                    eja_code = int(eja_code)
                except (ValueError, TypeError):
                    return None

            eja = self.db.get_eja_by_code(eja_code)
            if eja:
                # Transform field names to match the expected format
                if 'id' in eja:
                    eja['Nº'] = eja['id']
                if 'eja_code' in eja:
                    eja['EJA CODE'] = eja['eja_code']
                if 'title' in eja:
                    eja['TITLE'] = eja['title']
                if 'new_classification' in eja:
                    eja['NEW CLASSIFICATION'] = eja['new_classification']
                if 'classification' in eja:
                    eja['CLASSIFICATION'] = eja['classification']
            return eja
        except Exception as e:
            report_exception(e)
            trace(f"Error retrieving EJA by code: {str(e)}", color="red")
            return None

    def add_eja(self, eja_data):
        """
        Adiciona um novo EJA ao banco de dados SQLite

        Args:
            eja_data (dict): Dados do EJA

        Returns:
            int: ID do EJA adicionado ou dict com erro
        """
        # Validar campos obrigatórios
        if not eja_data.get('eja_code') or not eja_data.get('title'):
            return {'error': 'Código EJA e Título são obrigatórios'}

        try:
            # Verificar se já existe um EJA com o mesmo código
            return self.db.add_eja(eja_data)

        except Exception:
            return {'exception': 'Exception on eja creating process.'}

    def update_eja(self, row_id, eja_data):
        """
        Update an existing EJA.

        Args:
            row_id (int): ID of the EJA to update
            eja_data (dict): New EJA data

        Returns:
            dict: Updated EJA data or error message
        """
        try:
            # Convert to integer if needed
            if not isinstance(row_id, int):
                try:
                    row_id = int(row_id)
                except (ValueError, TypeError):
                    return {"error": f"Invalid ID: {row_id}"}

            # Transform field names to match the database format
            db_eja_data = {}
            if 'EJA CODE' in eja_data:
                db_eja_data['eja_code'] = eja_data['EJA CODE']
            if 'TITLE' in eja_data:
                db_eja_data['title'] = eja_data['TITLE']
            if 'NEW CLASSIFICATION' in eja_data:
                db_eja_data['new_classification'] = eja_data['NEW CLASSIFICATION']
            if 'CLASSIFICATION' in eja_data:
                db_eja_data['classification'] = eja_data['CLASSIFICATION']

            # Update the EJA in the database
            result = self.db.update_eja(row_id, db_eja_data)

            # If successful, transform the result to match the expected format
            if result and 'error' not in result:
                if 'id' in result:
                    result['Nº'] = result['id']
                if 'eja_code' in result:
                    result['EJA CODE'] = result['eja_code']
                if 'title' in result:
                    result['TITLE'] = result['title']
                if 'new_classification' in result:
                    result['NEW CLASSIFICATION'] = result['new_classification']
                if 'classification' in result:
                    result['CLASSIFICATION'] = result['classification']

            return result
        except Exception as e:
            report_exception(e)
            trace(f"Error updating EJA: {str(e)}", color="red")
            return {"error": str(e)}

    def delete_eja(self, row_id):
        """
        Delete an EJA by ID.

        Args:
            row_id (int): ID of the EJA to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Convert to integer if needed
            if not isinstance(row_id, int):
                try:
                    row_id = int(row_id)
                except (ValueError, TypeError):
                    return False

            # Delete the EJA from the database
            return self.db.delete_eja(row_id)
        except Exception as e:
            report_exception(e)
            trace(f"Error deleting EJA: {str(e)}", color="red")
            return False

    def import_csv(self, file_path, overwrite=True):
        """
        Import EJAs from a CSV file.

        Args:
            file_path (str): Path to the CSV file
            overwrite (bool): Whether to overwrite existing data

        Returns:
            dict: Import results with counts
        """
        try:
            # Use the database's import function
            result = self.db.import_ejas_from_csv(file_path, overwrite=overwrite)
            return result
        except Exception as e:
            report_exception(e)
            trace(f"Error importing CSV: {str(e)}", color="red")
            return {"error": str(e)}

    def export_csv(self, file_path=None):
        """
        Export EJAs to a CSV file.

        Args:
            file_path (str, optional): Path to save the CSV file

        Returns:
            str: Path to the exported file or error message
        """
        try:
            # Use the database's export function
            return self.db.export_ejas_to_csv(file_path)
        except Exception as e:
            report_exception(e)
            trace(f"Error exporting CSV: {str(e)}", color="red")
            return f"Error exporting CSV: {str(e)}"

    def get_all_classifications(self):
        """Get all unique classifications."""
        try:
            return self.db.get_all_classifications()
        except Exception as e:
            report_exception(e)
            trace(f"Error getting classifications: {str(e)}", color="red")
            return []

# Helper function to get an instance of the EJA SQLite Manager


def get_eja_sqlite_manager():
    """Returns an instance of the EJA SQLite Manager."""
    return EJASQLiteManager()
