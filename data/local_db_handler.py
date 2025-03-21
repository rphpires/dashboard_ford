"""
local_db_handler.py
Gerenciamento de banco de dados SQLite local para o dashboard ZeenTech VEV

Este módulo fornece funções para:
- Criar e conectar ao banco de dados SQLite
- Criar e gerenciar tabelas (EJA, tracks)
- Executar operações CRUD nas tabelas
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from utils.tracer import trace, report_exception


class LocalDatabaseHandler:
    """
    Classe para gerenciar o banco de dados SQLite local do dashboard.
    """

    def __init__(self, db_path=None):
        """
        Inicializa o manipulador de banco de dados local.

        Args:
            db_path (str, opcional): Caminho para o arquivo do banco de dados SQLite.
                                    Se None, será usado o caminho padrão.
        """
        if db_path is None:
            # Usar o caminho padrão no diretório de dados
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                        "data", "zeentech_dashboard.db")
        else:
            self.db_path = db_path

        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Verificar se o banco de dados precisa ser criado
        db_exists = os.path.exists(self.db_path)

        # Conectar ao banco de dados
        self.conn = None
        self.cursor = None
        self.connect()

        # Se não existir, criar as tabelas
        if not db_exists:
            self.create_tables()
        else:
            self.check_and_update_schema()  # Verificar e atualizar schema se necessário

    def connect(self):
        """Estabelece conexão com o banco de dados."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acessar colunas pelo nome
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao conectar ao banco de dados: {str(e)}", color="red")
            return False

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self):
        """
        Cria as tabelas necessárias no banco de dados.
        Esta função pode ser chamada para criar o esquema inicial.
        """
        try:
            # Criar a tabela EJA
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS eja (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eja_code INTEGER NOT NULL UNIQUE,
                title TEXT NOT NULL,
                new_classification TEXT,
                classification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Criar a tabela de tracks
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ponto TEXT,
                pista TEXT,
                track TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Criar índices para melhorar a performance
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_eja_code ON eja (eja_code)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_eja_title ON eja (title)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_eja_class ON eja (new_classification)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_track_pista ON tracks (pista)')

            # Commit para salvar as alterações
            self.conn.commit()
            trace("Tabelas criadas com sucesso.", color="green")
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao criar tabelas: {str(e)}", color="red")
            self.conn.rollback()
            return False

    def check_and_update_schema(self):
        """Verifica e atualiza o esquema do banco de dados se necessário."""
        try:
            # Verificar se existem colunas que precisam ser adicionadas à tabela EJA
            try:
                self.cursor.execute("SELECT created_at, updated_at FROM eja LIMIT 1")
            except sqlite3.OperationalError:
                # Se falhar, as colunas não existem, então adicionamos
                trace("Atualizando esquema da tabela eja...", color="yellow")
                self.cursor.execute("ALTER TABLE eja ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                self.cursor.execute("ALTER TABLE eja ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            # Verificar se existem colunas que precisam ser adicionadas à tabela tracks
            try:
                self.cursor.execute("SELECT created_at, updated_at FROM tracks LIMIT 1")
            except sqlite3.OperationalError:
                # Se falhar, as colunas não existem, então adicionamos
                trace("Atualizando esquema da tabela tracks...", color="yellow")
                self.cursor.execute("ALTER TABLE tracks ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                self.cursor.execute("ALTER TABLE tracks ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            self.conn.commit()
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao atualizar esquema: {str(e)}", color="red")
            self.conn.rollback()
            return False

    # =================== Métodos para tabela EJA ===================

    def get_all_ejas(self):
        """Retorna todos os registros da tabela EJA."""
        try:
            self.cursor.execute("SELECT * FROM eja ORDER BY eja_code")
            rows = self.cursor.fetchall()
            # Converter para lista de dicionários
            result = [dict(row) for row in rows]
            return result
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter EJAs: {str(e)}", color="red")
            return []

    def get_eja_by_id(self, eja_id):
        """
        Busca um EJA pelo ID.

        Args:
            eja_id (int): ID do registro

        Returns:
            dict: Dados do EJA ou None se não encontrado
        """
        try:
            self.cursor.execute("SELECT * FROM eja WHERE id = ?", (eja_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar EJA por ID: {str(e)}", color="red")
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
            self.cursor.execute("SELECT * FROM eja WHERE eja_code = ?", (eja_code,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar EJA por código: {str(e)}", color="red")
            return None

    def search_ejas(self, search_term=None, eja_code=None, classification=None):
        """
        Busca EJAs pelos termos fornecidos.

        Args:
            search_term (str, opcional): Termo para buscar no título
            eja_code (int, opcional): Código do EJA para busca exata
            classification (str, opcional): Classificação para filtragem

        Returns:
            list: Lista de EJAs encontrados
        """
        try:
            query = "SELECT * FROM eja WHERE 1=1"
            params = []

            if search_term:
                query += " AND title LIKE ?"
                params.append(f"%{search_term}%")

            if eja_code:
                query += " AND eja_code = ?"
                params.append(eja_code)

            if classification:
                query += " AND new_classification = ?"
                params.append(classification)

            query += " ORDER BY eja_code"

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar EJAs: {str(e)}", color="red")
            return []

    def add_eja(self, eja_data):
        """
        Adiciona um novo EJA ao banco de dados.

        Args:
            eja_data (dict): Dados do EJA com as chaves: eja_code, title, new_classification, classification

        Returns:
            dict: Dados do EJA inserido com ID ou dict com erro
        """
        try:
            # Validar campos obrigatórios
            if not all(k in eja_data for k in ['eja_code', 'title']):
                return {"error": "Campos obrigatórios ausentes (eja_code, title)"}

            # Verificar se o EJA CODE já existe
            eja_code = int(eja_data['eja_code'])
            existing_eja = self.get_eja_by_code(eja_code)
            if existing_eja:
                return {"error": f"EJA CODE {eja_code} já existe"}

            # Inserir o novo EJA
            self.cursor.execute("""
                INSERT INTO eja (eja_code, title, new_classification, classification)
                VALUES (?, ?, ?, ?)
            """, (
                eja_data['eja_code'],
                eja_data['title'],
                eja_data.get('new_classification', ''),
                eja_data.get('classification', '')
            ))

            # Commit para salvar as alterações
            self.conn.commit()

            # Retornar o registro recém-inserido
            return self.get_eja_by_code(eja_data['eja_code'])
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao adicionar EJA: {str(e)}", color="red")
            self.conn.rollback()
            return {"error": str(e)}

    def update_eja(self, eja_id, eja_data):
        """
        Atualiza um EJA existente.

        Args:
            eja_id (int): ID do EJA a ser atualizado
            eja_data (dict): Novos dados do EJA (chaves podem ser: eja_code, title, new_classification, classification)

        Returns:
            dict: Dados atualizados do EJA ou dict com erro
        """
        try:
            # Verificar se o EJA existe
            existing_eja = self.get_eja_by_id(eja_id)
            if not existing_eja:
                return {"error": f"EJA com ID {eja_id} não encontrado"}

            # Se estiver mudando o EJA CODE, verificar se já existe
            if 'eja_code' in eja_data:
                new_eja_code = int(eja_data['eja_code'])
                if new_eja_code != existing_eja['eja_code']:
                    code_check = self.get_eja_by_code(new_eja_code)
                    if code_check:
                        return {"error": f"EJA CODE {new_eja_code} já existe para outro registro"}

            # Construir a query de update
            fields = []
            values = []
            for key, value in eja_data.items():
                if key in ['eja_code', 'title', 'new_classification', 'classification']:
                    fields.append(f"{key} = ?")
                    values.append(value)

            if not fields:
                return {"error": "Nenhum campo válido para atualização"}

            # Adicionar updated_at
            fields.append("updated_at = CURRENT_TIMESTAMP")

            # Montar a query
            query = f"UPDATE eja SET {', '.join(fields)} WHERE id = ?"
            values.append(eja_id)

            # Executar a query
            self.cursor.execute(query, values)
            self.conn.commit()

            # Retornar o registro atualizado
            return self.get_eja_by_id(eja_id)
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao atualizar EJA: {str(e)}", color="red")
            self.conn.rollback()
            return {"error": str(e)}

    def delete_eja(self, eja_id):
        """
        Remove um EJA pelo ID.

        Args:
            eja_id (int): ID do EJA a ser removido

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        try:
            # Verificar se o EJA existe
            existing_eja = self.get_eja_by_id(eja_id)
            if not existing_eja:
                return False

            # Remover o EJA
            self.cursor.execute("DELETE FROM eja WHERE id = ?", (eja_id,))
            self.conn.commit()
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao remover EJA: {str(e)}", color="red")
            self.conn.rollback()
            return False

    def get_all_classifications(self):
        """Retorna todas as classificações únicas disponíveis."""
        try:
            self.cursor.execute("SELECT DISTINCT new_classification FROM eja WHERE new_classification IS NOT NULL AND new_classification != ''")
            rows = self.cursor.fetchall()
            return [row['new_classification'] for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter classificações: {str(e)}", color="red")
            return []

    def import_ejas_from_csv(self, file_path, overwrite=True):
        """
        Importa EJAs de um arquivo CSV.

        Args:
            file_path (str): Caminho para o arquivo CSV
            overwrite (bool): Se True, limpa todos os dados existentes antes de importar

        Returns:
            dict: Resultado da importação com contadores
        """
        try:
            if not os.path.exists(file_path):
                return {"error": f"Arquivo {file_path} não encontrado"}

            # Ler o CSV
            df = pd.read_csv(file_path, encoding='utf-8')

            # Verificar se possui as colunas necessárias
            required_cols = ['EJA CODE', 'TITLE']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                return {"error": f"Colunas obrigatórias ausentes: {', '.join(missing_cols)}"}

            # Garantir que os números são numéricos
            df['EJA CODE'] = pd.to_numeric(df['EJA CODE'], errors='coerce')

            # Iniciar transação
            self.conn.begin()

            if overwrite:
                # Limpar a tabela se estiver substituindo todos os registros
                self.cursor.execute("DELETE FROM eja")

                # Inserir todos os registros
                for _, row in df.iterrows():
                    self.cursor.execute("""
                        INSERT INTO eja (eja_code, title, new_classification, classification)
                        VALUES (?, ?, ?, ?)
                    """, (
                        int(row['EJA CODE']),
                        row['TITLE'],
                        row['NEW CLASSIFICATION'] if 'NEW CLASSIFICATION' in df.columns else '',
                        row['CLASSIFICATION'] if 'CLASSIFICATION' in df.columns else ''
                    ))

                result = {
                    "status": "success",
                    "message": f"Importação concluída: {len(df)} registros importados",
                    "imported": len(df),
                    "updated": 0,
                    "skipped": 0
                }
            else:
                # Atualizar apenas os existentes ou adicionar novos
                updated = 0
                added = 0
                skipped = 0

                for _, row in df.iterrows():
                    eja_code = int(row['EJA CODE'])

                    # Verificar se já existe
                    self.cursor.execute("SELECT id FROM eja WHERE eja_code = ?", (eja_code,))
                    existing = self.cursor.fetchone()

                    if existing:
                        # Atualizar existente
                        self.cursor.execute("""
                            UPDATE eja SET
                                title = ?,
                                new_classification = ?,
                                classification = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE eja_code = ?
                        """, (
                            row['TITLE'],
                            row['NEW CLASSIFICATION'] if 'NEW CLASSIFICATION' in df.columns else '',
                            row['CLASSIFICATION'] if 'CLASSIFICATION' in df.columns else '',
                            eja_code
                        ))
                        updated += 1
                    else:
                        # Adicionar novo
                        self.cursor.execute("""
                            INSERT INTO eja (eja_code, title, new_classification, classification)
                            VALUES (?, ?, ?, ?)
                        """, (
                            eja_code,
                            row['TITLE'],
                            row['NEW CLASSIFICATION'] if 'NEW CLASSIFICATION' in df.columns else '',
                            row['CLASSIFICATION'] if 'CLASSIFICATION' in df.columns else ''
                        ))
                        added += 1

                result = {
                    "status": "success",
                    "message": f"Importação parcial: {added} adicionados, {updated} atualizados, {skipped} ignorados",
                    "imported": added,
                    "updated": updated,
                    "skipped": skipped
                }

            # Commit para salvar as alterações
            self.conn.commit()
            return result
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao importar EJAs: {str(e)}", color="red")
            self.conn.rollback()
            return {"error": str(e)}

    def export_ejas_to_csv(self, file_path=None):
        """
        Exporta os EJAs para um arquivo CSV.

        Args:
            file_path (str, opcional): Caminho para salvar o arquivo CSV.
                                      Se None, gera um nome baseado na data atual.

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

            # Consultar todos os EJAs
            self.cursor.execute("""
                SELECT
                    id as 'Nº',
                    eja_code as 'EJA CODE',
                    title as 'TITLE',
                    new_classification as 'NEW CLASSIFICATION',
                    classification as 'CLASSIFICATION'
                FROM eja
                ORDER BY eja_code
            """)

            rows = self.cursor.fetchall()

            # Converter para DataFrame
            df = pd.DataFrame([dict(row) for row in rows])

            # Exportar para CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            return file_path
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao exportar EJAs: {str(e)}", color="red")
            return f"Erro ao exportar: {str(e)}"

    # =================== Métodos para tabela Tracks ===================

    def get_all_tracks(self):
        """Retorna todos os registros da tabela tracks."""
        try:
            self.cursor.execute("SELECT * FROM tracks ORDER BY pista, ponto")
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter tracks: {str(e)}", color="red")
            return []

    def get_track_by_id(self, track_id):
        """
        Busca um track pelo ID.

        Args:
            track_id (int): ID do registro

        Returns:
            dict: Dados do track ou None se não encontrado
        """
        try:
            self.cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar track por ID: {str(e)}", color="red")
            return None

    def search_tracks(self, ponto=None, pista=None, track=None):
        """
        Busca tracks pelos termos fornecidos.

        Args:
            ponto (str, opcional): Termo para buscar no campo ponto
            pista (str, opcional): Termo para buscar no campo pista
            track (str, opcional): Termo para buscar no campo track

        Returns:
            list: Lista de tracks encontrados
        """
        try:
            query = "SELECT * FROM tracks WHERE 1=1"
            params = []

            if ponto:
                query += " AND ponto LIKE ?"
                params.append(f"%{ponto}%")

            if pista:
                query += " AND pista LIKE ?"
                params.append(f"%{pista}%")

            if track:
                query += " AND track LIKE ?"
                params.append(f"%{track}%")

            query += " ORDER BY pista, ponto"

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar tracks: {str(e)}", color="red")
            return []

    def add_track(self, track_data):
        """
        Adiciona um novo track ao banco de dados.

        Args:
            track_data (dict): Dados do track com as chaves: ponto, pista, track

        Returns:
            dict: Dados do track inserido com ID ou dict com erro
        """
        try:
            # Validar campos obrigatórios
            if not all(k in track_data for k in ['ponto', 'pista', 'track']):
                return {"error": "Campos obrigatórios ausentes (ponto, pista, track)"}

            # Inserir o novo track
            self.cursor.execute("""
                INSERT INTO tracks (ponto, pista, track)
                VALUES (?, ?, ?)
            """, (
                track_data['ponto'],
                track_data['pista'],
                track_data['track']
            ))

            # Commit para salvar as alterações
            last_id = self.cursor.lastrowid
            self.conn.commit()

            # Retornar o registro recém-inserido
            return self.get_track_by_id(last_id)
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao adicionar track: {str(e)}", color="red")
            self.conn.rollback()
            return {"error": str(e)}

    def update_track(self, track_id, track_data):
        """
        Atualiza um track existente.

        Args:
            track_id (int): ID do track a ser atualizado
            track_data (dict): Novos dados do track (chaves: ponto, pista, track)

        Returns:
            dict: Dados atualizados do track ou dict com erro
        """
        try:
            # Verificar se o track existe
            existing_track = self.get_track_by_id(track_id)
            if not existing_track:
                return {"error": f"Track com ID {track_id} não encontrado"}

            # Construir a query de update
            fields = []
            values = []
            for key, value in track_data.items():
                if key in ['ponto', 'pista', 'track']:
                    fields.append(f"{key} = ?")
                    values.append(value)

            if not fields:
                return {"error": "Nenhum campo válido para atualização"}

            # Adicionar updated_at
            fields.append("updated_at = CURRENT_TIMESTAMP")

            # Montar a query
            query = f"UPDATE tracks SET {', '.join(fields)} WHERE id = ?"
            values.append(track_id)

            # Executar a query
            self.cursor.execute(query, values)
            self.conn.commit()

            # Retornar o registro atualizado
            return self.get_track_by_id(track_id)
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao atualizar track: {str(e)}", color="red")
            self.conn.rollback()
            return {"error": str(e)}

    def delete_track(self, track_id):
        """
        Remove um track pelo ID.

        Args:
            track_id (int): ID do track a ser removido

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        try:
            # Verificar se o track existe
            existing_track = self.get_track_by_id(track_id)
            if not existing_track:
                return False

            # Remover o track
            self.cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            self.conn.commit()
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao remover track: {str(e)}", color="red")
            self.conn.rollback()
            return False

    def import_tracks_from_csv(self, file_path, overwrite=True):
        """
        Importa tracks de um arquivo CSV.

        Args:
            file_path (str): Caminho para o arquivo CSV
            overwrite (bool): Se True, limpa todos os dados existentes antes de importar

        Returns:
            dict: Resultado da importação com contadores
        """
        try:
            if not os.path.exists(file_path):
                return {"error": f"Arquivo {file_path} não encontrado"}

            # Ler o CSV
            df = pd.read_csv(file_path, encoding='utf-8')

            # Verificar se possui as colunas necessárias
            required_cols = ['ponto', 'pista', 'track']
            missing_cols = [col for col in required_cols if col.lower() not in [c.lower() for c in df.columns]]

            if missing_cols:
                return {"error": f"Colunas obrigatórias ausentes: {', '.join(missing_cols)}"}

            # Mapear nomes de colunas para minúsculas
            column_map = {col: col.lower() for col in df.columns if col.lower() in ['ponto', 'pista', 'track']}
            df = df.rename(columns=column_map)

            # Iniciar transação
            self.conn.begin()

            if overwrite:
                # Limpar a tabela se estiver substituindo todos os registros
                self.cursor.execute("DELETE FROM tracks")

                # Inserir todos os registros
                for _, row in df.iterrows():
                    self.cursor.execute("""
                        INSERT INTO tracks (ponto, pista, track)
                        VALUES (?, ?, ?)
                    """, (
                        row['ponto'],
                        row['pista'],
                        row['track']
                    ))

                result = {
                    "status": "success",
                    "message": f"Importação concluída: {len(df)} registros importados",
                    "imported": len(df),
                    "updated": 0,
                    "skipped": 0
                }
            else:
                # Essa implementação é simplificada. Em um cenário real,
                # você precisaria definir uma chave única ou combinação de campos
                # para identificar registros duplicados.
                added = 0

                for _, row in df.iterrows():
                    # Adicionar novo
                    self.cursor.execute("""
                        INSERT INTO tracks (ponto, pista, track)
                        VALUES (?, ?, ?)
                    """, (
                        row['ponto'],
                        row['pista'],
                        row['track']
                    ))
                    added += 1

                result = {
                    "status": "success",
                    "message": f"Importação concluída: {added} registros adicionados",
                    "imported": added,
                    "updated": 0,
                    "skipped": 0
                }

            # Commit para salvar as alterações
            self.conn.commit()
            return result
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao importar tracks: {str(e)}", color="red")
            self.conn.rollback()
            return {"error": str(e)}


def export_tracks_to_csv(self, file_path=None):
    """
    Exporta os tracks para um arquivo CSV.

    Args:
        file_path (str, opcional): Caminho para salvar o arquivo CSV.
                                  Se None, gera um nome baseado na data atual.

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
            file_path = os.path.join(export_dir, f"tracks_export_{timestamp}.csv")

        # Consultar todos os tracks
        self.cursor.execute("SELECT ponto, pista, track FROM tracks ORDER BY pista, ponto")
        rows = self.cursor.fetchall()

        # Converter para DataFrame
        df = pd.DataFrame([dict(row) for row in rows])

        # Exportar para CSV
        df.to_csv(file_path, index=False, encoding='utf-8')
        return file_path
    except Exception as e:
        report_exception(e)
        trace(f"Erro ao exportar tracks: {str(e)}", color="red")
        return f"Erro ao exportar: {str(e)}"

# =================== Métodos para migração do CSV atual ===================


def migrate_eja_from_csv(self, csv_path=None):
    """
    Migra dados de EJA do arquivo CSV atual para o banco de dados SQLite.

    Args:
        csv_path (str, opcional): Caminho para o arquivo CSV de EJAs.
                                    Se None, usa o arquivo padrão.

    Returns:
        dict: Resultado da migração
    """
    if csv_path is None:
        # Usar o arquivo padrão no diretório aux_files
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "aux_files", "eja_simplificado.csv")

    if not os.path.exists(csv_path):
        return {"error": f"Arquivo CSV não encontrado: {csv_path}"}

    # Importar o CSV
    return self.import_ejas_from_csv(csv_path)

# =================== Métodos para execução direta de SQL ===================


def execute_query(self, query, params=None):
    """
    Executa uma consulta SQL diretamente.

    Args:
        query (str): Query SQL a ser executada
        params (tuple, opcional): Parâmetros para a query

    Returns:
        list: Resultado da consulta ou None em caso de erro
    """
    try:
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        # Se for uma consulta SELECT, retorna os resultados
        if query.strip().upper().startswith("SELECT"):
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

        # Se for outra operação (INSERT, UPDATE, DELETE), commit e retorna o número de linhas afetadas
        else:
            self.conn.commit()
            return {"rows_affected": self.cursor.rowcount}
    except Exception as e:
        report_exception(e)
        trace(f"Erro ao executar query: {str(e)}", color="red")
        self.conn.rollback()
        return {"error": str(e)}


def execute_script(self, script):
    """
    Executa um script SQL completo.

    Args:
        script (str): Script SQL com múltiplas instruções

    Returns:
        bool: True se executado com sucesso, False caso contrário
    """
    try:
        self.cursor.executescript(script)
        self.conn.commit()
        return True
    except Exception as e:
        report_exception(e)
        trace(f"Erro ao executar script SQL: {str(e)}", color="red")
        self.conn.rollback()
        return False

# =================== Métodos para backup e restauração ===================


def backup_database(self, backup_path=None):
    """
    Cria um backup do banco de dados.

    Args:
        backup_path (str, opcional): Caminho para salvar o backup.
                                    Se None, gera um nome baseado na data atual.

    Returns:
        str: Caminho do arquivo de backup ou mensagem de erro
    """
    try:
        if backup_path is None:
            # Gerar nome baseado na data atual
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"db_backup_{timestamp}.sqlite")

        # Criar uma conexão com o banco de backup
        backup_conn = sqlite3.connect(backup_path)

        # Usar o método de backup integrado do SQLite
        self.conn.backup(backup_conn)

        # Fechar a conexão do backup
        backup_conn.close()

        return backup_path
    except Exception as e:
        report_exception(e)
        trace(f"Erro ao criar backup: {str(e)}", color="red")
        return f"Erro ao criar backup: {str(e)}"


def restore_database(self, backup_path):
    """
    Restaura o banco de dados a partir de um backup.

    Args:
        backup_path (str): Caminho para o arquivo de backup

    Returns:
        bool: True se restaurado com sucesso, False caso contrário
    """
    try:
        if not os.path.exists(backup_path):
            trace(f"Arquivo de backup não encontrado: {backup_path}", color="red")
            return False

        # Fechar a conexão atual
        self.close()

        # Fazer backup do banco atual antes de sobrescrever
        current_backup = self.db_path + ".bak"
        if os.path.exists(self.db_path):
            import shutil
            shutil.copy2(self.db_path, current_backup)

        # Copiar o arquivo de backup para o local do banco de dados
        import shutil
        shutil.copy2(backup_path, self.db_path)

        # Reconectar ao banco restaurado
        self.connect()

        return True
    except Exception as e:
        report_exception(e)
        trace(f"Erro ao restaurar banco de dados: {str(e)}", color="red")

        # Tentar restaurar do backup se algo deu errado
        if os.path.exists(current_backup):
            try:
                import shutil
                shutil.copy2(current_backup, self.db_path)
                trace("Restaurada versão anterior do banco de dados", color="yellow")
            except Exception as ex:
                print(ex)
                pass

        # Tentar reconectar
        self.connect()

        return False


# Função auxiliar para obter uma instância do manipulador de banco de dados
def get_db_handler():
    """Retorna uma instância do manipulador de banco de dados local."""
    return LocalDatabaseHandler()


# Função principal para migrar dados do CSV para o SQLite
def migrate_data_from_csv():
    """
    Migra dados dos arquivos CSV existentes para o banco de dados SQLite.
    Pode ser executado como script independente.
    """
    try:
        db = LocalDatabaseHandler()

        # Migrar dados de EJA
        eja_result = db.migrate_eja_from_csv()
        if 'error' in eja_result:
            print(f"Erro ao migrar EJAs: {eja_result['error']}")
        else:
            print(f"Migração de EJAs concluída: {eja_result.get('imported', 0)} registros importados")

        # Aqui você pode adicionar código para migrar outros dados se necessário

        return True
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        return False


# Executar a migração se este script for executado diretamente
if __name__ == "__main__":
    print("Iniciando migração de dados CSV para SQLite...")
    success = migrate_data_from_csv()
    if success:
        print("Migração concluída com sucesso!")
    else:
        print("Migração falhou.")
