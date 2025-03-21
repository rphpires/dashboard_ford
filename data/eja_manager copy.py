# data/eja_manager.py
# Gerenciamento de EJAs para o dashboard ZeenTech VEV
import os
import pandas as pd
import json
from pathlib import Path
from utils.tracer import trace, report_exception


class EJAManager:
    """
    Classe para gerenciar os dados de EJA, incluindo operações CRUD e importação/exportação
    """

    def __init__(self, eja_file=None):
        """
        Inicializa o gerenciador de EJAs.

        Args:
            eja_file (str, opcional): Caminho para o arquivo CSV de EJAs.
                                     Se None, usa o arquivo padrão.
        """
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
        """Carrega os dados do arquivo CSV."""
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
        """Salva os dados no arquivo CSV."""
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
        Adiciona um novo EJA.

        Args:
            eja_data (dict): Dados do EJA a ser adicionado

        Returns:
            dict: Dados do EJA adicionado ou dict com erro
        """
        try:
            # Validar campos obrigatórios
            if not all(k in eja_data for k in ['EJA CODE', 'TITLE', 'NEW CLASSIFICATION']):
                return {"error": "Campos obrigatórios ausentes"}

            # Verificar se o EJA CODE já existe
            eja_code = int(eja_data['EJA CODE'])
            if any(self.df['EJA CODE'] == eja_code):
                return {"error": f"EJA CODE {eja_code} já existe"}

            # Gerar um novo número sequencial
            new_number = int(self.df['Nº'].max() + 1) if not self.df.empty else 1

            # Criar novo registro
            new_eja = {
                'Nº': new_number,
                'EJA CODE': eja_code,
                'TITLE': eja_data['TITLE'],
                'NEW CLASSIFICATION': eja_data['NEW CLASSIFICATION'],
                'CLASSIFICATION': eja_data.get('CLASSIFICATION', '')
            }

            # Adicionar ao DataFrame
            self.df = pd.concat([self.df, pd.DataFrame([new_eja])], ignore_index=True)

            # Salvar alterações
            self.save_data()

            return new_eja
        except Exception as e:
            report_exception(e)
            return {"error": str(e)}

    def update_eja(self, row_id, eja_data):
        """
        Atualiza um EJA existente.

        Args:
            row_id (int): Número da linha (Nº)
            eja_data (dict): Novos dados do EJA

        Returns:
            dict: Dados atualizados do EJA ou dict com erro
        """
        try:
            row_id = int(row_id)

            # Verificar se o EJA existe
            row_idx = self.df.index[self.df['Nº'] == row_id].tolist()
            if not row_idx:
                return {"error": f"EJA com Nº {row_id} não encontrado"}

            # Se estiver mudando o EJA CODE, verificar se já existe
            if 'EJA CODE' in eja_data:
                new_eja_code = int(eja_data['EJA CODE'])
                existing = self.df[(self.df['EJA CODE'] == new_eja_code) & (self.df['Nº'] != row_id)]
                if not existing.empty:
                    return {"error": f"EJA CODE {new_eja_code} já existe para outro registro"}

            # Atualizar os campos fornecidos
            for key, value in eja_data.items():
                if key in self.df.columns:
                    self.df.loc[row_idx[0], key] = value

            # Salvar alterações
            self.save_data()

            # Retornar o registro atualizado
            return self.df.iloc[row_idx[0]].to_dict()
        except Exception as e:
            report_exception(e)
            return {"error": str(e)}

    def delete_eja(self, row_id):
        """
        Remove um EJA.

        Args:
            row_id (int): Número da linha (Nº)

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
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
        return sorted(self.df['NEW CLASSIFICATION'].dropna().unique().tolist())

# Função auxiliar para uso externo


def get_eja_manager():
    """Retorna uma instância do gerenciador de EJAs."""
    return EJAManager()
