import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from utils.tracer import trace, report_exception
from data.db_connection import get_db_connection
from data.local_db_handler import get_db_handler
from contextlib import closing
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def convert_time_to_minutes(time_value):
    """
    Converte valor HH:MM para total de minutos.
    """
    try:
        if pd.isna(time_value) or time_value is None or time_value == '':
            return 0.0

        # Se for string, remove espaços
        if isinstance(time_value, str):
            time_value = time_value.strip()
            if time_value == '':
                return 0.0

            # Formato esperado: HH:MM
            if ':' in time_value:
                parts = time_value.split(':')
                if len(parts) >= 2:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    total_minutes = (hours * 60) + minutes
                    # print(f"DEBUG: Convertendo {time_value} -> {total_minutes} minutos")
                    return float(total_minutes)

        # Se não conseguiu converter, tenta como float direto
        result = float(time_value)
        # print(f"DEBUG: Valor {time_value} convertido diretamente para {result}")
        return result

    except (ValueError, TypeError) as e:
        print(f"ERRO: Erro ao converter tempo {time_value}: {str(e)}")
        return 0.0


def calculate_week_range(start_date=None):
    """
    Calcula o intervalo de semanas a partir de uma data inicial.
    """
    if start_date is None:
        start_date = datetime.now()

    # Calcular o início da semana (segunda-feira)
    start_of_week = start_date - timedelta(days=start_date.weekday())
    start_of_week = datetime(
        start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0
    )

    # Calcular o final da semana (domingo)
    end_of_week = start_of_week + timedelta(days=6)
    end_of_week = datetime(
        end_of_week.year, end_of_week.month, end_of_week.day, 23, 59, 59
    )

    return start_of_week, end_of_week


def safe_convert_hours(value):
    """
    Converte valor de horas para float de forma segura.
    """
    try:
        if pd.isna(value) or value is None or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def normalize_datetime_string(dt_value):
    """
    Normaliza valores de datetime para string padronizada.
    Trata valores nulos como string vazia para comparação.
    """
    if pd.isna(dt_value) or dt_value is None:
        return ""

    try:
        if isinstance(dt_value, str):
            # Se já é string, tenta converter para datetime e depois para string padronizada
            dt_obj = pd.to_datetime(dt_value, errors='coerce')
            if pd.isna(dt_obj):
                return ""
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Se é datetime, converte direto
            return pd.to_datetime(dt_value).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(dt_value) if dt_value else ""


def create_unique_key(client_name, entry_time, exit_time):
    """
    Cria uma chave única para identificar registros duplicados.
    """
    # Normalizar strings para comparação
    client = str(client_name).strip().upper() if client_name else "UNKNOWN"
    entry = normalize_datetime_string(entry_time)
    exit = normalize_datetime_string(exit_time)

    return f"{client}|{entry}|{exit}"


def process_weekly_data(start_date=None, end_date=None):
    """
    Processa os dados semanais evitando duplicatas de forma simples e robusta.
    """
    try:
        db_handler = get_db_handler()
        sql_connection = get_db_connection()

        if not sql_connection:
            trace("Falha na conexão com o banco de dados principal.", color="red")
            return {"error": "Conexão com o banco de dados principal falhou"}

        # Calcular intervalo da semana
        if start_date and end_date:
            if isinstance(start_date, datetime):
                start_of_week = start_date
            else:
                start_of_week = datetime.combine(start_date, datetime.min.time())

            if isinstance(end_date, datetime):
                end_of_week = end_date
            else:
                end_of_week = datetime.combine(end_date, datetime.max.time())
        else:
            start_of_week, end_of_week = calculate_week_range(start_date)

        trace(f"Processando dados de {start_of_week.strftime('%Y-%m-%d %H:%M:%S')} a {end_of_week.strftime('%Y-%m-%d %H:%M:%S')}")

        # Obter dados do banco principal
        dashboard_df = sql_connection.execute_stored_procedure_df(
            "sp_VehicleAccessReport",
            [start_of_week.strftime('%Y-%m-%d %H:%M:%S'), end_of_week.strftime('%Y-%m-%d %H:%M:%S')]
        )

        if dashboard_df is None or dashboard_df.empty:
            trace("Nenhum dado retornado pela stored procedure.", color="yellow")
            return {"status": "success", "records_inserted": 0, "message": "Nenhum dado disponível para o período"}

        # print(dashboard_df)
        trace(f"Dados retornados da stored procedure: {len(dashboard_df)} registros")

        # Preparar dados para inserção
        week_number = start_of_week.isocalendar()[1]
        year = start_of_week.year
        start_date_str = start_of_week.strftime('%Y-%m-%d')
        end_date_str = end_of_week.strftime('%Y-%m-%d')

        # Processar cada linha dos dados retornados
        records_to_process = []
        for _, row in dashboard_df.iterrows():
            # Normalizar dados
            client_name = str(row.get('Vehicle', 'Unknown')).strip()
            classification = str(row.get('EJA', 'Unknown')).strip()

            # Converter StayTime (HH:MM) para total de minutos
            stay_time_value = row.get('StayTime')
            minutes = convert_time_to_minutes(stay_time_value)
            # print(f"DEBUG: Cliente {client_name}, StayTime: {stay_time_value}, Minutos: {minutes}")

            entry_time = normalize_datetime_string(row.get('VehicleEntranceTime'))
            exit_time = normalize_datetime_string(row.get('VehicleExitTime'))

            # Criar chave única para detectar duplicatas
            unique_key = create_unique_key(client_name, entry_time, exit_time)

            records_to_process.append({
                'unique_key': unique_key,
                'week_number': week_number,
                'year': year,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'client_name': client_name,
                'classification': classification,
                'hours': minutes,  # Agora são minutos totais
                'entry_time': entry_time if entry_time else "00:00",
                'exit_time': exit_time if exit_time else ""
            })

        trace(f"Registros processados: {len(records_to_process)}")

        # Obter registros existentes no período para evitar duplicatas
        with closing(db_handler.conn.cursor()) as cursor:
            cursor.execute("BEGIN TRANSACTION")

            try:
                # Buscar registros existentes que se sobrepõem ao período
                cursor.execute("""
                    SELECT client_name, entry_time, exit_time
                    FROM clients_usage
                    WHERE (start_date <= ? AND end_date >= ?) 
                       OR (start_date <= ? AND end_date >= ?)
                       OR (start_date >= ? AND end_date <= ?)
                """, (end_date_str, start_date_str, end_date_str, end_date_str, start_date_str, end_date_str))

                existing_records = cursor.fetchall()

                # Criar set de chaves existentes para comparação rápida
                existing_keys = set()
                for record in existing_records:
                    existing_key = create_unique_key(
                        record[0],  # client_name
                        record[1],  # entry_time
                        record[2]   # exit_time
                    )
                    existing_keys.add(existing_key)

                trace(f"Registros existentes no período: {len(existing_keys)}")

                # Filtrar apenas registros novos
                new_records = []
                duplicates_found = 0

                for record in records_to_process:
                    if record['unique_key'] not in existing_keys:
                        new_records.append(record)
                    else:
                        duplicates_found += 1

                # print(new_records[:5])
                trace(f"Novos registros para inserir: {len(new_records)}")
                trace(f"Duplicatas encontradas e ignoradas: {duplicates_found}")

                # Inserir novos registros
                inserted_count = 0
                if new_records:
                    for record in new_records:
                        try:
                            cursor.execute("""
                                INSERT INTO clients_usage
                                (week_number, year, start_date, end_date, client_name, classification, hours, entry_time, exit_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                record['week_number'],
                                record['year'],
                                record['start_date'],
                                record['end_date'],
                                record['client_name'],
                                record['classification'],
                                record['hours'],
                                record['entry_time'],
                                record['exit_time']
                            ))
                            inserted_count += 1
                        except Exception as e:
                            trace(f"Erro ao inserir registro {record['client_name']}: {str(e)}", color="yellow")
                            continue

                db_handler.conn.commit()

                result_message = f"Processamento concluído. Inseridos: {inserted_count}, Duplicatas ignoradas: {duplicates_found}"
                trace(result_message, color="green")

                return {
                    "status": "success",
                    "records_inserted": inserted_count,
                    "duplicates_ignored": duplicates_found,
                    "total_processed": len(records_to_process),
                    "message": result_message
                }

            except Exception as e:
                db_handler.conn.rollback()
                raise e

    except Exception as e:
        if 'db_handler' in locals() and hasattr(db_handler, 'conn'):
            db_handler.conn.rollback()
        report_exception(e)
        trace(f"Erro ao processar dados: {str(e)}", color="red")
        return {"error": str(e)}


def setup_scheduler():
    """
    Configura o agendador para ser executado dentro de outra aplicação.
    Args:
        run_immediately (bool): Se True, executa o processamento imediatamente
    Returns:
        schedule.Job: O job agendado
    """
    import schedule
    import threading

    # # Agendar para todas as segundas-feiras às 00:15
    # schedule.every().day.at("00:15").do(process_weekly_data, [])
    # trace("Agendamento configurado: Processamento de dados de cliente todos os dias às 00:15", color="green")

    # # Iniciar thread para verificar agendamentos pendentes
    # def run_scheduler():
    #     while True:
    #         schedule.run_pending()
    #         time.sleep(60) # Verifica a cada minuto


def run_weekly_processing():
    try:
        option = '2'

        if option == "1":
            print("Processando semana atual...")
            result = process_weekly_data()

        elif option == "2":
            print("Digite as datas no formato YYYY-MM-DD")
            start_str = '2024-08-12'
            end_str = '2025-09-05'

            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

            print(f"Processando período de {start_date} a {end_date}...")
            result = process_weekly_data(start_date, end_date)

        elif option == "3":
            from datetime import date, timedelta
            end_date = date.today() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)

            print(f"Processando última semana: {start_date} a {end_date}...")
            result = process_weekly_data(start_date, end_date)

        else:
            print("Opção inválida!")
            return

        # Mostrar resultado
        print("\n=== RESULTADO ===")
        if "error" in result:
            print(f"Erro: {result['error']}")
        else:
            print(f"Status: {result['status']}")
            print(f"Registros inseridos: {result.get('records_inserted', 0)}")
            print(f"Duplicatas ignoradas: {result.get('duplicates_ignored', 0)}")
            print(f"Total processado: {result.get('total_processed', 0)}")
            if 'message' in result:
                print(f"Mensagem: {result['message']}")

    except KeyboardInterrupt:
        print("\n\nProcessamento cancelado pelo usuário.")
    except Exception as e:
        print(f"\nErro inesperado: {str(e)}")


if __name__ == "__main__":
    run_weekly_processing()
