# data/tracks_manager.py
# Gerenciador unificado de Tracks para o dashboard ZeenTech VEV
import os
import pandas as pd
from utils.tracer import trace, report_exception
from datetime import datetime

# Importar o gerenciador de banco de dados SQLite
from data.local_db_handler import LocalDatabaseHandler, get_db_handler


class TracksManager:
    """
    Classe unificada para gerenciar os dados de Tracks, utilizando SQLite como armazenamento.
    """

    def __init__(self):
        """Inicializa o gerenciador de Tracks."""
        try:
            # Inicializar o gerenciador de banco de dados SQLite
            self.db_handler = LocalDatabaseHandler()
            self.use_sqlite = True
            trace("Gerenciador de Tracks inicializado com SQLite", color="green")
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao inicializar gerenciador de Tracks: {str(e)}", color="red")

    def get_all_tracks(self):
        """
        Retorna todos os Tracks.

        Returns:
            list: Lista de dicionários com os dados dos Tracks
        """
        try:
            self.db_handler.cursor.execute("SELECT * FROM tracks ORDER BY track")
            rows = self.db_handler.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter todos os Tracks: {str(e)}", color="red")
            return []

    def search_tracks(self, search_term=None, track_type=None, pista=None):
        """
        Busca Tracks pelos critérios fornecidos.

        Args:
            search_term (str): Termo de busca para o track
            track_type (str): Tipo específico de track
            pista (str): Pista específica

        Returns:
            list: Lista de Tracks correspondentes aos critérios
        """
        try:
            query = "SELECT * FROM tracks WHERE 1=1"
            params = []

            if search_term:
                query += " AND track LIKE ?"
                params.append(f"%{search_term}%")

            if track_type:
                query += " AND track = ?"
                params.append(track_type)

            if pista:
                query += " AND pista = ?"
                params.append(pista)

            query += " ORDER BY track"

            self.db_handler.cursor.execute(query, params)
            rows = self.db_handler.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro na busca de Tracks: {str(e)}", color="red")
            return []

    def get_track_by_id(self, track_id):
        """
        Busca um Track pelo seu ID.

        Args:
            track_id (int): ID do Track

        Returns:
            dict: Dados do Track ou None se não encontrado
        """
        try:
            track_id = int(track_id)
            self.db_handler.cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
            row = self.db_handler.cursor.fetchone()
            return dict(row) if row else None
        except (ValueError, TypeError):
            trace(f"ID de Track inválido: {track_id}", color="yellow")
            return None
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar Track por ID: {str(e)}", color="red")
            return None

    def add_track(self, track_data):
        """
        Adiciona um novo Track.

        Args:
            track_data (dict): Dados do Track a ser adicionado

        Returns:
            dict: Dados do Track adicionado ou dict com erro
        """
        try:
            # Validar campos obrigatórios
            if not track_data.get('track') or not track_data.get('pista'):
                return {"error": "Track e Pista são obrigatórios"}

            # Formatando o dicionário de dados
            formatted_data = {
                'track': track_data['track'],
                'pista': track_data['pista'],
                'ponto': track_data.get('ponto', '')
            }

            # Inserir o novo Track
            self.db_handler.cursor.execute("""
                INSERT INTO tracks (track, pista, ponto)
                VALUES (?, ?, ?)
            """, (
                formatted_data['track'],
                formatted_data['pista'],
                formatted_data['ponto']
            ))

            # Commit para salvar as alterações
            self.db_handler.conn.commit()

            # Retornar o registro recém-inserido
            self.db_handler.cursor.execute("SELECT * FROM tracks WHERE id = last_insert_rowid()")
            row = self.db_handler.cursor.fetchone()
            return dict(row) if row else {"error": "Erro ao retornar o Track inserido"}
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao adicionar Track: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return {"error": str(e)}

    def update_track(self, track_id, track_data):
        """
        Atualiza um Track existente.

        Args:
            track_id (int): ID do Track a ser atualizado
            track_data (dict): Novos dados do Track

        Returns:
            dict: Dados atualizados do Track ou dict com erro
        """
        try:
            track_id = int(track_id)

            # Verificar se o Track existe
            existing_track = self.get_track_by_id(track_id)
            if not existing_track:
                return {"error": f"Track com ID {track_id} não encontrado"}

            # Validar campos obrigatórios
            if not track_data.get('track') or not track_data.get('pista'):
                return {"error": "Track e Pista são obrigatórios"}

            # Construir a query de update
            fields = []
            values = []
            for key, value in track_data.items():
                if key in ['track', 'pista', 'ponto']:
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
            self.db_handler.cursor.execute(query, values)
            self.db_handler.conn.commit()

            # Retornar o registro atualizado
            return self.get_track_by_id(track_id)
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao atualizar Track: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return {"error": str(e)}

    def delete_track(self, track_id):
        """
        Remove um Track.

        Args:
            track_id (int): ID do Track a ser removido

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        try:
            track_id = int(track_id)

            # Verificar se o Track existe
            existing_track = self.get_track_by_id(track_id)
            if not existing_track:
                return False

            # Remover o Track
            self.db_handler.cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            self.db_handler.conn.commit()
            return True
        except (ValueError, TypeError):
            trace(f"ID de Track inválido para exclusão: {track_id}", color="yellow")
            return False
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao excluir Track: {str(e)}", color="red")
            self.db_handler.conn.rollback()
            return False

    def get_all_pistas(self):
        """
        Retorna todas as pistas únicas disponíveis.

        Returns:
            list: Lista de pistas
        """
        try:
            self.db_handler.cursor.execute("SELECT DISTINCT pista FROM tracks WHERE pista IS NOT NULL AND pista != '' ORDER BY pista")
            rows = self.db_handler.cursor.fetchall()
            return [row['pista'] for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter pistas: {str(e)}", color="red")
            return []

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

            # Ler o CSV
            df = pd.read_csv(file_path, encoding='utf-8')

            # Verificar se possui as colunas necessárias
            required_cols = ['TRACK', 'PISTA']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                return {"error": f"Colunas obrigatórias ausentes: {', '.join(missing_cols)}"}

            # Iniciar transação
            self.db_handler.cursor.execute("BEGIN TRANSACTION")

            try:
                if overwrite:
                    # Limpar a tabela se estiver substituindo todos os registros
                    self.db_handler.cursor.execute("DELETE FROM tracks")

                    # Inserir todos os registros
                    imported = 0
                    for _, row in df.iterrows():
                        self.db_handler.cursor.execute("""
                            INSERT INTO tracks (track, pista, ponto)
                            VALUES (?, ?, ?)
                        """, (
                            row['TRACK'],
                            row['PISTA'],
                            row['PONTO'] if 'PONTO' in df.columns else ''
                        ))
                        imported += 1

                    result = {
                        "status": "success",
                        "message": f"Importação concluída: {imported} registros importados",
                        "imported": imported,
                        "updated": 0,
                        "skipped": 0
                    }
                else:
                    # Atualizar apenas os existentes ou adicionar novos
                    updated = 0
                    added = 0
                    skipped = 0

                    for _, row in df.iterrows():
                        track_name = row['TRACK']
                        pista_name = row['PISTA']

                        # Verificar se já existe
                        self.db_handler.cursor.execute(
                            "SELECT id FROM tracks WHERE track = ? AND pista = ?",
                            (track_name, pista_name)
                        )
                        existing = self.db_handler.cursor.fetchone()

                        if existing:
                            # Atualizar existente
                            self.db_handler.cursor.execute("""
                                UPDATE tracks SET
                                    ponto = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (
                                row['PONTO'] if 'PONTO' in df.columns else '',
                                existing['id']
                            ))
                            updated += 1
                        else:
                            # Adicionar novo
                            self.db_handler.cursor.execute("""
                                INSERT INTO tracks (track, pista, ponto)
                                VALUES (?, ?, ?)
                            """, (
                                track_name,
                                pista_name,
                                row['PONTO'] if 'PONTO' in df.columns else ''
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
                self.db_handler.conn.commit()
                return result

            except Exception:
                # Rollback em caso de erro dentro da transação
                self.db_handler.conn.rollback()
                raise

        except pd.errors.EmptyDataError:
            return {"error": "O arquivo CSV está vazio"}
        except pd.errors.ParserError:
            return {"error": "Erro ao analisar o arquivo CSV. Verifique o formato."}
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao importar Tracks do CSV: {str(e)}", color="red")
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
                file_path = os.path.join(export_dir, f"tracks_export_{timestamp}.csv")

            # Consultar todos os Tracks
            self.db_handler.cursor.execute("""
                SELECT
                    id as 'ID',
                    track as 'TRACK',
                    pista as 'PISTA',
                    ponto as 'PONTO'
                FROM tracks
                ORDER BY track, pista
            """)

            rows = self.db_handler.cursor.fetchall()

            # Converter para DataFrame
            df = pd.DataFrame([dict(row) for row in rows])

            # Exportar para CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            return file_path
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao exportar Tracks para CSV: {str(e)}", color="red")
            return f"Erro ao exportar: {str(e)}"


# Função auxiliar para obter uma instância do gerenciador de Tracks
def get_tracks_manager():
    """Retorna uma instância do gerenciador de Tracks."""
    return TracksManager()
