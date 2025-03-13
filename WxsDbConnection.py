
# Descrição: Arquivo base para conexão com o banco de dados
# Desenvolvido por: Raphael Pires
# Última Revisão: 09/08/2023

import threading
import pyodbc
import configparser

class Parameters:
    parser = configparser.ConfigParser()
    parser.read("WxsDbConnection.cfg")

    chtypes_list = parser.get("userFields", "CHType")
    chstate_expired = parser.get("userFields", "CHStateExpiredDoc")

class DatabaseReader:
    def __init__(self):
        parser = configparser.ConfigParser()
        parser.read("WxsDbConnection.cfg")

        self.server = parser.get("config", "WAccessBDServer")
        self.database = parser.get("config", "WAccessDB")
        self.username = 'W-Access'
        self.password = 'db_W-X-S@Wellcare924_'

        self.api_server = parser.get("config", "WAccessAPIServer")
        self.api_oper = parser.get("config", "WAccessAPIOper")
        
        self.lock = threading.Lock()

    def _create_connection(self):
        connection_string = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
        )
        return pyodbc.connect(connection_string)

    def _execute_query(self, query):
        connection = self._create_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            connection.commit()
            return True
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()

    def read_data(self, query):
        with self.lock:
            connection = self._create_connection()
            cursor = connection.cursor()

            try:
                cursor.execute(query)
                result = cursor.fetchall()
            except Exception as e:
                result = None
                print(f"Error executing query: {str(e)}")
            finally:
                cursor.close()
                connection.close()

        return result

    def read_single_row(self, query):
        with self.lock:
            connection = self._create_connection()
            cursor = connection.cursor()

            try:
                cursor.execute(query)
                result = cursor.fetchone()
            except Exception as e:
                result = None
                print(f"Error executing query: {str(e)}")
            finally:
                cursor.close()
                connection.close()

        return result

    def execute_update(self, query):
        return self._execute_query(query)

    def execute_insert(self, query):
        return self._execute_query(query)

    def execute_procedure(self, procedure_name, params=None):
        with self.lock:
            connection = self._create_connection()
            cursor = connection.cursor()

            try:
                if params:
                    cursor.execute(f"EXEC {procedure_name} {', '.join(params)}")
                else:
                    cursor.execute(f"EXEC {procedure_name}")
                connection.commit()
                return True
            except Exception as e:
                print(f"Error executing procedure: {str(e)}")
                connection.rollback()
                return False
            finally:
                cursor.close()
                connection.close()
