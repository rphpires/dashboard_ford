# data/database.py
# Funções para conexão com banco de dados SQL Server
from utils.tracer import report_exception
from data.db_connection import DatabaseReader
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from dateutil import relativedelta

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
    try:
        # Tenta carregar dados reais com as datas especificadas
        result = load_real_data(start_date, end_date)

        # Verificar se o resultado tem 4 itens
        if isinstance(result, tuple) and len(result) == 4:
            dfs, tracks_data, areas_data_df, periodo_info = result

            # Verificar se há dados reais ou se são apenas estruturas vazias
            has_real_data = False

            # Verificar totais de horas para determinar se há dados reais
            if 'total_hours' in periodo_info and periodo_info['total_hours']:
                hours_str = periodo_info['total_hours']

                # Se for formato HH:MM, converter para decimal
                if ':' in hours_str:
                    hours, minutes = map(int, hours_str.split(':'))
                    total_hours = hours + (minutes / 60.0)
                else:
                    try:
                        total_hours = float(hours_str)
                    except (ValueError, TypeError):
                        total_hours = 0

                has_real_data = total_hours > 0

            if not has_real_data:
                # Manter a estrutura, mas limpar os dados
                empty_dfs, _, _, _ = create_empty_data_structure()

                # Preservar a estrutura, mas zerar os valores
                for key in empty_dfs:
                    if key in dfs and hasattr(dfs[key], 'copy'):
                        # Para DataFrames, manter colunas mas zerar valores numéricos
                        df = dfs[key].copy()
                        for col in df.columns:
                            if pd.api.types.is_numeric_dtype(df[col]):
                                df[col] = 0
                        dfs[key] = df

                # Atualizar período info para indicar zero horas
                periodo_info['total_hours'] = '0:00'
                periodo_info['total_hours_ytd'] = '0:00'
                periodo_info['ytd_utilization_percentage'] = '0%'
                periodo_info['ytd_availability_percentage'] = '0%'

                # Para tracks e áreas
                if isinstance(tracks_data, pd.DataFrame) and not tracks_data.empty:
                    tracks_data['hours'] = 0
                    tracks_data['percentage'] = '0%'

                if isinstance(areas_data_df, pd.DataFrame) and not areas_data_df.empty:
                    areas_data_df['hours'] = 0

            return dfs, tracks_data, areas_data_df, periodo_info
        else:
            print(f"Erro: load_real_data retornou {len(result) if isinstance(result, tuple) else type(result)} valores em vez de 4")
            # Criar estrutura vazia com dados zerados
            return None

    except Exception as e:
        print(f"Erro ao carregar dados reais: {e}")
        # Em caso de falha, usar estrutura vazia
        return None


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
    try:
        # Importar bibliotecas necessárias
        import pandas as pd
        from data.local_db_handler import get_db_handler

        # Obter o handler do banco de dados local
        db_handler = get_db_handler()

        # Obter dados de utilização de clientes do banco SQLite
        clients_df = db_handler.get_client_usage_data()

        if clients_df.empty:
            # Se não houver dados, retornar DataFrame vazio com estrutura esperada
            empty_df = pd.DataFrame({
                'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
                'hours': [0, 0, 0, 0]
            })
            return empty_df

        # Agrupar por classificação e somar as horas
        classification_hours = clients_df.groupby('classification')['total_hours'].sum().reset_index()

        # Renomear colunas para o formato esperado pelo gráfico
        classification_hours = classification_hours.rename(columns={
            'total_hours': 'hours'
        })

        # Ordenar por horas em ordem decrescente
        classification_hours = classification_hours.sort_values('hours', ascending=False)

        # Garantir que todas as classificações principais estejam presentes
        main_classifications = ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES']
        for classification in main_classifications:
            if classification not in classification_hours['classification'].values:
                # Adicionar classificação ausente com valor zero
                classification_hours = pd.concat([
                    classification_hours,
                    pd.DataFrame([{'classification': classification, 'hours': 0}])
                ])

        # Se não houver dados, garantir pelo menos as classificações padrão
        if classification_hours.empty:
            for classification in main_classifications:
                classification_hours = pd.concat([
                    classification_hours,
                    pd.DataFrame([{'classification': classification, 'hours': 0}])
                ])

        # Reordenar após adicionar as classificações faltantes
        classification_hours = classification_hours.sort_values('hours', ascending=False)

        return classification_hours

    except Exception as e:
        print(f"Erro ao processar dados de clientes: {str(e)}")
        # Em caso de erro, retornar DataFrame com estrutura esperada, mas valores zero
        empty_df = pd.DataFrame({
            'classification': ['PROGRAMS', 'OTHER SKILL TEAMS', 'INTERNAL USERS', 'EXTERNAL SALES'],
            'hours': [0, 0, 0, 0]
        })
        return empty_df


if __name__ == '__main__':
    ret = get_available_months()
    print(ret)
