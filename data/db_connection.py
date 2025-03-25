
# Descrição: Arquivo base para conexão com o banco de dados
# Desenvolvido por: Raphael Pires
# Última Revisão: 09/08/2023

import threading
import pyodbc
import configparser
import os
import pandas as pd


class DatabaseReader:
    def __init__(self):
        parser = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "db_connection.cfg")
        parser.read(config_path)

        self.server = parser.get("config", "WAccessBDServer")
        self.database = parser.get("config", "WAccessDB")
        self.username = 'sa'
        self.password = '#w_access_Adm#'

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
                    sp_script = f"EXEC {procedure_name} {', '.join(['?'] * len(params))}"
                    cursor.execute(sp_script, params)
                else:
                    cursor.execute(f"EXEC {procedure_name}")

                # Captura o valor retornado pela stored procedure
                result = cursor.fetchall()

                connection.commit()

            except Exception as e:
                print(f"Error executing procedure: {str(e)}")
                connection.rollback()
                return None
            finally:
                cursor.close()
                connection.close()

        return result

    def execute_stored_procedure_df(self, procedure_name, params=None):
        """
        Executa uma stored procedure e retorna os resultados como DataFrame.

        Parâmetros:
        sp_name (str): Nome da stored procedure
        *params: Parâmetros para a stored procedure

        Retorno:
        DataFrame: Resultado da consulta
        """
        with self.lock:
            connection = self._create_connection()
            cursor = connection.cursor()

            try:
                # Construir a string de chamada da stored procedure
                if params:
                    sp_script = f"EXEC {procedure_name} {', '.join(['?'] * len(params))}"
                    cursor.execute(sp_script, params)
                else:
                    cursor.execute(f"EXEC {procedure_name}")

                # Obter os resultados e nomes das colunas
                columns = [column[0] for column in cursor.description]
                results = cursor.fetchall()

                # Converter para DataFrame
                df = pd.DataFrame.from_records(results, columns=columns)

            except Exception as e:
                print(f"Error executing procedure: {str(e)}")
                connection.rollback()
                return None
            finally:
                cursor.close()
                connection.close()

        return df


# Função auxiliar para obter uma instância da conexão
def get_db_connection():
    """Retorna uma instância da conexão com o banco de dados."""
    try:
        return DatabaseReader()
    except Exception as e:
        print(f"Erro ao criar conexão com banco de dados: {str(e)}")
        return None


if __name__ == '__main__':
    sql = DatabaseReader()
    start_date = '2024-01-01 00:00:33.220'
    end_date = '2024-01-31 23:59:59.220'

    ret = sql.execute_stored_procedure_df('sp_VehicleAccessReport', [start_date, end_date])
    print(ret)
