# Salvar como diagnostics_sp.py
# Script para diagnosticar problemas com stored procedures

import pyodbc
import configparser
import os
import pandas as pd
import time
from datetime import datetime


def get_connection_string():
    """Obtém a string de conexão a partir do arquivo de configuração"""
    parser = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "db_connection.cfg")
    parser.read(config_path)

    server = parser.get("config", "WAccessBDServer")
    database = parser.get("config", "WAccessDB")
    username = 'sa'
    password = '#w_access_Adm#'

    connection_string = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Connection Timeout=30;"
    )

    return connection_string


def get_active_sessions():
    """Retorna informações sobre as sessões ativas no SQL Server"""
    conn = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()

    # Query para obter informações sobre sessões ativas
    query = """
    SELECT 
        s.session_id, 
        s.login_name, 
        s.host_name, 
        s.program_name,
        DB_NAME(s.database_id) AS database_name,
        s.status,
        s.cpu_time,
        s.memory_usage,
        s.total_elapsed_time / 1000.0 AS elapsed_time_sec,
        t.text AS sql_command,
        s.last_request_start_time,
        s.last_request_end_time,
        s.reads,
        s.writes,
        s.logical_reads,
        CASE WHEN r.blocking_session_id > 0 THEN r.blocking_session_id ELSE NULL END AS blocked_by,
        r.wait_type,
        r.wait_time / 1000.0 AS wait_time_sec,
        r.wait_resource,
        r.command
    FROM 
        sys.dm_exec_sessions s
    LEFT JOIN 
        sys.dm_exec_requests r ON s.session_id = r.session_id
    OUTER APPLY 
        sys.dm_exec_sql_text(r.sql_handle) t
    WHERE 
        s.is_user_process = 1
        AND s.session_id <> @@SPID  -- Excluir a sessão atual
    ORDER BY 
        s.session_id
    """

    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Erro ao consultar sessões ativas: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()


def test_stored_procedure(procedure_name, params=None, timeout=60):
    """Testa a execução de uma stored procedure com monitoramento"""
    conn = pyodbc.connect(get_connection_string())

    # Configurar timeout da conexão
    conn.timeout = timeout

    # Configurar o comportamento de cursores para buscar em lotes
    cursor = conn.cursor()

    try:
        print(f"\n{'-'*80}")
        print(f"Iniciando teste da SP '{procedure_name}' em {datetime.now()}")
        print(f"{'-'*80}\n")

        # Construir a string de chamada da stored procedure
        param_str = ""
        if params:
            param_placeholders = ', '.join(['?'] * len(params))
            sp_script = f"EXEC {procedure_name} {param_placeholders}"
            param_str = str(params)
        else:
            sp_script = f"EXEC {procedure_name}"

        print(f"Executando: {sp_script}")
        if params:
            print(f"Parâmetros: {param_str}")

        # Iniciar temporizador
        start_time = time.time()

        # Iniciar uma thread para monitorar conexões enquanto a SP executa
        import threading
        monitoring = True

        def monitor_connections():
            monitor_count = 0
            while monitoring:
                if monitor_count % 5 == 0:  # A cada 5 segundos
                    print(f"\n--- Monitoramento de conexões ({int(time.time() - start_time)}s) ---")
                    sessions = get_active_sessions()

                    if not sessions.empty:
                        # Filtrar apenas sessões executando algo
                        active = sessions[sessions['sql_command'].notna()]

                        if not active.empty:
                            print(f"Sessões ativas: {len(active)}")

                            # Exibir informações sobre cada sessão ativa
                            for _, row in active.iterrows():
                                print(f"Sessão {row['session_id']} - Status: {row['status']} - Tempo: {row['elapsed_time_sec']:.1f}s")
                                print(f"  Comando: {row['command']}")
                                if row['blocked_by']:
                                    print(f"  Bloqueada por: {row['blocked_by']}")
                                if row['wait_type']:
                                    print(f"  Aguardando: {row['wait_type']} ({row['wait_time_sec']:.1f}s)")
                                if row['wait_resource']:
                                    print(f"  Recurso: {row['wait_resource']}")
                        else:
                            print("Nenhuma sessão executando comandos SQL")
                    else:
                        print("Não foi possível obter informações sobre sessões")

                monitor_count += 1
                time.sleep(1)

        # Iniciar thread de monitoramento
        monitor_thread = threading.Thread(target=monitor_connections)
        monitor_thread.daemon = True
        monitor_thread.start()

        try:
            # Executar a stored procedure
            if params:
                cursor.execute(sp_script, params)
            else:
                cursor.execute(sp_script)

            # Verificar se há resultados
            if cursor.description:
                # Obter nomes das colunas
                columns = [column[0] for column in cursor.description]

                # Buscar resultados em lotes
                batch_size = 1000
                all_results = []
                count = 0

                while True:
                    batch = cursor.fetchmany(batch_size)
                    if not batch:
                        break

                    all_results.extend(batch)
                    count += len(batch)

                    # Reportar progresso a cada 5000 registros
                    if count % 5000 == 0:
                        elapsed = time.time() - start_time
                        print(f"Processados {count} registros em {elapsed:.2f}s ({count/elapsed:.1f} registros/s)")

                # Criar DataFrame com os resultados
                if all_results:
                    df = pd.DataFrame.from_records(all_results, columns=columns)
                    elapsed_time = time.time() - start_time

                    print(f"\n{'-'*80}")
                    print(f"Execução concluída em {elapsed_time:.2f}s")
                    print(f"Retornados {len(df)} registros com {len(df.columns)} colunas")
                    print(f"Tipos de dados: {df.dtypes}")
                    print(f"Tamanho em memória: {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
                    print(f"{'-'*80}\n")

                    return df
                else:
                    print("Nenhum resultado retornado pela stored procedure")
                    return pd.DataFrame(columns=columns)
            else:
                elapsed_time = time.time() - start_time
                print(f"\nExecução concluída em {elapsed_time:.2f}s - Sem conjunto de resultados")
                return None

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"\nERRO após {elapsed_time:.2f}s: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            # Encerrar o monitoramento
            monitoring = False
            monitor_thread.join(timeout=1)

    except Exception as e:
        print(f"Erro ao configurar teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        try:
            conn.close()
            print("Conexão fechada")
        except:
            print("Erro ao fechar conexão")

# Função principal


def main():
    print("Ferramenta de diagnóstico para stored procedures")

    # Perguntar qual stored procedure testar
    sp_name = input("Digite o nome da stored procedure: ")

    # Perguntar se há parâmetros
    has_params = input("A SP possui parâmetros? (s/n): ").lower() == 's'
    params = None

    if has_params:
        # Coletar parâmetros
        params = []
        param_count = int(input("Quantos parâmetros? "))

        for i in range(param_count):
            param_value = input(f"Valor do parâmetro {i+1}: ")
            # Verificar se é uma data
            if '/' in param_value or '-' in param_value:
                try:
                    from dateutil import parser
                    param_value = parser.parse(param_value)
                except Exception:
                    pass
            # Verificar se é um número
            elif param_value.isdigit():
                param_value = int(param_value)
            elif param_value.replace('.', '', 1).isdigit():
                param_value = float(param_value)

            params.append(param_value)

    # Definir timeout
    timeout = int(input("Timeout em segundos (padrão: 60): ") or "60")

    # Executar o teste
    df = test_stored_procedure(sp_name, params, timeout)

    # Perguntar se deseja salvar os resultados
    if df is not None and not df.empty:
        save = input("Deseja salvar os resultados em CSV? (s/n): ").lower() == 's'
        if save:
            filename = f"{sp_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"Resultados salvos em {filename}")


if __name__ == "__main__":
    main()
