# data/weekly_processor.py
# Processador semanal de dados de utilização por cliente
import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.tracer import trace, report_exception
from data.local_db_handler import get_db_handler
from data.db_connection import get_db_connection
from data.database import ReportGenerator
from data.eja_manager import get_eja_manager


class WeeklyUsageProcessor:
    """
    Processador de utilização semanal por cliente.
    Coleta dados da semana anterior e armazena na tabela 'clients_usage'.
    """

    def __init__(self):
        self.db_handler = get_db_handler()
        self.sql_connection = get_db_connection()

    def get_week_range(self, date=None):
        """
        Calcula o intervalo da semana anterior para a data fornecida.
        Se nenhuma data for fornecida, usa a data atual.

        Args:
            date (datetime, opcional): Data de referência. Default é data atual.

        Returns:
            tuple: (início da semana anterior, fim da semana anterior, número da semana, ano)
        """
        if date is None:
            date = datetime.now()

        # Calcular o início da semana atual (segunda-feira)
        start_of_current_week = date - timedelta(days=date.weekday())
        start_of_current_week = start_of_current_week.replace(hour=0, minute=0, second=0, microsecond=0)

        # Calcular início e fim da semana anterior
        end_of_previous_week = start_of_current_week - timedelta(seconds=1)
        start_of_previous_week = end_of_previous_week - timedelta(days=6)

        # Calcular o número da semana e ano
        year = start_of_previous_week.year
        week_number = start_of_previous_week.isocalendar()[1]

        return start_of_previous_week, end_of_previous_week, week_number, year

    def process_weekly_data(self):
        """
        Processa os dados da semana anterior e armazena na tabela 'clients_usage'.

        Returns:
            dict: Resultado do processamento com contadores
        """
        try:
            # Obter intervalo da semana anterior
            start_date, end_date, week_number, year = self.get_week_range()

            trace(f"Processando dados da semana {week_number}/{year}: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")

            # Formatar datas para a stored procedure
            start_date_str = start_date.strftime('%Y-%m-%d 00:00:00.000')
            end_date_str = end_date.strftime('%Y-%m-%d 23:59:59.999')

            # Verificar se já existem dados para esta semana
            self.db_handler.cursor.execute(
                "SELECT COUNT(*) FROM clients_usage WHERE week_number = ? AND year = ?",
                (week_number, year)
            )
            count = self.db_handler.cursor.fetchone()[0]

            if count > 0:
                trace(f"Dados da semana {week_number}/{year} já existem. Removendo antes de atualizar...")
                self.db_handler.cursor.execute(
                    "DELETE FROM clients_usage WHERE week_number = ? AND year = ?",
                    (week_number, year)
                )
                self.db_handler.conn.commit()

            # Obter dados do banco principal através da stored procedure
            if not self.sql_connection:
                trace("Não foi possível estabelecer conexão com o banco de dados principal.", color="red")
                return {"error": "Falha na conexão com o banco de dados"}

            # Executar a stored procedure para obter os dados
            dashboard_df = self.sql_connection.execute_stored_procedure_df(
                "sp_VehicleAccessReport",
                [start_date_str, end_date_str]
            )

            if dashboard_df is None or dashboard_df.empty:
                trace("Nenhum dado retornado pela stored procedure.", color="yellow")
                return {"error": "Nenhum dado disponível para o período"}

            # Carregar dados de EJA para processamento
            eja_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aux_files", "eja_simplificado.csv")
            if not os.path.exists(eja_path):
                trace(f"Arquivo EJA não encontrado em {eja_path}.", color="red")
                return {"error": "Arquivo EJA não encontrado"}

            # Instanciar o gerador de relatórios
            report_gen = ReportGenerator(dashboard_df=dashboard_df, eja_file=eja_path)

            # Processar dados para cada classificação
            classifications = ["PROGRAMS", "OTHER SKILL TEAMS", "INTERNAL USERS", "EXTERNAL SALES"]
            inserted_count = 0

            # Iniciar transação
            self.db_handler.cursor.execute("BEGIN TRANSACTION")

            # Processar e inserir dados para cada classificação
            for classification in classifications:
                report_data = report_gen.gerar_relatorio_eja(classification)

                if 'error' in report_data:
                    trace(f"Erro ao processar dados para {classification}: {report_data['error']}", color="yellow")
                    continue

                # Inserir dados para cada cliente na classificação
                for item in report_data['top_itens']:
                    self.db_handler.cursor.execute('''
                        INSERT INTO clients_usage
                        (week_number, year, start_date, end_date, client_name, classification, hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        week_number,
                        year,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d'),
                        item['TITLE'],
                        classification,
                        item['HORAS_DECIMAL']
                    ))
                    inserted_count += 1

            # Commit da transação
            self.db_handler.conn.commit()

            trace(f"Processamento concluído: {inserted_count} registros inseridos para a semana {week_number}/{year}", color="green")

            return {
                "status": "success",
                "week_number": week_number,
                "year": year,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "records_inserted": inserted_count
            }

        except Exception as e:
            # Rollback em caso de erro
            if self.db_handler.conn:
                self.db_handler.conn.rollback()

            report_exception(e)
            trace(f"Erro ao processar dados semanais: {str(e)}", color="red")
            return {"error": str(e)}

    def get_weekly_data(self, classifications=None, weeks=12):
        """
        Recupera os dados semanais armazenados para os últimos N semanas.

        Args:
            classifications (list, opcional): Lista de classificações para filtrar
            weeks (int, opcional): Número de semanas para recuperar. Default é 12.

        Returns:
            pd.DataFrame: DataFrame com os dados semanais agrupados
        """
        try:
            query = """
                SELECT
                    week_number,
                    year,
                    start_date,
                    end_date,
                    client_name,
                    classification,
                    SUM(hours) as total_hours
                FROM clients_usage
                WHERE 1=1
            """

            params = []

            if classifications:
                placeholders = ", ".join(["?"] * len(classifications))
                query += f" AND classification IN ({placeholders})"
                params.extend(classifications)

            # Limitar por número de semanas mais recentes
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

            query += " GROUP BY week_number, year, client_name, classification ORDER BY year DESC, week_number DESC"

            self.db_handler.cursor.execute(query, params)
            rows = self.db_handler.cursor.fetchall()

            if not rows:
                return pd.DataFrame()

            # Converter para DataFrame
            df = pd.DataFrame([dict(row) for row in rows])

            # Converter data strings para objetos datetime
            if 'start_date' in df.columns:
                df['start_date'] = pd.to_datetime(df['start_date'])
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'])

            return df

        except Exception as e:
            report_exception(e)
            trace(f"Erro ao recuperar dados semanais: {str(e)}", color="red")
            return pd.DataFrame()


# data/weekly_processor.py (adicione estas funções)

def setup_scheduler(run_immediately=False):
    """
    Configura o agendador para ser executado dentro de outra aplicação.

    Args:
        run_immediately (bool): Se True, executa o processamento imediatamente

    Returns:
        schedule.Job: O job agendado
    """
    import schedule
    import threading

    # Agendar para todas as segundas-feiras às 00:15
    job = schedule.every().monday.at("00:15").do(process_weekly_data)
    trace("Agendamento configurado: Processamento de dados de cliente toda segunda-feira às 00:15", color="green")

    # Executar imediatamente se solicitado
    if run_immediately:
        trace("Executando processamento inicial de dados de cliente", color="blue")
        # Executar em uma thread para não bloquear a aplicação
        threading.Thread(target=process_weekly_data).start()

    # Iniciar thread para verificar agendamentos pendentes
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    return job


def check_and_process_if_needed(force=False):
    """
    Verifica se dados da semana atual estão disponíveis e processa-os se necessário.

    Args:
        force (bool): Se True, força o processamento independentemente da verificação

    Returns:
        bool: True se os dados foram processados, False caso contrário
    """
    if force:
        # Forçar processamento
        trace("Forçando processamento de dados de cliente", color="blue")
        return process_weekly_data()

    # Obter semana atual
    processor = WeeklyUsageProcessor()
    start_date, end_date, week_number, year = processor.get_week_range()

    # Verificar se já existem dados para esta semana
    try:
        db_handler = get_db_handler()
        db_handler.cursor.execute(
            "SELECT COUNT(*) FROM clients_usage WHERE week_number = ? AND year = ?",
            (week_number, year)
        )
        count = db_handler.cursor.fetchone()[0]

        if count == 0:
            # Não há dados para a semana atual, processar
            trace(f"Dados da semana {week_number}/{year} não encontrados. Processando...", color="blue")
            return process_weekly_data()
        else:
            trace(f"Dados da semana {week_number}/{year} já estão disponíveis ({count} registros)", color="green")
            return False
    except Exception as e:
        report_exception(e)
        trace(f"Erro ao verificar dados da semana: {str(e)}", color="red")
        return False


# Função auxiliar para obter uma instância do processador
def get_weekly_processor():
    """Retorna uma instância do processador de uso semanal."""
    return WeeklyUsageProcessor()


# Função para executar o processamento diretamente
def process_weekly_data():
    """Executa o processamento dos dados da semana anterior."""
    processor = WeeklyUsageProcessor()
    result = processor.process_weekly_data()

    if 'error' in result:
        print(f"Erro no processamento: {result['error']}")
        return False
    else:
        print(f"Processamento concluído: {result['records_inserted']} registros inseridos para a semana {result['week_number']}/{result['year']}")
        return True


# Execução como script independente
if __name__ == "__main__":
    process_weekly_data()
