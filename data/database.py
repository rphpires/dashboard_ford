# data/database.py
# Funções para conexão com banco de dados SQL Server
from data.simplified_processor import get_simplified_processor, get_clients_historical_processor
from utils.tracer import *
from data.db_connection import DatabaseReader
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from dateutil import relativedelta
from data.simplified_processor import get_simplified_processor, get_clients_historical_processor


sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class ReportGenerator:
    def __init__(self, dashboard_df=None, db_handler=None):
        """
        Inicializa o gerador de relatórios.

        Args:
            dashboard_df (DataFrame, opcional): DataFrame com os dados do dashboard
            eja_df (DataFrame, opcional): DataFrame com os dados de EJA
            dashboard_file (str, opcional): Caminho para o arquivo dashboard_ford.csv
            eja_file (str, opcional): Caminho para o arquivo eja_simplificado.csv
        """
        # Armazenar referência para o DataFrame do dashboard
        self.dashboard_df = dashboard_df

        # Obter o gerenciador de banco local
        if db_handler is None:
            from data.local_db_handler import get_db_handler
            self.db_handler = get_db_handler()
        else:
            self.db_handler = db_handler

    def _preparar_dataframes(self):
        """Prepara os DataFrames para processamento, convertendo tipos de dados."""
        # Garantir tipos numéricos para as colunas de códigos
        self.eja_df['EJA CODE'] = pd.to_numeric(self.eja_df['EJA CODE'], errors='coerce')
        self.dashboard_df['EJA'] = pd.to_numeric(self.dashboard_df['EJA'], errors='coerce')

    @staticmethod
    def converter_tempo_para_horas(tempo_str):
        """Converte uma string de tempo no formato HH:MM para horas decimais."""
        try:
            if pd.isna(tempo_str) or tempo_str == "":
                return 0.0

            horas, minutos = map(int, tempo_str.split(':'))
            return horas + (minutos / 60.0)
        except Exception as e:
            print(f"Erro ao converter tempo: {e}")
            return 0.0

    def format_datetime(self, total_horas):
        # Converter para o formato HH:MM
        horas_inteiras = int(total_horas)  # Parte inteira das horas
        minutos = int((total_horas - horas_inteiras) * 60)  # Parte decimal convertida para minutos

        # Formatar como HH:MM
        return f"{horas_inteiras:02d}:{minutos:02d}"

    def gerar_relatorio_eja(self, classificacao, top_n=7):
        if self.dashboard_df is None:
            return {"error": "DataFrame do dashboard não inicializado"}

        dashboard_copy = self.dashboard_df.copy()
        dashboard_copy['HorasDecimais'] = dashboard_copy['StayTime'].apply(self.converter_tempo_para_horas)

        # Converter para float para garantir a compatibilidade de tipos
        total_horas_geral = float(dashboard_copy['HorasDecimais'].sum())

        # print(f"Tipo de dados da coluna EJA: {dashboard_copy['EJA'].dtype}")
        # print("Primeiros 5 valores da coluna EJA:")
        # print(dashboard_copy['EJA'].head(5))
        # print("Exemplos de tipos de itens individuais na coluna EJA:")
        # for i, item in enumerate(dashboard_copy['EJA'].head(5)):
        #     print(f"  Item {i}: {item} (tipo: {type(item)})")

        # Consultar os EJAs do banco SQLite pela classificação
        try:
            # Obter os EJA codes para a classificação especificada
            self.db_handler.cursor.execute(
                "SELECT id, eja_code, title FROM eja WHERE new_classification = ?",
                (classificacao,)
            )
            eja_records = self.db_handler.cursor.fetchall()

            if not eja_records:
                return {"error": f"Nenhum registro encontrado com a classificação '{classificacao}'"}

            # Criar um dicionário para mapear código EJA para título
            eja_titles = {str(row['eja_code']): row['title'] for row in eja_records}

            # Lista de EJA codes que pertencem à classificação desejada
            eja_codes_da_classificacao = list(eja_titles.keys())

            print(dashboard_copy['EJA'])
            # Filtrar registros do dashboard que têm EJA correspondente na classificação
            # dashboard_filtrado = dashboard_copy[dashboard_copy['EJA'].isin(eja_codes_da_classificacao)].copy()
            dashboard_copy['EJA_str'] = dashboard_copy['EJA'].astype(str)
            dashboard_filtrado = dashboard_copy[dashboard_copy['EJA_str'].isin(eja_codes_da_classificacao)].copy()
            if len(dashboard_filtrado) == 0:
                # Verificar se há EJAs dessa classificação no dashboard mas não cadastrados
                all_ejas_in_dashboard = set(dashboard_copy['EJA_str'].unique())
                registered_ejas = set(eja_codes_da_classificacao)

                # EJAs não cadastrados que poderiam pertencer a esta classificação
                unregistered_ejas = all_ejas_in_dashboard - registered_ejas

                error_msg = f"Nenhum registro no dashboard corresponde à classificação '{classificacao}'"
                if unregistered_ejas:
                    error_msg += f". EJAs não cadastrados encontrados: {', '.join(sorted(unregistered_ejas))}"

                return {"error": error_msg}

            # Agrupar por EJA e somar as horas
            # horas_por_eja = dashboard_filtrado.groupby('EJA')['HorasDecimais'].sum().reset_index()
            horas_por_eja = dashboard_filtrado.groupby('EJA_str')['HorasDecimais'].sum().reset_index()
            horas_por_eja = horas_por_eja.rename(columns={'EJA_str': 'EJA'})

            # Ordenar por horas (decrescente)
            horas_por_eja = horas_por_eja.sort_values('HorasDecimais', ascending=False)

            # Calcular o total de horas
            total_horas = self.format_datetime(horas_por_eja['HorasDecimais'].sum())
            _total_horas = float(horas_por_eja['HorasDecimais'].sum())

            # Pegar os top_n itens com mais horas
            top_itens = horas_por_eja.head(top_n)

            # Calcular a porcentagem em relação ao total
            porcentagem = (_total_horas / total_horas_geral) * 100 if total_horas_geral > 0 else 0

            # Criar lista de resultados com título do EJA
            resultado_top = []
            for _, row in top_itens.iterrows():
                eja_code = row['EJA']
                # Obter o título do dicionário criado anteriormente
                titulo = eja_titles.get(eja_code, "Título não encontrado")

                resultado_top.append({
                    "EJA_CODE": int(eja_code) if pd.notna(eja_code) else None,
                    "TITLE": titulo,
                    "HORAS": self.format_datetime(row['HorasDecimais']),
                    "HORAS_DECIMAL": row['HorasDecimais']
                })

            # Montar o resultado final
            resultado = {
                "classificacao": classificacao,
                "total_horas": total_horas,
                "total_horas_decimal": _total_horas,
                "porcentagem": f"{porcentagem:.1f}%",
                "porcentagem_decimal": porcentagem,
                "top_itens": resultado_top
            }

            return resultado

        except Exception as e:
            print(f"Erro ao gerar relatório EJA: {str(e)}")
            return {"error": f"Erro ao processar dados: {str(e)}"}

    def gerar_relatorio_tracks(self, top_n=6):
        try:
            dashboard_copy = self.dashboard_df.copy()

            # Verificar se há dados disponíveis
            if dashboard_copy is None or dashboard_copy.empty or 'StayTime' not in dashboard_copy.columns:
                return {}  # Retornar dicionário vazio se não houver dados

            dashboard_copy['HorasDecimais'] = dashboard_copy['StayTime'].apply(self.converter_tempo_para_horas)

            # Verificar se há horas registradas
            if dashboard_copy['HorasDecimais'].sum() == 0:
                return {}  # Retornar dicionário vazio se o total de horas for zero

            # Agrupar por LocalityName e somar as horas
            tracks_horas = dashboard_copy.groupby('LocalityName')['HorasDecimais'].sum().to_dict()

            # Verificar se há registros válidos
            if not tracks_horas:
                return {}

            tracks_horas_ordenado = dict(sorted(tracks_horas.items(), key=lambda item: item[1], reverse=True))

            for key, item in tracks_horas_ordenado.items():
                formated_dte = self.format_datetime(item)
                tracks_horas_ordenado[key] = formated_dte

            return tracks_horas_ordenado

        except Exception:
            print('Error converting tracks')
            return {}  # Retornar dicionário vazio em caso de erro


def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados SQL Server.
    """
    try:
        return DatabaseReader()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def load_real_data(start_date=None, end_date=None):
    try:
        # Obter conexão com o banco
        sql = get_db_connection()

        if not sql:
            print("Erro ao conectar ao banco de dados. Usando dados simulados.")

        # Definir período de consulta
        if start_date is None or end_date is None:
            # Se não foram fornecidas datas, usar o mês atual
            current_date = dt.now()
            year = current_date.year
            month = current_date.month

            # Primeiro dia do mês atual
            start_date = f'{year}-{month:02d}-01 00:00:00.000'

            # Calcular o último dia do mês atual
            if month == 12:
                next_month_year = year + 1
                next_month = 1
            else:
                next_month_year = year
                next_month = month + 1

            end_date = f'{next_month_year}-{next_month:02d}-01 00:00:00.000'

            # Voltar um dia (último dia do mês atual)
            end_date_obj = dt.strptime(end_date, '%Y-%m-%d %H:%M:%S.%f')
            end_date_obj = end_date_obj - timedelta(days=1)
            end_date = end_date_obj.strftime('%Y-%m-%d 23:59:59.999')

        # Obter dados do banco
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport", [start_date, end_date])

        if dashboard_df is None or dashboard_df.empty:
            print("Não foi possível obter dados do banco. Usando dados simulados.")
            return {}, {}, {}, {}
        # Instanciar o gerador de relatórios
        report_gen = ReportGenerator(dashboard_df=dashboard_df)

        # Gerar relatórios para cada classificação
        programs_data = report_gen.gerar_relatorio_eja("PROGRAMS")
        other_skills_data = report_gen.gerar_relatorio_eja("OTHER SKILL TEAMS")
        internal_users_data = report_gen.gerar_relatorio_eja("INTERNAL USERS")
        external_sales_data = report_gen.gerar_relatorio_eja("EXTERNAL SALES")

        # Processar dados para compatibilidade com o dashboard
        processed_data = process_real_data_for_dashboard(dashboard_df, report_gen,
                                                         programs_data, other_skills_data,
                                                         internal_users_data, external_sales_data)

        report_tracks = report_gen.gerar_relatorio_tracks()
        area_data = process_areas_data(dashboard_df)
        # clients_utilization = process_clients_data(start_date, end_date)

        # Calcular horas totais
        dashboard_df['HorasDecimais'] = dashboard_df['StayTime'].apply(report_gen.converter_tempo_para_horas)
        total_horas = report_gen.format_datetime(dashboard_df['HorasDecimais'].sum())

        # Extrair mês e ano das datas para exibição
        try:
            display_date = dt.strptime(start_date.split()[0], '%Y-%m-%d')
            display_month = display_date.strftime('%B').upper()
            display_day = display_date.strftime('%d')
        except Exception:
            current_date = dt.now()
            display_month = current_date.strftime('%B').upper()
            display_day = current_date.strftime('%d')

        metrics_data = {
            'current_month': display_month,
            'current_day': display_day,
            'total_hours': total_horas,
            'total_hours_ytd': total_horas,  # Por enquanto, igual ao total do mês
            'ytd_utilization_percentage': '82.5%',  # Placeholder
            'ytd_availability_percentage': '88.2%',  # Placeholder
            'selected_date': start_date.split()[0] if isinstance(start_date, str) else None
        }

        return processed_data, report_tracks, area_data, metrics_data

    except Exception as e:
        print(f"Erro ao carregar dados reais: {e}")
        return {}, {}, {}, {}


def get_available_months(limit=20):
    """
    Retorna uma lista dos últimos 20 meses cronologicamente.

    Args:
        limit (int): Número máximo de meses a retornar

    Returns:
        list: Lista de dicionários com informações dos meses disponíveis
    """
    # Gerar uma lista dos últimos 'limit' meses a partir do mês atual
    current_date = dt.now()
    months = []

    for i in range(limit):
        # Calcular o mês i meses atrás
        year = current_date.year
        month = current_date.month - i

        # Ajustar o ano se necessário
        while month <= 0:
            year -= 1
            month += 12

        # Criar objeto de data para formatação
        date_obj = dt(year, month, 1)

        # Calcular o último dia do mês
        if month == 12:
            next_month_year = year + 1
            next_month = 1
        else:
            next_month_year = year
            next_month = month + 1

        next_month_date = dt(next_month_year, next_month, 1)
        last_day = (next_month_date - timedelta(days=1)).day

        # Formato para exibição
        display_text = date_obj.strftime('%B %Y').upper()

        # Formato para valor
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"

        months.append({
            'display': display_text,
            'value': f"{start_date}|{end_date}",
            'year': year,
            'month': month
        })

    return months


def process_real_data_for_dashboard(dashboard_df, report_gen, programs_data, other_skills_data, internal_users_data, external_sales_data):
    """
    Processa os dados reais para o formato esperado pelo dashboard
    """
    # Importar dados simulados para manter a estrutura adequada
    mock_dfs, _, _, _ = create_empty_data_structure()

    # Processar dados para o dashboard
    processed_data = {}
    # Copiar a estrutura base dos dados simulados
    for key in mock_dfs:
        processed_data[key] = mock_dfs[key].copy() if hasattr(mock_dfs[key], 'copy') else mock_dfs[key]

    # Processar dados de programas
    if 'error' not in programs_data:
        programs_df = pd.DataFrame(programs_data['top_itens'])
        if not programs_df.empty:
            programs_df['program'] = programs_df['TITLE']
            programs_df['hours'] = programs_df['HORAS_DECIMAL'].astype(int)
            processed_data['programs'] = programs_df[['program', 'hours']].sort_values('hours', ascending=False)

    # Processar dados de outras equipes
    if 'error' not in other_skills_data:
        other_skills_df = pd.DataFrame(other_skills_data['top_itens'])
        if not other_skills_df.empty:
            other_skills_df['team'] = other_skills_df['TITLE']
            other_skills_df['hours'] = other_skills_df['HORAS_DECIMAL'].astype(int)
            processed_data['other_skills'] = other_skills_df[['team', 'hours']].sort_values('hours', ascending=False)

    # Processar dados de usuários internos
    if 'error' not in internal_users_data:
        internal_users_df = pd.DataFrame(internal_users_data['top_itens'])
        if not internal_users_df.empty:
            internal_users_df['department'] = internal_users_df['TITLE']
            internal_users_df['hours'] = internal_users_df['HORAS_DECIMAL'].astype(int)
            processed_data['internal_users'] = internal_users_df[['department', 'hours']].sort_values('hours', ascending=False)

    # Processar dados de vendas externas
    if 'error' not in external_sales_data:
        external_sales_df = pd.DataFrame(external_sales_data['top_itens'])
        if not external_sales_df.empty:
            external_sales_df['company'] = external_sales_df['TITLE']
            external_sales_df['hours'] = external_sales_df['HORAS_DECIMAL'].astype(int)
            processed_data['external_sales'] = external_sales_df[['company', 'hours']].sort_values('hours', ascending=False)

    return processed_data


def load_dashboard_data(start_date=None, end_date=None):
    """
    Versão corrigida que garante que os dados de clientes sejam carregados
    """
    try:
        sql = get_db_connection()

        if not sql:
            trace("Erro ao conectar ao banco de dados", color="red")
            return create_empty_data_structure()

        # Formatar datas para a stored procedure
        start_date_formatted = f"{start_date} 00:00:00.000"
        end_date_formatted = f"{end_date} 23:59:59.999"

        # Obter dados da SP
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport",
                                                       [start_date_formatted, end_date_formatted])

        if dashboard_df is None or dashboard_df.empty:
            trace("Nenhum dado retornado pela SP", color="yellow")
            return create_empty_data_structure()

        # Usar o processador simplificado
        from data.simplified_processor import get_simplified_processor
        processor = get_simplified_processor(dashboard_df)
        dfs, tracks_data, areas_data_df, periodo_info = processor.get_all_dashboard_data()

        print("=== DEBUG: Iniciando carregamento de dados historicos ===")
        try:
            from data.local_db_handler import get_db_handler
            print("Handler do banco local obtido com sucesso")
            
            db_handler = get_db_handler()
            
            query = """
                SELECT 
                    e.new_classification as classification,
                    SUM(c.hours) as total_minutes
                FROM clients_usage c
                INNER JOIN eja e ON c.classification = e.eja_code
                WHERE e.new_classification IS NOT NULL 
                AND e.new_classification != ''
                GROUP BY e.new_classification
                ORDER BY total_minutes DESC
            """
            
            print("Executando query no banco local...")
            cursor = db_handler.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            print(f"Query executada. Retornou {len(rows)} linhas")
            
            if rows:
                clients_data = []
                for row in rows:
                    classification = row[0]
                    total_minutes = row[1]
                    hours = total_minutes / 60.0
                    
                    print(f"  Processando: {classification} = {hours:.1f} horas")
                    
                    clients_data.append({
                        'classification': classification,
                        'hours': hours
                    })
                
                import pandas as pd
                dfs['customers_ytd'] = pd.DataFrame(clients_data)
                print(f"DataFrame customers_ytd criado com {len(dfs['customers_ytd'])} registros")
                print("Dados historicos carregados com sucesso")
            else:
                print("AVISO: Nenhuma linha retornada pela query")
                dfs['customers_ytd'] = pd.DataFrame(columns=['classification', 'hours'])

        except Exception as e:
            print(f"ERRO ao carregar dados historicos: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            import pandas as pd
            dfs['customers_ytd'] = pd.DataFrame(columns=['classification', 'hours'])

        print("=== DEBUG: Fim do carregamento de dados historicos ===")

        # Adicionar informações do período
        try:
            from datetime import datetime
            display_date = datetime.strptime(start_date, '%Y-%m-%d')
            periodo_info.update({
                'display_month': display_date.strftime('%B').upper(),
                'display_day': display_date.strftime('%d')
            })
        except Exception:
            periodo_info.update({
                'display_month': 'UNKNOWN',
                'display_day': '01'
            })

        return dfs, tracks_data, areas_data_df, periodo_info

    except Exception as e:
        trace(f"Erro no carregamento: {e}", color="red")
        return create_empty_data_structure()


def create_empty_data_structure():
    from .mock_data import get_all_dataframes
    empty_dfs, tracks_data, areas_data_df, periodo_info = get_all_dataframes()

    # Zerar todos os valores nos DataFrames
    for key in empty_dfs:
        if hasattr(empty_dfs[key], 'copy'):
            df = empty_dfs[key].copy()
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = 0
            empty_dfs[key] = df

    # Zerar valores em tracks e areas
    if isinstance(tracks_data, pd.DataFrame) and not tracks_data.empty:
        tracks_data['hours'] = 0
        if 'percentage' in tracks_data.columns:
            tracks_data['percentage'] = '0%'

    if isinstance(areas_data_df, pd.DataFrame) and not areas_data_df.empty:
        areas_data_df['hours'] = 0
        if 'percentage' in areas_data_df.columns:
            areas_data_df['percentage'] = '0%'

    # Atualizar período info para indicar zero horas
    periodo_info['total_hours'] = '0:00'
    periodo_info['total_hours_ytd'] = '0:00'
    periodo_info['ytd_utilization_percentage'] = '0%'
    periodo_info['ytd_availability_percentage'] = '0%'

    return empty_dfs, tracks_data, areas_data_df, periodo_info


def process_areas_data(raw_data):
    # Verificar se o DataFrame tem as colunas necessárias
    if 'VehicleDepartment' not in raw_data.columns or 'StayTime' not in raw_data.columns:
        # Se não tiver, retornar dados simulados para evitar erro
        return pd.DataFrame({
            'area': ['Departamento 1', 'Departamento 2', 'Departamento 3', 'Departamento 4'],
            'hours': [120, 85, 65, 30]
        })

    if 'StayTime' in raw_data.columns:
        # Verifique o tipo/formato de StayTime
        if pd.api.types.is_string_dtype(raw_data['StayTime']):
            # Se for string no formato HH:MM, converter para horas decimais
            def convert_time(time_str):
                try:
                    hours, minutes = map(int, time_str.split(':'))
                    return hours + (minutes / 60.0)
                except (ValueError, AttributeError):
                    return 0

            raw_data['hours'] = raw_data['StayTime'].apply(convert_time)
        else:
            # Assumindo que está em minutos
            raw_data['hours'] = raw_data['StayTime'] / 60.0

    # Agrupar por VehicleDepartment e somar as horas (mantendo a precisão)
    areas_df = raw_data.groupby('VehicleDepartment')['hours'].sum().reset_index()

    # Armazenar os valores decimais exatos para os cálculos
    areas_df['hours_exact'] = areas_df['hours']

    # Arredondar os valores apenas para a exibição no gráfico
    # Usando np.round() para arredondar para o inteiro mais próximo (não truncando)
    areas_df['hours'] = np.round(areas_df['hours']).astype(int)

    # Renomear colunas para corresponder ao formato esperado pela função de gráfico
    areas_df = areas_df.rename(columns={'VehicleDepartment': 'area'})

    # Ordenar por horas exatas em ordem decrescente (mantém a ordem correta)
    areas_df = areas_df.sort_values('hours_exact', ascending=False)

    # Remover a coluna auxiliar se não for necessária para outros cálculos
    areas_df = areas_df.drop(columns=['hours_exact'])

    return areas_df


def process_clients_data(start_date, end_date):
    """Versão simplificada para clientes - usa SQLite apenas para histórico"""
    try:
        from data.simplified_processor import get_clients_historical_processor

        clients_processor = get_clients_historical_processor()
        historical_data = clients_processor.get_last_12_months_data()

        if historical_data.empty:
            # Retornar estrutura padrão
            return pd.DataFrame({
                'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
                'hours': [0, 0, 0, 0]
            })

        return historical_data

    except Exception as e:
        trace(f"Erro ao processar dados de clientes: {e}", color="red")
        return pd.DataFrame({
            'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
            'hours': [0, 0, 0, 0]
        })


def load_dashboard_data_simplified(start_date=None, end_date=None):
    """
    Versão simplificada que substitui load_dashboard_data()
    Remove camadas desnecessárias de processamento
    """
    try:
        # Obter conexão com o banco
        sql = get_db_connection()

        if not sql:
            trace("Erro ao conectar ao banco de dados. Usando dados vazios.", color="red")
            return create_empty_data_structure()

        # Formatar datas para a stored procedure
        start_date_formatted = f"{start_date} 00:00:00.000"
        end_date_formatted = f"{end_date} 23:59:59.999"

        trace(f"Consultando SP para período: {start_date} até {end_date}")

        # Obter dados da SP
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport",
                                                       [start_date_formatted, end_date_formatted])

        if dashboard_df is None or dashboard_df.empty:
            trace("Nenhum dado retornado pela SP", color="yellow")
            return create_empty_data_structure()

        trace(f"SP retornou {len(dashboard_df)} registros")

        # Usar o processador simplificado
        processor = get_simplified_processor(dashboard_df)
        dfs, tracks_data, areas_data_df, periodo_info = processor.get_all_dashboard_data()

        # Adicionar informações do período
        try:
            display_date = datetime.strptime(start_date, '%Y-%m-%d')
            periodo_info.update({
                'display_month': display_date.strftime('%B').upper(),
                'display_day': display_date.strftime('%d')
            })
        except Exception:
            periodo_info.update({
                'display_month': 'UNKNOWN',
                'display_day': '01'
            })

        trace(f"Processamento concluído. Total de horas: {periodo_info.get('total_hours', '0:00')}")

        return dfs, tracks_data, areas_data_df, periodo_info

    except Exception as e:
        trace(f"Erro no carregamento simplificado: {e}", color="red")
        return create_empty_data_structure()


def process_clients_data_simplified(start_date=None, end_date=None):
    """
    Versão simplificada para dados de clientes (últimos 12 meses)
    Usa SQLite apenas quando necessário
    """
    try:
        clients_processor = get_clients_historical_processor()

        # Verificar se precisamos processar dados históricos
        if clients_processor.needs_historical_processing():
            trace("Dados históricos insuficientes. Processamento necessário.", color="yellow")
            # Aqui você pode optar por:
            # 1. Rodar o processador semanal automaticamente
            # 2. Retornar dados vazios com mensagem
            # 3. Usar dados do mês atual da SP

            # Opção segura: usar dados vazios por enquanto
            return pd.DataFrame({
                'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
                'hours': [0, 0, 0, 0]
            })

        # Obter dados históricos do SQLite
        historical_data = clients_processor.get_last_12_months_data()

        if historical_data.empty:
            trace("Nenhum dado histórico encontrado", color="yellow")
            return pd.DataFrame({
                'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
                'hours': [0, 0, 0, 0]
            })

        return historical_data

    except Exception as e:
        trace(f"Erro ao processar dados de clientes: {e}", color="red")
        return pd.DataFrame({
            'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
            'hours': [0, 0, 0, 0]
        })


# Manter a classe ReportGenerator para compatibilidade, mas simplificada
class ReportGenerator:
    """
    Versão simplificada da classe ReportGenerator
    Mantém apenas métodos essenciais para compatibilidade
    """

    def __init__(self, dashboard_df=None, db_handler=None):
        self.dashboard_df = dashboard_df
        self.db_handler = db_handler
        self.processor = get_simplified_processor(dashboard_df) if dashboard_df is not None else None

    @staticmethod
    def converter_tempo_para_horas(tempo_str):
        """Mantido para compatibilidade com código existente"""
        if pd.isna(tempo_str) or not tempo_str or ':' not in str(tempo_str):
            return 0.0

        try:
            parts = str(tempo_str).split(':')
            if len(parts) != 2:
                return 0.0

            hours = int(parts[0])
            minutes = int(parts[1])
            return hours + (minutes / 60.0)
        except (ValueError, TypeError):
            return 0.0

    def format_datetime(self, total_horas):
        """Mantido para compatibilidade"""
        horas_inteiras = int(total_horas)
        minutos = int((total_horas - horas_inteiras) * 60)
        return f"{horas_inteiras:02d}:{minutos:02d}"

    def gerar_relatorio_eja(self, classificacao, top_n=7):
        """
        Versão simplificada que usa o novo processador
        Mantém compatibilidade com código existente
        """
        if not self.processor:
            return {"error": "Processador não inicializado"}

        try:
            # Mapear classificação para método correto
            method_map = {
                "PROGRAMS": self.processor.get_programs_data,
                "OTHER SKILL TEAMS": self.processor.get_other_skills_data,
                "INTERNAL USERS": self.processor.get_internal_users_data,
                "EXTERNAL SALES": self.processor.get_external_sales_data
            }

            if classificacao not in method_map:
                return {"error": f"Classificação '{classificacao}' não reconhecida"}

            # Obter dados usando o processador simplificado
            df = method_map[classificacao](top_n)

            if df.empty:
                return {"error": f"Nenhum dado encontrado para '{classificacao}'"}

            # Converter para o formato esperado pelo código existente
            total_horas_decimal = df['hours'].sum()
            total_horas_formatted = self.format_datetime(total_horas_decimal)

            # Preparar lista de itens
            top_itens = []
            for _, row in df.iterrows():
                # O nome da coluna varia por tipo
                if 'program' in df.columns:
                    title = row['program']
                elif 'team' in df.columns:
                    title = row['team']
                elif 'department' in df.columns:
                    title = row['department']
                elif 'company' in df.columns:
                    title = row['company']
                else:
                    title = "Unknown"

                top_itens.append({
                    "EJA_CODE": 0,  # Não usado no contexto atual
                    "TITLE": title,
                    "HORAS": self.format_datetime(row['hours']),
                    "HORAS_DECIMAL": float(row['hours'])
                })

            return {
                "classificacao": classificacao,
                "total_horas": total_horas_formatted,
                "total_horas_decimal": total_horas_decimal,
                "porcentagem": "100%",  # Sempre 100% dentro da classificação
                "porcentagem_decimal": 100.0,
                "top_itens": top_itens
            }

        except Exception as e:
            trace(f"Erro no relatório EJA simplificado: {e}", color="red")
            return {"error": str(e)}

    def gerar_relatorio_tracks(self, top_n=6):
        """
        Versão simplificada para tracks
        """
        if not self.processor:
            return {}

        try:
            tracks_data = self.processor.get_tracks_data()

            # Ordenar por tempo (convertendo de volta para comparação)
            sorted_tracks = {}
            for track, info in tracks_data.items():
                time_str = info['track_time']
                # Converter para minutos para ordenação
                if ':' in time_str:
                    hours, minutes = map(int, time_str.split(':'))
                    total_minutes = hours * 60 + minutes
                    sorted_tracks[track] = (total_minutes, info)

            # Ordenar e pegar top N
            sorted_items = sorted(sorted_tracks.items(), key=lambda x: x[1][0], reverse=True)[:top_n]

            # Retornar no formato esperado
            result = {}
            for track, (_, info) in sorted_items:
                result[track] = info['track_time']

            return result

        except Exception as e:
            trace(f"Erro no relatório de tracks: {e}", color="red")
            return {}


if __name__ == '__main__':
    ret = get_available_months()
    print(ret)
