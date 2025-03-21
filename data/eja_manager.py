# data/eja_manager.py
# Gerenciamento de EJAs para o dashboard ZeenTech VEV
import os
import pandas as pd
import json
from pathlib import Path
from utils.tracer import trace, report_exception

# Import the SQLite-based implementation
try:
    from data.eja_sqlite_manager import EJASQLiteManager
    _USE_SQLITE = True
except ImportError:
    _USE_SQLITE = False
    trace("SQLite EJA Manager not available, falling back to CSV-based implementation", color="yellow")


class EJAManager:
    """
    Classe para gerenciar os dados de EJA, incluindo operações CRUD e importação/exportação.
    This is now a wrapper that delegates to either the SQLite or CSV implementation.
    """

    def __init__(self, eja_file=None):
        """
        Inicializa o gerenciador de EJAs.

        Args:
            eja_file (str, opcional): Caminho para o arquivo CSV de EJAs.
                                     Se None, usa o arquivo padrão.
        """
        self.use_sqlite = _USE_SQLITE

        if self.use_sqlite:
            # Use the SQLite implementation
            self.sqlite_manager = EJASQLiteManager()
        else:
            # Use the original CSV implementation
            if eja_file is None:
                # Usar o arquivo padrão no diretório aux_files
                self.eja_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                             "aux_files", "eja_simplificado.csv")
            else:
                self.eja_file = eja_file

            # Backup do arquivo original
            self.backup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                            "aux_files", "eja_backup.csv")

            # Garantir que o diretório aux_files existe
            os.makedirs(os.path.dirname(self.eja_file), exist_ok=True)

            # Carregar os dados
            self.load_data()

    def load_data(self):
        """Carrega os dados do arquivo CSV. Usado apenas para a implementação CSV."""
        if self.use_sqlite:
            return  # SQLite implementation doesn't need this method

        try:
            if os.path.exists(self.eja_file):
                self.df = pd.read_csv(self.eja_file, encoding='utf-8')

                # Garantir que as colunas necessárias existam
                required_cols = ['Nº', 'EJA CODE', 'TITLE', 'NEW CLASSIFICATION', 'CLASSIFICATION']
                for col in required_cols:
                    if col not in self.df.columns:
                        self.df[col] = ""

                # Garantir que EJA CODE seja numérico
                self.df['EJA CODE'] = pd.to_numeric(self.df['EJA CODE'], errors='coerce')

                # Garantir que Nº seja numérico
                self.df['Nº'] = pd.to_numeric(self.df['Nº'], errors='coerce')

                # Se algum Nº for NaN, preenchemos com um valor incremental
                if self.df['Nº'].isna().any():
                    max_num = self.df['Nº'].max()
                    if pd.isna(max_num):
                        max_num = 0

                    # Preencher valores NaN com números incrementais a partir do máximo
                    mask = self.df['Nº'].isna()
                    self.df.loc[mask, 'Nº'] = range(int(max_num) + 1, int(max_num) + 1 + mask.sum())
            else:
                # Criar DataFrame vazio com as colunas necessárias
                self.df = pd.DataFrame(columns=['Nº', 'EJA CODE', 'TITLE', 'NEW CLASSIFICATION', 'CLASSIFICATION'])

            # Ordenar pelo número
            self.df = self.df.sort_values('Nº')

        except Exception as e:
            report_exception(e)
            # Criar um DataFrame vazio em caso de erro
            self.df = pd.DataFrame(columns=['Nº', 'EJA CODE', 'TITLE', 'NEW CLASSIFICATION', 'CLASSIFICATION'])
            trace(f"Erro ao carregar dados de EJA: {str(e)}", color="red")

    def save_data(self):
        """Salva os dados no arquivo CSV. Usado apenas para a implementação CSV."""
        if self.use_sqlite:
            return True  # SQLite implementation automatically saves data

        try:
            # Criar backup do arquivo existente
            if os.path.exists(self.eja_file):
                self.df.to_csv(self.backup_file, index=False, encoding='utf-8')

            # Salvar os dados atualizados
            self.df.to_csv(self.eja_file, index=False, encoding='utf-8')
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao salvar dados de EJA: {str(e)}", color="red")
            return False

    def get_all_ejas(self):
        """Retorna todos os EJAs."""
        if self.use_sqlite:
            return self.sqlite_manager.get_all_ejas()
        else:
            return self.df.to_dict('records')

    def search_ejas(self, search_term=None, eja_code=None):
        """
        Busca EJAs pelo termo de busca no título ou pelo código.

        Args:
            search_term (str): Termo de busca para o título
            eja_code (int/str): Código EJA específico para busca

        Returns:
            list: Lista de EJAs encontrados
        """
        if self.use_sqlite:
            return self.sqlite_manager.search_ejas(search_term=search_term, eja_code=eja_code)
        else:
            filtered_df = self.df.copy()

            if search_term:
                # Busca por título
                filtered_df = filtered_df[filtered_df['TITLE'].str.contains(search_term, case=False, na=False)]

            if eja_code:
                # Busca por código EJA
                try:
                    eja_code = int(eja_code)
                    filtered_df = filtered_df[filtered_df['EJA CODE'] == eja_code]
                except (ValueError, TypeError):
                    # Se o código não for um número válido, retorna vazio
                    trace(f"EJA CODE inválido para busca: {eja_code}", color="yellow")

            return filtered_df.to_dict('records')

    def get_eja_by_id(self, row_id):
        """
        Busca um EJA pelo seu número de linha.

        Args:
            row_id (int): Número da linha (Nº)

        Returns:
            dict: Dados do EJA ou None se não encontrado
        """
        if self.use_sqlite:
            return self.sqlite_manager.get_eja_by_id(row_id)
        else:
            try:
                row_id = int(row_id)
                result = self.df[self.df['Nº'] == row_id]
                if not result.empty:
                    return result.iloc[0].to_dict()
                return None
            except (ValueError, TypeError):
                return None

    def get_eja_by_code(self, eja_code):
        """
        Busca um EJA pelo seu código (EJA CODE).

        Args:
            eja_code (int): Código do EJA

        Returns:
            dict: Dados do EJA ou None se não encontrado
        """
        if self.use_sqlite:
            return self.sqlite_manager.get_eja_by_code(eja_code)
        else:
            try:
                eja_code = int(eja_code)
                result = self.df[self.df['EJA CODE'] == eja_code]
                if not result.empty:
                    return result.iloc[0].to_dict()
                return None
            except (ValueError, TypeError):
                return None

    def add_eja(self, eja_data):
        """
        Adiciona um novo EJA ao sistema

        Args:
            eja_data (dict): Dados do EJA

        Returns:
            int: ID do EJA adicionado ou dict com erro
        """
        # Validar campos obrigatórios
        if not eja_data.get('eja_code') or not eja_data.get('title'):
            return {'error': 'Código EJA e Título são obrigatórios. XX'}

        try:
            if self.use_sqlite:
                return self.sqlite_manager.add_eja(eja_data)

            else:
                # Implementação para CSV
                # Carregar dados existentes
                all_ejas = self.get_all_ejas()

                # Verificar se já existe um EJA com o mesmo código
                for eja in all_ejas:
                    if eja.get('eja_code') == eja_data.get('eja_code'):
                        return {'error': f'Já existe um EJA com o código {eja_data.get("eja_code")}'}

                # Gerar um novo ID
                next_id = 1
                if all_ejas:
                    # Tentar obter o maior ID atual e incrementar
                    try:
                        next_id = max([int(eja.get('Nº', 0)) for eja in all_ejas if eja.get('Nº', '').isdigit()]) + 1
                    except ValueError:
                        next_id = len(all_ejas) + 1

                # Adicionar o ID ao novo EJA
                eja_data['Nº'] = str(next_id)

                # Adicionar à lista e salvar
                all_ejas.append(eja_data)
                self._save_to_csv(all_ejas)

                return next_id

        except Exception as e:
            print(f"Erro ao adicionar EJA: {str(e)}")
            return {'error': str(e)}

    def update_eja(self, eja_id, eja_data):
        """
        Atualiza um EJA existente

        Args:
            eja_id (str): ID do EJA a ser atualizado
            eja_data (dict): Novos dados do EJA

        Returns:
            bool: True se atualizado com sucesso, ou dict com erro
        """
        # Validar campos obrigatórios
        if not eja_data.get('eja_code') or not eja_data.get('title'):
            return {'error': 'Código EJA e Título são obrigatórios'}

        try:
            if self.use_sqlite:
                # Implementação para SQLite
                # Verificar se existe outro EJA com o mesmo código (exceto o próprio)
                return self.sqlite_manager.update_eja(eja_data)

        except Exception as e:
            print(f"Erro ao atualizar EJA: {str(e)}")
            return {'error': str(e)}

    def delete_eja(self, row_id):
        """
        Remove um EJA.

        Args:
            row_id (int): Número da linha (Nº)

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        if self.use_sqlite:
            return self.sqlite_manager.delete_eja(row_id)
        else:
            try:
                row_id = int(row_id)

                # Verificar se o EJA existe
                initial_len = len(self.df)
                self.df = self.df[self.df['Nº'] != row_id]

                # Se removeu alguma linha, salvar
                if len(self.df) < initial_len:
                    self.save_data()
                    return True
                return False
            except Exception as e:
                report_exception(e)
                return False

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
        if self.use_sqlite:
            return self.sqlite_manager.import_csv(file_path, overwrite=overwrite)
        else:
            try:
                # Verificar se o arquivo existe
                if not os.path.exists(file_path):
                    return {"error": f"Arquivo {file_path} não encontrado"}

                # Ler o CSV
                new_df = pd.read_csv(file_path, encoding='utf-8')

                # Verificar se possui as colunas necessárias
                required_cols = ['EJA CODE', 'TITLE', 'NEW CLASSIFICATION']
                missing_cols = [col for col in required_cols if col not in new_df.columns]
                if missing_cols:
                    return {"error": f"Colunas obrigatórias ausentes: {', '.join(missing_cols)}"}

                # Garantir que os números são numéricos
                new_df['EJA CODE'] = pd.to_numeric(new_df['EJA CODE'], errors='coerce')

                # Criar backup antes da importação
                if os.path.exists(self.eja_file):
                    backup_path = self.backup_file
                    self.df.to_csv(backup_path, index=False, encoding='utf-8')

                if overwrite:
                    # Se for para sobrescrever, substitui completamente
                    # Mas mantém a coluna Nº se ela existir
                    if 'Nº' in new_df.columns:
                        # Usar os números do arquivo importado
                        self.df = new_df.copy()
                    else:
                        # Gerar novos números sequenciais
                        self.df = new_df.copy()
                        self.df['Nº'] = range(1, len(new_df) + 1)

                    result = {
                        "status": "success",
                        "message": f"Importação concluída: {len(new_df)} registros importados",
                        "imported": len(new_df),
                        "updated": 0,
                        "skipped": 0
                    }
                else:
                    # Atualizar apenas os existentes ou adicionar novos
                    updated = 0
                    added = 0
                    skipped = 0

                    for _, row in new_df.iterrows():
                        eja_code = row['EJA CODE']
                        # Verificar se já existe
                        existing = self.df[self.df['EJA CODE'] == eja_code]

                        if not existing.empty:
                            # Atualizar existente
                            idx = existing.index[0]
                            for col in new_df.columns:
                                if col in self.df.columns:
                                    self.df.loc[idx, col] = row[col]
                            updated += 1
                        else:
                            # Adicionar novo
                            new_number = int(self.df['Nº'].max() + 1) if not self.df.empty else 1
                            new_row = row.to_dict()
                            new_row['Nº'] = new_number
                            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
                            added += 1

                    result = {
                        "status": "success",
                        "message": f"Importação parcial: {added} adicionados, {updated} atualizados, {skipped} ignorados",
                        "imported": added,
                        "updated": updated,
                        "skipped": skipped
                    }

                # Garantir que as colunas necessárias existam
                for col in ['Nº', 'EJA CODE', 'TITLE', 'NEW CLASSIFICATION', 'CLASSIFICATION']:
                    if col not in self.df.columns:
                        self.df[col] = ""

                # Salvar as alterações
                self.save_data()

                return result
            except Exception as e:
                report_exception(e)
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
        if self.use_sqlite:
            return self.sqlite_manager.export_csv(file_path)
        else:
            try:
                if file_path is None:
                    # Gerar nome baseado na data atual
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
                    os.makedirs(export_dir, exist_ok=True)
                    file_path = os.path.join(export_dir, f"eja_export_{timestamp}.csv")

                # Exportar para CSV
                self.df.to_csv(file_path, index=False, encoding='utf-8')
                return file_path
            except Exception as e:
                report_exception(e)
                return f"Erro ao exportar: {str(e)}"

    def get_all_classifications(self):
        """Retorna todas as classificações únicas disponíveis."""
        if self.use_sqlite:
            return self.sqlite_manager.get_all_classifications()
        else:
            return sorted(self.df['NEW CLASSIFICATION'].dropna().unique().tolist())

# Função auxiliar para uso externo


def get_eja_manager():
    """Retorna uma instância do gerenciador de EJAs."""
    return EJAManager()
