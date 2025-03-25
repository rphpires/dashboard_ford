# data/database.py
# Funções para conexão com banco de dados SQL Server
from utils.tracer import report_exception
from .db_connection import DatabaseReader
import os
import numpy as np
import pandas as pd
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importe a classe EJAReportGenerator do dash_2.py


class ReportGenerator:
    """
    Classe para gerar relatórios de horas trabalhadas por classificação EJA.
    """

    def __init__(self, dashboard_df=None, eja_df=None, dashboard_file=None, eja_file=None):
        """
        Inicializa o gerador de relatórios.

        Args:
            dashboard_df (DataFrame, opcional): DataFrame com os dados do dashboard
            eja_df (DataFrame, opcional): DataFrame com os dados de EJA
            dashboard_file (str, opcional): Caminho para o arquivo dashboard_ford.csv
            eja_file (str, opcional): Caminho para o arquivo eja_simplificado.csv
        """
        # Se fornecidos DataFrames, usar diretamente
        self.dashboard_df = dashboard_df
        self.eja_df = eja_df

        # Se fornecidos caminhos de arquivo, carregar os DataFrames
        if dashboard_file and not dashboard_df:
            self.dashboard_df = pd.read_csv(dashboard_file, encoding='utf-8')

        if eja_file and not eja_df:
            self.eja_df = pd.read_csv(eja_file, encoding='utf-8')

        # Preparar os DataFrames
        if self.dashboard_df is not None and self.eja_df is not None:
            self._preparar_dataframes()

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
        except Exception as ex:
            report_exception(ex)
            return 0.0

    def format_datetime(self, total_horas):
        # Converter para o formato HH:MM
        horas_inteiras = int(total_horas)  # Parte inteira das horas
        minutos = int((total_horas - horas_inteiras) * 60)  # Parte decimal convertida para minutos

        # Formatar como HH:MM
        return f"{horas_inteiras:02d}:{minutos:02d}"

    def gerar_relatorio_eja(self, classificacao, top_n=7):
        """
        Gera um relatório com as horas por classificação.

        Args:
            classificacao (str): Valor de NEW CLASSIFICATION para filtrar
            top_n (int): Número de itens principais a retornar

        Returns:
            dict: Resultado do processamento
        """
        if self.dashboard_df is None or self.eja_df is None:
            return {"error": "DataFrames não inicializados"}

        dashboard_copy = self.dashboard_df.copy()
        dashboard_copy['HorasDecimais'] = dashboard_copy['StayTime'].apply(self.converter_tempo_para_horas)

        # Converter para float para garantir a compatibilidade de tipos
        total_horas_geral = float(dashboard_copy['HorasDecimais'].sum())

        # Filtrar EJA por classificação
        eja_filtrado = self.eja_df[self.eja_df['CLASSIFICATION'] == classificacao]

        if len(eja_filtrado) == 0:
            return {"error": f"Nenhum registro encontrado com a classificação '{classificacao}'"}

        # Lista de EJA CODEs que pertencem à classificação desejada
        eja_codes_da_classificacao = set(eja_filtrado['CLASSIFICATION'].tolist())

        # Filtrar registros do dashboard que têm EJA correspondente na classificação
        # dashboard_filtrado = self.dashboard_df[self.dashboard_df['EJA'].isin(eja_codes_da_classificacao)]
        dashboard_filtrado = self.dashboard_df[self.dashboard_df['EJA'].isin(eja_codes_da_classificacao)].copy()

        if len(dashboard_filtrado) == 0:
            return {"error": f"Nenhum registro no dashboard corresponde à classificação '{classificacao}'"}

        # Converter a coluna StayTime para horas decimais
        dashboard_filtrado['HorasDecimais'] = dashboard_filtrado['StayTime'].apply(self.converter_tempo_para_horas)

        # Agrupar por EJA e somar as horas
        horas_por_eja = dashboard_filtrado.groupby('EJA')['HorasDecimais'].sum().reset_index()

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
            # Buscar o título correspondente ao EJA CODE
            titulo_encontrado = self.eja_df[self.eja_df['EJA CODE'] == eja_code]['TITLE']
            titulo = titulo_encontrado.iloc[0] if not titulo_encontrado.empty else "Título não encontrado"

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

    def gerar_relatorio_tracks(self, top_n=7):
        try:
            dashboard_copy = self.dashboard_df.copy()
            dashboard_copy['HorasDecimais'] = dashboard_copy['StayTime'].apply(self.converter_tempo_para_horas)

            # Agrupar por LocalityName e somar as horas
            tracks_horas = dashboard_copy.groupby('LocalityName')['HorasDecimais'].sum().to_dict()
            tracks_horas_ordenado = dict(sorted(tracks_horas.items(), key=lambda item: item[1], reverse=True))

            for key, item in tracks_horas_ordenado.items():
                formated_dte = self.format_datetime(item)
                tracks_horas_ordenado[key] = formated_dte

        except Exception:
            print('Error converting tracks')

        return tracks_horas_ordenado


def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados SQL Server.
    """
    try:
        return DatabaseReader()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def load_real_data():
    """
    Carrega dados reais do banco de dados e processa com o EJAReportGenerator
    """
    try:
        # Obter conexão com o banco
        sql = get_db_connection()

        if not sql:
            print("Erro ao conectar ao banco de dados. Usando dados simulados.")
            from .mock_data import get_all_dataframes
            return get_all_dataframes()

        # Definir período de consulta (ajuste conforme necessário)
        start_date = '2024-01-01 00:00:33.220'
        end_date = '2024-01-31 23:59:59.220'

        # Obter dados do banco
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport", [start_date, end_date])

        print(dashboard_df)
        if dashboard_df is None or dashboard_df.empty:
            print("Não foi possível obter dados do banco. Usando dados simulados.")
            from .mock_data import get_all_dataframes
            return get_all_dataframes()

        # Carregar dados de EJA do arquivo auxiliar
        eja_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aux_files", "eja_simplificado.csv")
        if not os.path.exists(eja_path):
            print(f"Arquivo EJA não encontrado em {eja_path}. Usando dados simulados.")
            from .mock_data import get_all_dataframes
            return get_all_dataframes()

        # Instanciar o gerador de relatórios
        report_gen = ReportGenerator(dashboard_df=dashboard_df, eja_file=eja_path)

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

        return processed_data, report_tracks, area_data

    except Exception as e:
        print(f"Erro ao carregar dados reais: {e}")
        from .mock_data import get_all_dataframes
        return get_all_dataframes()


def process_real_data_for_dashboard(dashboard_df, report_gen, programs_data, other_skills_data, internal_users_data, external_sales_data):
    """
    Processa os dados reais para o formato esperado pelo dashboard
    """
    # Importar dados simulados para manter a estrutura adequada
    from .mock_data import get_all_dataframes
    mock_data = get_all_dataframes()

    # Calcular utilização mensal (placeholder - deve ser calculado com dados reais)
    # Esta é uma implementação básica; ajuste conforme necessário

    # Processar dados para o dashboard
    processed_data = mock_data.copy()  # Manter a estrutura base

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


def load_dashboard_data():
    """
    Função principal para carregar todos os dados do dashboard.
    Tenta carregar dados reais e, se falhar, usa os dados simulados.
    """
    try:
        return load_real_data()
    except Exception as e:
        print(f"Erro ao carregar dados reais: {e}")
        # Em caso de falha, usar dados simulados
        from .mock_data import get_all_dataframes
        return get_all_dataframes()


def get_current_period_info():
    """
    Obtém informações do período atual (mês, dia, totais).
    """
    try:
        # Tentar obter dados reais
        sql = get_db_connection()
        if not sql:
            raise Exception("Não foi possível conectar ao banco de dados")

        # Obter dados do dashboard para janeiro de 2024
        start_date = '2024-01-01 00:00:33.220'
        end_date = '2024-01-31 23:59:59.220'
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport", [start_date, end_date])

        if dashboard_df is None or dashboard_df.empty:
            raise Exception("Não foi possível obter dados do banco")

        # Ler dados do EJA
        eja_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aux_files", "eja_simplificado.csv")
        report_gen = ReportGenerator(dashboard_df=dashboard_df, eja_file=eja_path)

        # Calcular horas totais
        dashboard_df['HorasDecimais'] = dashboard_df['StayTime'].apply(report_gen.converter_tempo_para_horas)
        total_horas = report_gen.format_datetime(dashboard_df['HorasDecimais'].sum())

        # Data atual para exibição
        current_date = datetime.now()

        return {
            'current_month': current_date.strftime('%B').upper(),
            'current_day': current_date.strftime('%d'),
            'total_hours': total_horas,
            'total_hours_ytd': total_horas,  # Por enquanto, igual ao total do mês
            'ytd_utilization_percentage': '82.5%',  # Placeholder
            'ytd_availability_percentage': '88.2%'  # Placeholder
        }

    except Exception as e:
        print(f"Erro ao obter informações do período: {e}")
        # Em caso de falha, usar valores padrão
        return {
            'current_month': 'JANUARY',
            'current_day': '24',
            'total_hours': '1032',
            'total_hours_ytd': '10386',
            'ytd_utilization_percentage': '16%',
            'ytd_availability_percentage': '96%'
        }

# Adicionar à data/database.py


def process_areas_data(raw_data):
    """
    Processa os dados brutos da tabela, agrupando por VehicleDepartment e somando StayTime

    Args:
        raw_data (DataFrame): DataFrame com os dados brutos da consulta SQL

    Returns:
        DataFrame: DataFrame processado com colunas 'area' e 'hours'
    """
    import pandas as pd

    # Verificar se o DataFrame tem as colunas necessárias
    if 'VehicleDepartment' not in raw_data.columns or 'StayTime' not in raw_data.columns:
        # Se não tiver, retornar dados simulados para evitar erro
        return pd.DataFrame({
            'area': ['Departamento 1', 'Departamento 2', 'Departamento 3', 'Departamento 4'],
            'hours': [120, 85, 65, 30]
        })

    # Converter StayTime para horas se estiver em outro formato
    # Assumindo que StayTime está em minutos
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
