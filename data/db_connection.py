
# Descrição: Arquivo base para conexão com o banco de dados
# Desenvolvido por: Raphael Pires
# Última Revisão: 09/08/2023

import threading
import pyodbc
import configparser
import os
import pandas as pd
from utils.helpers import is_running_in_docker


def get_appropriate_driver():
    if is_running_in_docker():
        return "FreeTDS"  # Ou "ODBC Driver 17 for SQL Server" se instalado no container
    else:
        return "SQL Server"  # Driver padrão no Windows


class DatabaseReader:
    def __init__(self):
        # Usar valores fixos para usuário e senha, ou obter do arquivo de configuração
        self.server = os.environ.get('DB_SERVER', 'localhost,1433')
        self.database = os.environ.get('DB_DATABASE', 'W_Access')
        self.username = os.environ.get('DB_USERNAME', 'sa')
        self.password = os.environ.get('DB_PASSWORD', '#w_access_Adm#')

        # Obter o driver ODBC especificado nas variáveis de ambiente ou usar o padrão
        self.driver = os.environ.get('DB_DRIVER', 'SQL Server')

        self.lock = threading.Lock()

        # Validar a configuração
        print(f"Configuração do banco carregada: Servidor={self.server}, DB={self.database}, Driver={self.driver}")

    def _create_connection(self):
        # Tentar diferentes formatos de string de conexão
        connection_string = None
        connection = None
        errors = []

        if not connection:
            try:
                connection_string = (
                    f"DRIVER={{SQL Server}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
                connection = pyodbc.connect(connection_string)
                return connection
            except Exception as e:
                errors.append(f"Erro com driver 'FreeTDS': {str(e)}")

        # Se chegou aqui, nenhuma tentativa funcionou
        raise Exception(f"Falha ao conectar ao banco de dados. Erros: {'; '.join(errors)}")

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
