# data/tracks_usage_manager.py
from utils.tracer import trace, report_exception
from data.local_db_handler import get_db_handler


class TracksUsageManager:
    """
    Class for managing tracks_availability and usage_percentage data
    """

    def __init__(self):
        """Initialize the manager with database connection"""
        try:
            self.db_handler = get_db_handler()
            trace("Tracks and Usage Manager initialized", color="green")
        except Exception as e:
            report_exception(e)
            trace(f"Error initializing Tracks and Usage Manager: {str(e)}", color="red")

    # =================== Track Availability Methods ===================

    def get_all_tracks(self):
        """
        Returns all track availability records

        Returns:
            list: List of dictionaries with track availability data
        """
        try:
            self.db_handler.cursor.execute("""
                SELECT id, year, month, value FROM tracks_availability
                ORDER BY year DESC, month DESC
            """)
            rows = self.db_handler.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Error getting all track availability records: {str(e)}", color="red")
            return []

    def search_tracks(self, year=None, month=None):
        """
        Search track availability records by criteria

        Args:
            year (int): Year to filter by
            month (int): Month to filter by

        Returns:
            list: List of matching track availability records
        """
        try:
            query = "SELECT id, year, month, value FROM tracks_availability WHERE 1=1"
            params = []

            if year is not None:
                query += " AND year = ?"
                params.append(year)

            if month is not None:
                query += " AND month = ?"
                params.append(month)

            query += " ORDER BY year DESC, month DESC"

            self.db_handler.cursor.execute(query, params)
            rows = self.db_handler.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Error searching track availability records: {str(e)}", color="red")
            return []

    def get_track_by_id(self, track_id):
        """
        Get a track availability record by ID

        Args:
            track_id (int): ID of the record

        Returns:
            dict: Track availability record or None if not found
        """
        try:
            self.db_handler.cursor.execute(
                "SELECT id, year, month, value FROM tracks_availability WHERE id = ?",
                (track_id,)
            )
            row = self.db_handler.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Error getting track availability record by ID: {str(e)}", color="red")
            return None

    def add_track(self, track_data):
        """
        Add a new track availability record

        Args:
            track_data (dict): Data for the new record

        Returns:
            dict: Added record or error message
        """
        try:
            # Validate required fields
            if 'year' not in track_data or 'month' not in track_data or 'value' not in track_data:
                return {"error": "Year, month and value are required fields"}

            # Validate data types
            try:
                year = int(track_data['year'])
                month = int(track_data['month'])
                value = float(track_data['value'])
            except (ValueError, TypeError):
                return {"error": "Invalid data types: year and month must be integers, value must be a number"}

            # Validate value range
            if month < 1 or month > 12:
                return {"error": "Month must be between 1 and 12"}

            # Check if record for this year/month already exists
            self.db_handler.cursor.execute(
                "SELECT id FROM tracks_availability WHERE year = ? AND month = ?",
                (year, month)
            )
            existing = self.db_handler.cursor.fetchone()
            if existing:
                return {"error": f"Record for {year}-{month} already exists"}

            # Insert new record
            self.db_handler.cursor.execute("""
                INSERT INTO tracks_availability (year, month, value)
                VALUES (?, ?, ?)
            """, (year, month, value))

            self.db_handler.conn.commit()

            # Get the inserted record
            self.db_handler.cursor.execute(
                "SELECT id FROM tracks_availability WHERE year = ? AND month = ?",
                (year, month)
            )
            new_id = self.db_handler.cursor.fetchone()['id']

            return self.get_track_by_id(new_id)
        except Exception as e:
            report_exception(e)
            trace(f"Error adding track availability record: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return {"error": str(e)}

    def update_track(self, track_id, track_data):
        """
        Update an existing track availability record

        Args:
            track_id (int): ID of the record to update
            track_data (dict): New data for the record

        Returns:
            dict: Updated record or error message
        """
        try:
            # Validate required fields
            if not all(k in track_data for k in ['year', 'month', 'value']):
                return {"error": "Year, month and value are required fields"}

            # Validate data types
            try:
                year = int(track_data['year'])
                month = int(track_data['month'])
                value = float(track_data['value'])
            except (ValueError, TypeError):
                return {"error": "Invalid data types: year and month must be integers, value must be a number"}

            # Validate value range
            if month < 1 or month > 12:
                return {"error": "Month must be between 1 and 12"}

            # Check if record exists
            existing_record = self.get_track_by_id(track_id)
            if not existing_record:
                return {"error": f"Record with ID {track_id} not found"}

            # Check if new year/month combination already exists in another record
            if existing_record['year'] != year or existing_record['month'] != month:
                self.db_handler.cursor.execute(
                    "SELECT id FROM tracks_availability WHERE year = ? AND month = ? AND id != ?",
                    (year, month, track_id)
                )
                duplicate = self.db_handler.cursor.fetchone()
                if duplicate:
                    return {"error": f"Another record for {year}-{month} already exists"}

            # Update record
            self.db_handler.cursor.execute("""
                UPDATE tracks_availability
                SET year = ?, month = ?, value = ?
                WHERE id = ?
            """, (year, month, value, track_id))

            self.db_handler.conn.commit()

            return self.get_track_by_id(track_id)
        except Exception as e:
            report_exception(e)
            trace(f"Error updating track availability record: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return {"error": str(e)}

    def delete_track(self, track_id):
        """
        Delete a track availability record

        Args:
            track_id (int): ID of the record to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if record exists
            existing_record = self.get_track_by_id(track_id)
            if not existing_record:
                return False

            # Delete record
            self.db_handler.cursor.execute("DELETE FROM tracks_availability WHERE id = ?", (track_id,))
            self.db_handler.conn.commit()

            return True
        except Exception as e:
            report_exception(e)
            trace(f"Error deleting track availability record: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return False

    # =================== Usage Percentage Methods ===================

    def get_all_usage(self):
        """
        Returns all usage percentage records

        Returns:
            list: List of dictionaries with usage percentage data
        """
        try:
            self.db_handler.cursor.execute("""
                SELECT id, year, month, value FROM usage_percentage
                ORDER BY year DESC, month DESC
            """)
            rows = self.db_handler.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Error getting all usage percentage records: {str(e)}", color="red")
            return []

    def search_usage(self, year=None, month=None):
        """
        Search usage percentage records by criteria

        Args:
            year (int): Year to filter by
            month (int): Month to filter by

        Returns:
            list: List of matching usage percentage records
        """
        try:
            query = "SELECT id, year, month, value FROM usage_percentage WHERE 1=1"
            params = []

            if year is not None:
                query += " AND year = ?"
                params.append(year)

            if month is not None:
                query += " AND month = ?"
                params.append(month)

            query += " ORDER BY year DESC, month DESC"

            self.db_handler.cursor.execute(query, params)
            rows = self.db_handler.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Error searching usage percentage records: {str(e)}", color="red")
            return []

    def get_usage_by_id(self, usage_id):
        """
        Get a usage percentage record by ID

        Args:
            usage_id (int): ID of the record

        Returns:
            dict: Usage percentage record or None if not found
        """
        try:
            self.db_handler.cursor.execute(
                "SELECT id, year, month, value FROM usage_percentage WHERE id = ?",
                (usage_id,)
            )
            row = self.db_handler.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Error getting usage percentage record by ID: {str(e)}", color="red")
            return None

    def add_usage(self, usage_data):
        """
        Add a new usage percentage record

        Args:
            usage_data (dict): Data for the new record

        Returns:
            dict: Added record or error message
        """
        try:
            # Validate required fields
            if 'year' not in usage_data or 'month' not in usage_data or 'value' not in usage_data:
                return {"error": "Year, month and value are required fields"}

            # Validate data types
            try:
                year = int(usage_data['year'])
                month = int(usage_data['month'])
                value = float(usage_data['value'])
            except (ValueError, TypeError):
                return {"error": "Invalid data types: year and month must be integers, value must be a number"}

            # Validate value range
            if month < 1 or month > 12:
                return {"error": "Month must be between 1 and 12"}

            # Check if record for this year/month already exists
            self.db_handler.cursor.execute(
                "SELECT id FROM usage_percentage WHERE year = ? AND month = ?",
                (year, month)
            )
            existing = self.db_handler.cursor.fetchone()
            if existing:
                return {"error": f"Record for {year}-{month} already exists"}

            # Insert new record
            self.db_handler.cursor.execute("""
                INSERT INTO usage_percentage (year, month, value)
                VALUES (?, ?, ?)
            """, (year, month, value))

            self.db_handler.conn.commit()

            # Get the inserted record
            self.db_handler.cursor.execute(
                "SELECT id FROM usage_percentage WHERE year = ? AND month = ?",
                (year, month)
            )
            new_id = self.db_handler.cursor.fetchone()['id']

            return self.get_usage_by_id(new_id)
        except Exception as e:
            report_exception(e)
            trace(f"Error adding usage percentage record: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return {"error": str(e)}

    def update_usage(self, usage_id, usage_data):
        """
        Update an existing usage percentage record

        Args:
            usage_id (int): ID of the record to update
            usage_data (dict): New data for the record

        Returns:
            dict: Updated record or error message
        """
        try:
            # Validate required fields
            if not all(k in usage_data for k in ['year', 'month', 'value']):
                return {"error": "Year, month and value are required fields"}

            # Validate data types
            try:
                year = int(usage_data['year'])
                month = int(usage_data['month'])
                value = float(usage_data['value'])
            except (ValueError, TypeError):
                return {"error": "Invalid data types: year and month must be integers, value must be a number"}

            # Validate value range
            if month < 1 or month > 12:
                return {"error": "Month must be between 1 and 12"}

            # Check if record exists
            existing_record = self.get_usage_by_id(usage_id)
            if not existing_record:
                return {"error": f"Record with ID {usage_id} not found"}

            # Check if new year/month combination already exists in another record
            if existing_record['year'] != year or existing_record['month'] != month:
                self.db_handler.cursor.execute(
                    "SELECT id FROM usage_percentage WHERE year = ? AND month = ? AND id != ?",
                    (year, month, usage_id)
                )
                duplicate = self.db_handler.cursor.fetchone()
                if duplicate:
                    return {"error": f"Another record for {year}-{month} already exists"}

            # Update record
            self.db_handler.cursor.execute("""
                UPDATE usage_percentage
                SET year = ?, month = ?, value = ?
                WHERE id = ?
            """, (year, month, value, usage_id))

            self.db_handler.conn.commit()

            return self.get_usage_by_id(usage_id)
        except Exception as e:
            report_exception(e)
            trace(f"Error updating usage percentage record: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return {"error": str(e)}

    def delete_usage(self, usage_id):
        """
        Delete a usage percentage record

        Args:
            usage_id (int): ID of the record to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if record exists
            existing_record = self.get_usage_by_id(usage_id)
            if not existing_record:
                return False

            # Delete record
            self.db_handler.cursor.execute("DELETE FROM usage_percentage WHERE id = ?", (usage_id,))
            self.db_handler.conn.commit()

            return True
        except Exception as e:
            report_exception(e)
            trace(f"Error deleting usage percentage record: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return False

# Function to get an instance of the manager


def get_tracks_usage_manager():
    """Returns an instance of the TracksUsageManager"""
    return TracksUsageManager()
