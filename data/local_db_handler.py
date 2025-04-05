# data/local_db_handler.py
import os
import sqlite3
import pandas as pd
from utils.tracer import trace, report_exception
from datetime import datetime


class LocalDatabaseHandler:
    """
    Classe simplificada para gerenciar o banco de dados SQLite local do dashboard.
    """

    def __init__(self, db_path=None):
        """
        Inicializa o gerenciador de banco de dados SQLite.

        Args:
            db_path (str, opcional): Caminho para o arquivo de banco de dados.
                                    Se None, usa o caminho padrão.
        """
        if db_path is None:
            # Caminho padrão no diretório de dados
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                        "data", "database.db")
        else:
            self.db_path = db_path

        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Verificar se o banco precisa ser criado
        db_exists = os.path.exists(self.db_path)

        # Conectar ao banco
        self.conn = None
        self.cursor = None
        self.connect()

        # Criar tabelas se necessário
        if not db_exists:
            self.create_tables()

    def connect(self):
        """Estabelece conexão com o banco de dados SQLite."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acessar colunas pelo nome
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao conectar ao banco de dados SQLite: {str(e)}", color="red")
            return False

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self):
        """Cria as tabelas necessárias no banco de dados."""
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

            # Criar a tabela tracks
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ponto TEXT,
                pista TEXT,
                track TEXT
            )
            ''')

            # Tabela clients_usage para armazenar utilização semanal
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_number INTEGER NOT NULL,      -- Número da semana no ano (1-53)
                year INTEGER NOT NULL,             -- Ano
                start_date TEXT NOT NULL,          -- Data inicial da semana (YYYY-MM-DD)
                end_date TEXT NOT NULL,            -- Data final da semana (YYYY-MM-DD)
                client_name TEXT NOT NULL,         -- Nome do cliente
                classification TEXT NOT NULL,      -- Classificação (PROGRAMS, OTHER SKILL TEAMS, etc.)
                hours REAL NOT NULL,               -- Horas consumidas (valor decimal)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Criar índices para melhorar a performance
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_eja_code ON eja (eja_code)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_eja_title ON eja (title)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_eja_class ON eja (new_classification)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_track_pista ON tracks (pista)')

            # Índices para a tabela clients_usage
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_week ON clients_usage (week_number, year)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_date ON clients_usage (start_date, end_date)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_client ON clients_usage (client_name)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_class ON clients_usage (classification)')

            # Commit para salvar as alterações
            self.conn.commit()
            trace("Tabelas criadas com sucesso no SQLite.", color="green")
            return True
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao criar tabelas no SQLite: {str(e)}", color="red")
            self.conn.rollback()
            return False

    def select(self, script):
        """Retorna todos os EJAs do banco de dados."""
        try:
            self.cursor.execute(script)
            return self.cursor.fetchone()
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao fazer select: {str(e)}", color="red")
            return None

    def get_client_usage_data(self, weeks=52, classification=None):
        try:
            query = """
                SELECT
                    client_name,
                    classification,
                    SUM(hours) as total_hours,
                    year,
                    week_number,
                    start_date
                FROM clients_usage
                WHERE 1=1
            """

            params = []

            if classification:
                query += " AND classification = ?"
                params.append(classification)

            # Limitar às semanas mais recentes
            if weeks > 0:
                query += """
                    AND (year, week_number) IN (
                        SELECT year, week_number FROM clients_usage
                        GROUP BY year, week_number
                        ORDER BY year DESC, week_number DESC
                        LIMIT ?
                    )
                """
                params.append(weeks)

            query += " GROUP BY client_name, classification ORDER BY total_hours DESC"

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            if not rows:
                return pd.DataFrame()

            # Converter para DataFrame
            import pandas as pd
            df = pd.DataFrame([dict(row) for row in rows])

            return df

        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter dados de utilização por cliente: {str(e)}", color="red")
            return pd.DataFrame()

    # =================== Métodos para gerenciamento de EJAs ===================

    def get_all_ejas(self):
        """Retorna todos os EJAs do banco de dados."""
        try:
            self.cursor.execute("SELECT * FROM eja ORDER BY eja_code")
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao obter todos os EJAs: {str(e)}", color="red")
            return []

    def get_eja_by_id(self, eja_id):
        """Busca um EJA pelo ID."""
        try:
            self.cursor.execute("SELECT * FROM eja WHERE id = ?", (eja_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar EJA por ID: {str(e)}", color="red")
            return None

    def get_eja_by_code(self, eja_code):
        """Busca um EJA pelo código."""
        try:
            self.cursor.execute("SELECT * FROM eja WHERE eja_code = ?", (eja_code,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao buscar EJA por código: {str(e)}", color="red")
            return None

    def search_ejas(self, search_term=None, eja_code=None, classification=None):
        """Busca EJAs pelos termos fornecidos."""
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
            ret = [dict(row) for row in rows]
            trace(f"Search result: {ret}")
            return ret
        except Exception as e:
            report_exception(e)
            trace(f"Erro na busca de EJAs: {str(e)}", color="red")
            return []

    def add_eja(self, eja_data):
        """Adiciona um novo EJA ao banco de dados."""
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
        """Atualiza um EJA existente."""
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
        """Remove um EJA pelo ID."""
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

    # =================== Métodos para importação/exportação de CSV ===================

    def import_ejas_from_csv(self, file_path, overwrite=True):
        """
        Importa EJAs de um arquivo CSV para o banco de dados.

        Args:
            file_path (str): Caminho do arquivo CSV
            overwrite (bool): Se True, substitui todos os dados existentes

        Returns:
            dict: Resultado da importação com contadores
        """
        if not os.path.exists(file_path):
            return {"error": f"Arquivo {file_path} não encontrado"}

        try:
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
            self.cursor.execute("BEGIN TRANSACTION")

            try:
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

            except Exception:
                # Rollback em caso de erro dentro da transação
                self.conn.rollback()
                raise

        except pd.errors.EmptyDataError:
            return {"error": "O arquivo CSV está vazio"}
        except pd.errors.ParserError:
            return {"error": "Erro ao analisar o arquivo CSV. Verifique o formato."}
        except Exception as e:
            report_exception(e)
            trace(f"Erro ao importar EJAs do CSV: {str(e)}", color="red")
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
            trace(f"Erro ao exportar EJAs para CSV: {str(e)}", color="red")
            return f"Erro ao exportar: {str(e)}"

    # =================== Método para backup do banco de dados ===================

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
            trace(f"Erro ao criar backup do banco: {str(e)}", color="red")
            return f"Erro ao criar backup: {str(e)}"


# Função auxiliar para obter uma instância do gerenciador de banco de dados
def get_db_handler():
    """Retorna uma instância do gerenciador de banco de dados local."""
    return LocalDatabaseHandler()


if __name__ == '__main__':
    local_db = get_db_handler()
