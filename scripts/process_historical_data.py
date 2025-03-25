# scripts/process_historical_data.py

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta

# sys.path.append(os.path.dirname(os.path.dirname(__file__)))


# Adicionar o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.local_db_handler import get_db_handler
from data.db_connection import get_db_connection
from data.database import ReportGenerator


def process_historical_weeks(num_weeks=52):
    """
    Processa dados históricos para as últimas N semanas.

    Args:
        num_weeks (int): Número de semanas para processar

    Returns:
        int: Número de semanas processadas com sucesso
    """
    # Obter conexões ao banco de dados
    db_handler = get_db_handler()
    sql_connection = get_db_connection()

    if not sql_connection:
        print("Não foi possível estabelecer conexão com o banco de dados principal.", color="red")
        return 0

    # Data de referência (hoje)
    current_date = datetime.now()

    success_count = 0
    error_count = 0
    skipped_count = 0

    # Processar cada semana, da mais recente para a mais antiga
    for week_offset in range(1, num_weeks + 1):
        # Calcular a data de referência para esta semana
        target_date = current_date - timedelta(weeks=week_offset)

        # Calcular o intervalo da semana
        start_of_week = target_date - timedelta(days=target_date.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # Calcular número da semana e ano
        year = start_of_week.year
        week_number = start_of_week.isocalendar()[1]

        print(f"Processando semana {week_number}/{year}: {start_of_week.strftime('%Y-%m-%d')} a {end_of_week.strftime('%Y-%m-%d')}")

        try:
            # Verificar se já existem dados para esta semana
            db_handler.cursor.execute(
                "SELECT COUNT(*) FROM clients_usage WHERE week_number = ? AND year = ?",
                (week_number, year)
            )
            count = db_handler.cursor.fetchone()[0]

            if count > 0:
                print(f"  Dados para semana {week_number}/{year} já existem ({count} registros). Pulando...")
                skipped_count += 1
                continue

            # Formatar datas para a stored procedure
            start_date_str = start_of_week.strftime('%Y-%m-%d 00:00:00.000')
            end_date_str = end_of_week.strftime('%Y-%m-%d 23:59:59.999')

            # Executar a stored procedure para obter os dados
            print(f"  Consultando banco de dados para o período {start_date_str} a {end_date_str}...")
            dashboard_df = sql_connection.execute_stored_procedure_df(
                "sp_VehicleAccessReport",
                [start_date_str, end_date_str]
            )

            if dashboard_df is None or dashboard_df.empty:
                print(f"  Nenhum dado retornado pela stored procedure para semana {week_number}/{year}.")
                error_count += 1
                continue

            print(f"  Processando {len(dashboard_df)} registros obtidos...")

            # Usar o novo gerador de relatórios com SQLite
            report_gen = ReportGenerator(dashboard_df=dashboard_df, db_handler=db_handler)

            # Processar dados para cada classificação
            classifications = ["PROGRAMS", "OTHER SKILL TEAMS", "INTERNAL USERS", "EXTERNAL SALES"]
            inserted_count = 0

            # Iniciar transação
            db_handler.cursor.execute("BEGIN TRANSACTION")

            try:
                # Remover registros antigos para esta semana (se existirem)
                db_handler.cursor.execute(
                    "DELETE FROM clients_usage WHERE week_number = ? AND year = ?",
                    (week_number, year)
                )

                # Processar e inserir dados para cada classificação
                for classification in classifications:
                    print(f"  Processando classificação: {classification}")
                    report_data = report_gen.gerar_relatorio_eja(classification)

                    if 'error' in report_data:
                        print(f"    Erro ao processar dados para {classification}: {report_data['error']}")
                        continue

                    print(f"    Encontrados {len(report_data['top_itens'])} itens para {classification}")

                    # Inserir dados para cada cliente na classificação
                    for idx, item in enumerate(report_data['top_itens']):
                        try:
                            db_handler.cursor.execute('''
                                INSERT INTO clients_usage
                                (week_number, year, start_date, end_date, client_name, classification, hours)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                week_number,
                                year,
                                start_of_week.strftime('%Y-%m-%d'),
                                end_of_week.strftime('%Y-%m-%d'),
                                item['TITLE'],
                                classification,
                                item['HORAS_DECIMAL']
                            ))
                            inserted_count += 1

                            if idx % 10 == 0:  # Log a cada 10 inserções
                                print(f"      Progresso: {idx+1}/{len(report_data['top_itens'])} itens inseridos")

                        except Exception as e:
                            print(f"      ERRO ao inserir item {idx+1}: {str(e)}")

                # Commit da transação
                db_handler.conn.commit()
                print(f"  Semana {week_number}/{year} processada com sucesso: {inserted_count} registros inseridos")
                success_count += 1

            except Exception as e:
                # Rollback em caso de erro
                db_handler.conn.rollback()
                print(f"  Erro ao inserir dados para semana {week_number}/{year}: {str(e)}")
                error_count += 1

            # Pausa para não sobrecarregar o banco
            time.sleep(1)

        except Exception as e:
            print(f"  Erro ao processar semana {week_number}/{year}: {str(e)}")
            error_count += 1

    print("\nResumo do processamento histórico:")
    print(f"  Semanas processadas com sucesso: {success_count}")
    print(f"  Semanas puladas (já existentes): {skipped_count}")
    print(f"  Semanas com erro: {error_count}")
    print(f"  Total de semanas: {num_weeks}")

    return success_count


def verify_table_exists():
    """
    Verifica se a tabela clients_usage existe e a cria se necessário.

    Returns:
        bool: True se a tabela existe ou foi criada com sucesso
    """
    try:
        db_handler = get_db_handler()

        # Verificar se a tabela existe
        db_handler.cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='clients_usage'
        """)

        if db_handler.cursor.fetchone() is None:
            print("Tabela clients_usage não encontrada. Criando...")

            # Criar a tabela
            db_handler.cursor.execute('''
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

            # Criar índices
            db_handler.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_week ON clients_usage (week_number, year)')
            db_handler.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_date ON clients_usage (start_date, end_date)')
            db_handler.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_client ON clients_usage (client_name)')
            db_handler.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_usage_class ON clients_usage (classification)')

            db_handler.conn.commit()
            print("Tabela clients_usage criada com sucesso!")
        else:
            print("Tabela clients_usage já existe.")

        return True

    except Exception as e:
        print(f"Erro ao verificar/criar tabela: {str(e)}")
        return False


def list_processed_weeks():
    """
    Lista as semanas já processadas no banco de dados.

    Returns:
        pd.DataFrame: DataFrame com as semanas processadas
    """
    try:
        db_handler = get_db_handler()

        db_handler.cursor.execute("""
            SELECT
                year,
                week_number,
                start_date,
                end_date,
                COUNT(DISTINCT client_name) as client_count,
                COUNT(*) as record_count,
                SUM(hours) as total_hours
            FROM clients_usage
            GROUP BY year, week_number
            ORDER BY year DESC, week_number DESC
        """)

        rows = db_handler.cursor.fetchall()

        if not rows:
            print("Nenhuma semana processada encontrada.")
            return pd.DataFrame()

        # Converter para DataFrame
        df = pd.DataFrame([dict(row) for row in rows])

        # Formatar para exibição
        print(f"\nSemanas processadas ({len(df)} semanas):")
        for idx, row in df.iterrows():
            print(f"  Semana {row['week_number']}/{row['year']}: {row['start_date']} a {row['end_date']} - "
                  f"{row['client_count']} clientes, {row['record_count']} registros, {row['total_hours']:.1f} horas")

        return df

    except Exception as e:
        print(f"Erro ao listar semanas processadas: {str(e)}")
        return pd.DataFrame()


def clear_week_data(year, week_number):
    """
    Remove os dados de uma semana específica.

    Args:
        year (int): Ano
        week_number (int): Número da semana

    Returns:
        bool: True se os dados foram removidos com sucesso
    """
    try:
        db_handler = get_db_handler()

        # Verificar se existem dados para esta semana
        db_handler.cursor.execute(
            "SELECT COUNT(*) FROM clients_usage WHERE week_number = ? AND year = ?",
            (week_number, year)
        )
        count = db_handler.cursor.fetchone()[0]

        if count == 0:
            print(f"Nenhum dado encontrado para semana {week_number}/{year}.")
            return False

        # Remover os dados
        db_handler.cursor.execute(
            "DELETE FROM clients_usage WHERE week_number = ? AND year = ?",
            (week_number, year)
        )

        db_handler.conn.commit()
        print(f"Dados removidos com sucesso: {count} registros da semana {week_number}/{year}.")
        return True

    except Exception as e:
        print(f"Erro ao remover dados: {str(e)}")
        return False


if __name__ == "__main__":
    command = 'process'

    # Verificar se a tabela existe
    if not verify_table_exists():
        print("Não foi possível verificar/criar a tabela clients_usage. Abortando.")
        sys.exit(1)

    # Executar o comando apropriado
    if command == "process":
        # Obter número de semanas da linha de comando (padrão: 52 semanas = 1 ano)
        weeks = 104
        if len(sys.argv) > 2:
            try:
                weeks = int(sys.argv[2])
            except ValueError:
                print(f"Argumento inválido: {sys.argv[2]}. Usando padrão: 52 semanas.")

        print(f"Iniciando processamento histórico para as últimas {weeks} semanas...")
        processed = process_historical_weeks(weeks)
        print("Processamento histórico concluído.")

    elif command == "list":
        list_processed_weeks()

    elif command == "clear":
        if len(sys.argv) < 4:
            print("Uso: python process_historical_data.py clear [year] [week]")
            sys.exit(1)

        try:
            year = int(sys.argv[2])
            week = int(sys.argv[3])

            confirm = input(f"Tem certeza que deseja remover os dados da semana {week}/{year}? (s/n): ")
            if confirm.lower() == 's':
                clear_week_data(year, week)
            else:
                print("Operação cancelada.")
        except ValueError:
            print("Argumentos inválidos. Use: python process_historical_data.py clear [year] [week]")

    else:
        print(f"Comando desconhecido: {command}")
        print("Comandos válidos: process, list, clear")
        sys.exit(1)
