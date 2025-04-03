# data/eja_manager.py
import os
import pandas as pd
from utils.tracer import trace, report_exception
from datetime import datetime

# Importar o gerenciador de banco de dados SQLite
from data.local_db_handler import LocalDatabaseHandler, get_db_handler


class EJAManager:
    """
    Classe unificada para gerenciar os dados de EJA, utilizando SQLite como armazenamento.
    """

    def __init__(self):
        """Inicializa o gerenciador de EJAs."""
        try:
            # Inicializar o gerenciador de banco de dados SQLite
            self.db_handler = LocalDatabaseHandler()
            self.use_sqlite = True
            trace("Gerenciador de EJAs inicializado com SQLite", color="green")
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao inicializar gerenciador de EJAs: {str(e)}", color="red")

    def get_all_ejas(self):
        """
        Retorna todos os EJAs.

        Returns:
            list: Lista de dicionários com os dados dos EJAs
        """
        return self.db_handler.get_all_ejas()

    def search_ejas(self, search_term=None, eja_code=None, classification=None):
        """
        Busca EJAs pelos critérios fornecidos.

        Args:
            search_term (str): Termo de busca para o título
            eja_code (int): Código EJA específico
            classification (str): Classificação para filtro

        Returns:
            list: Lista de EJAs correspondentes aos critérios
        """
        trace(f"Search item using: titulo={search_term}, EJA Code={eja_code}")
        return self.db_handler.search_ejas(
            search_term=search_term,
            eja_code=eja_code,
            classification=classification
        )

    def get_eja_by_id(self, eja_id):
        """
        Busca um EJA pelo seu ID.

        Args:
            eja_id (int): ID do EJA

        Returns:
            dict: Dados do EJA ou None se não encontrado
        """
        try:
            eja_id = int(eja_id)
            return self.db_handler.get_eja_by_id(eja_id)
        except (ValueError, TypeError):
            trace(f"ID de EJA inválido: {eja_id}", color="yellow")
            return None

    def get_eja_by_code(self, eja_code):
        """
        Busca um EJA pelo seu código.

        Args:
            eja_code (int): Código do EJA

        Returns:
            dict: Dados do EJA ou None se não encontrado
        """
        try:
            eja_code = int(eja_code)
            return self.db_handler.get_eja_by_code(eja_code)
        except (ValueError, TypeError):
            trace(f"Código de EJA inválido: {eja_code}", color="yellow")
            return None

    def add_eja(self, eja_data):
        """
        Adiciona um novo EJA.

        Args:
            eja_data (dict): Dados do EJA a ser adicionado

        Returns:
            dict: Dados do EJA adicionado ou dict com erro
        """
        try:
            # Validar campos obrigatórios
            if not eja_data.get('eja_code') or not eja_data.get('title'):
                return {"error": "Código EJA e Título são obrigatórios"}

            # Formatando o dicionário de dados
            formatted_data = {
                'eja_code': int(eja_data['eja_code']),
                'title': eja_data['title'],
                'new_classification': eja_data.get('new_classification', ''),
                'classification': eja_data.get('classification', '')
            }

            # Adicionar ao banco de dados
            return self.db_handler.add_eja(formatted_data)
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao adicionar EJA: {str(e)}", color="red")
            return {"error": str(e)}

    def update_eja(self, eja_id, eja_data):
        """
        Atualiza um EJA existente.

        Args:
            eja_id (int): ID do EJA a ser atualizado
            eja_data (dict): Novos dados do EJA

        Returns:
            dict: Dados atualizados do EJA ou dict com erro
        """
        try:
            eja_id = int(eja_id)

            # Validar campos obrigatórios
            if not eja_data.get('eja_code') or not eja_data.get('title'):
                return {"error": "Código EJA e Título são obrigatórios"}

            # Formatando o dicionário de dados
            formatted_data = {}
            if 'eja_code' in eja_data:
                formatted_data['eja_code'] = int(eja_data['eja_code'])
            if 'title' in eja_data:
                formatted_data['title'] = eja_data['title']
            if 'new_classification' in eja_data:
                formatted_data['new_classification'] = eja_data['new_classification']
            if 'classification' in eja_data:
                formatted_data['classification'] = eja_data['classification']

            # Atualizar no banco de dados
            return self.db_handler.update_eja(eja_id, formatted_data)
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao atualizar EJA: {str(e)}", color="red")
            return {"error": str(e)}

    def delete_eja(self, eja_id):
        """
        Remove um EJA.

        Args:
            eja_id (int): ID do EJA a ser removido

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        try:
            eja_id = int(eja_id)
            return self.db_handler.delete_eja(eja_id)
        except (ValueError, TypeError):
            trace(f"ID de EJA inválido para exclusão: {eja_id}", color="yellow")
            return False
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao excluir EJA: {str(e)}", color="red")
            return False

    def get_all_classifications(self):
        """
        Retorna todas as classificações únicas disponíveis.

        Returns:
            list: Lista de classificações
        """
        return self.db_handler.get_all_classifications()

    # =================== Métodos para importação/exportação CSV ===================

    def import_csv(self, file_path, overwrite=True):
        """
        Importa dados de um arquivo CSV.

        Args:
            file_path (str): Caminho para o arquivo CSV
            overwrite (bool): Se True, substitui todos os dados existentes.
                             Se False, apenas adiciona novos ou atualiza existentes.

        Returns:
            dict: Resultado da importação com contadores
        """
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(file_path):
                return {"error": f"Arquivo {file_path} não encontrado"}

            # Utilizar o método do gerenciador de banco de dados
            result = self.db_handler.import_ejas_from_csv(file_path, overwrite=overwrite)

            # Verificar se houve erro
            if "error" in result:
                trace(f"Erro na importação de CSV: {result['error']}", color="red")
            else:
                trace(f"Importação de CSV concluída: {result.get('message')}", color="green")

            return result
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao importar CSV: {str(e)}", color="red")
            return {"error": str(e)}

    def export_csv(self, file_path=None):
        """
        Exporta os dados para um arquivo CSV.

        Args:
            file_path (str, opcional): Caminho para salvar o arquivo CSV.
                                      Se None, usa o caminho padrão.

        Returns:
            str: Caminho do arquivo exportado ou mensagem de erro
        """
        try:
            if file_path is None:
                # Gerar nome baseado na data atual
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
                os.makedirs(export_dir, exist_ok=True)
                file_path = os.path.join(export_dir, f"eja_export_{timestamp}.csv")

            # Utilizar o método do gerenciador de banco de dados
            result = self.db_handler.export_ejas_to_csv(file_path)

            if os.path.exists(file_path):
                trace(f"Dados exportados com sucesso para: {file_path}", color="green")
            else:
                trace(f"Erro na exportação: {result}", color="red")

            return result
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao exportar CSV: {str(e)}", color="red")
            return f"Erro ao exportar: {str(e)}"


# Função auxiliar para obter uma instância do gerenciador de EJAs
def get_eja_manager():
    """Retorna uma instância do gerenciador de EJAs."""
    return EJAManager()
