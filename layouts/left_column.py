# layouts/left_column.py
import dash
import traceback
from datetime import datetime, timedelta
import pandas as pd
from utils.tracer import trace, report_exception
from dash import html

from data.local_db_handler import get_db_handler

from utils.helpers import *
from components.sections import (
    create_section_container, create_section_header,
    create_graph_section, create_info_card,
)
from components.graphs import (
    create_utilization_graph, create_availability_graph
)


# Modificar a inicialização para não carregar dados imediatamente
dfs, tracks_data, areas_data_df, periodo_info = None, None, None, None

# Inicializar variáveis globais
current_month = ""
current_day = ""
ytd_utilization_percentage = ""
ytd_availability_percentage = ""
total_hours = ""
total_hours_ytd = ""


# def create_utilization_availability_column(dfs, ytd_utilization_percentage, ytd_availability_percentage):
#     try:
#         # Extrair o valor numérico do total de horas
#         if isinstance(total_hours, str) and ':' in total_hours:
#             horas, minutos = map(int, total_hours.split(':'))
#             total_horas_decimal = horas + (minutos / 60.0)
#         else:
#             total_horas_decimal = safe_convert_to_float(total_hours)

#         # Calcular somas para cada categoria
#         programas_horas = safe_convert_to_float(dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0)
#         outras_equipes_horas = safe_convert_to_float(dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0)
#         usuarios_internos_horas = safe_convert_to_float(dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0)
#         vendas_externas_horas = safe_convert_to_float(dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0)

#         # Calcular percentuais com função segura
#         programas_perc_fmt = safe_calculate_percentage(programas_horas, total_horas_decimal)
#         outras_equipes_perc_fmt = safe_calculate_percentage(outras_equipes_horas, total_horas_decimal)
#         usuarios_internos_perc_fmt = safe_calculate_percentage(usuarios_internos_horas, total_horas_decimal)
#         vendas_externas_perc_fmt = safe_calculate_percentage(vendas_externas_horas, total_horas_decimal)

#     except Exception as e:
#         print(f"Erro ao calcular percentuais: {e}")
#         traceback.print_exc()
#         # Valores padrão em caso de erro
#         programas_horas = 89
#         outras_equipes_horas = 130
#         usuarios_internos_horas = 778
#         vendas_externas_horas = 34
#         programas_perc_fmt = "9%"
#         outras_equipes_perc_fmt = "13%"
#         usuarios_internos_perc_fmt = "75%"
#         vendas_externas_perc_fmt = "3%"

#     return [
#         # Seção de Utilização (%)
#         create_section_container([
#             create_section_header('Utilization (%)', ytd_utilization_percentage),
#             html.Div(
#                 className='panel-content',
#                 children=[
#                     # Cards de resumo agrupados
#                     html.Div(
#                         className='flex-container',
#                         style={'marginBottom': '2px'},
#                         children=[
#                             create_info_card('Programs', f"{int(programas_horas)} hr",
#                                              f"{programas_perc_fmt} of total", color='#1E88E5'),
#                             create_info_card('Other Skill Teams', f"{int(outras_equipes_horas)} hr",
#                                              f"{outras_equipes_perc_fmt} of total", color='#673AB7'),
#                             create_info_card('Internal Users', f"{int(usuarios_internos_horas)} hr",
#                                              f"{usuarios_internos_perc_fmt} of total", color='#2E7D32'),
#                             create_info_card('External Sales', f"{int(vendas_externas_horas)} hr",
#                                              f"{vendas_externas_perc_fmt} of total", color='#F57C00')
#                         ]
#                     ),
#                     # Gráfico - sem altura fixa para ajuste automático
#                     create_graph_section(
#                         'utilization-graph',
#                         create_utilization_graph(dfs['utilization'], height=None)
#                     )
#                 ]
#             )
#         ], margin_bottom='2px'),

#         # Seção de Disponibilidade de Tracks (%)
#         create_section_container([
#             create_section_header('Tracks Availability (%)', ytd_availability_percentage),
#             html.Div(
#                 className='panel-content',
#                 children=[
#                     create_graph_section(
#                         'availability-graph',
#                         create_availability_graph(dfs['availability'], height=None)
#                     )
#                 ]
#             )
#         ], margin_bottom='2px')
#     ]


def get_utilization_data():
    """
    Busca os dados de utilização (usage_percentage) do banco de dados
    para exibição no gráfico.

    Returns:
        DataFrame: DataFrame com os dados formatados para o gráfico
    """
    try:
        # Obter conexão com o banco de dados
        db_handler = get_db_handler()

        # Buscar os dados dos últimos 12 meses
        current_date = datetime.now()

        # Gerar lista de todos os meses dos últimos 12 meses
        months_data = []
        for i in range(11, -1, -1):
            # Calcular o mês (partindo do mês atual e indo para trás)
            target_date = current_date - timedelta(days=i * 30)
            year = target_date.year
            month = target_date.month

            # Formato para exibição: "Jan", "Feb", etc.
            month_name = datetime(year, month, 1).strftime('%b')
            # Adicionar o ano se for o primeiro mês do ano ou janeiro
            if month == 1:
                month_display = f"{month_name}-{year}"
            else:
                month_display = month_name

            months_data.append({
                'month': month_display,
                'utilization': 0,  # Valor padrão
                'year': year,
                'month_num': month  # Para correspondência com os dados do banco
            })

        # Consultar os dados de utilização dos últimos 12 meses
        months_ago_12 = current_date - timedelta(days=365)
        year_start = months_ago_12.year
        month_start = months_ago_12.month

        query = """
            SELECT year, month, value
            FROM usage_percentage
            WHERE (year > ? OR (year = ? AND month >= ?))
            ORDER BY year, month
        """

        db_handler.cursor.execute(query, (year_start, year_start, month_start))
        rows = db_handler.cursor.fetchall()

        # Atualizar os meses que têm dados
        for row in rows:
            for month_data in months_data:
                if row['year'] == month_data['year'] and row['month'] == month_data['month_num']:
                    month_data['utilization'] = row['value']
                    break

        # Converter para DataFrame
        df = pd.DataFrame(months_data)

        # Garantir que os meses estejam na ordem cronológica
        df = df.sort_values(by=['year', 'month_num'])

        # Remover colunas auxiliares
        df = df[['month', 'utilization']]

        avg_utilization = 0
        if not df.empty and 'utilization' in df.columns:
            avg_utilization = df['utilization'].mean()

        return df, avg_utilization

    except Exception as e:
        trace(f"Erro ao obter dados de utilização: {e}", color="red")
        print(traceback.format_exc())

        # Em caso de erro, retornar DataFrame vazio com a estrutura esperada
        return pd.DataFrame({
            'month': [],
            'utilization': []
        })


def get_availability_data():
    """
    Busca os dados de disponibilidade (tracks_availability) do banco de dados
    para exibição no gráfico. Inclui todos os meses dos últimos 12 meses com valor 0% 
    para os meses sem registros.

    Returns:
        DataFrame: DataFrame com os dados formatados para o gráfico
    """
    try:
        # Obter conexão com o banco de dados
        db_handler = get_db_handler()

        # Buscar os dados dos últimos 12 meses
        current_date = datetime.now()

        # Gerar lista de todos os meses dos últimos 12 meses
        months_data = []
        for i in range(11, -1, -1):
            # Calcular o mês (partindo do mês atual e indo para trás)
            target_date = current_date - timedelta(days=i * 30)
            year = target_date.year
            month = target_date.month

            # Formato para exibição: "Jan", "Feb", etc.
            month_name = datetime(year, month, 1).strftime('%b')
            # Adicionar o ano se for o primeiro mês do ano ou janeiro
            if month == 1:
                month_display = f"{month_name}-{year}"
            else:
                month_display = month_name

            months_data.append({
                'month': month_display,
                'availability': 0,  # Valor padrão
                'year': year,
                'month_num': month  # Para correspondência com os dados do banco
            })

        # Consultar os dados de disponibilidade dos últimos 12 meses
        months_ago_12 = current_date - timedelta(days=365)
        year_start = months_ago_12.year
        month_start = months_ago_12.month

        query = """
            SELECT year, month, value
            FROM tracks_availability
            WHERE (year > ? OR (year = ? AND month >= ?))
            ORDER BY year, month
        """

        db_handler.cursor.execute(query, (year_start, year_start, month_start))
        rows = db_handler.cursor.fetchall()

        # Atualizar os meses que têm dados
        for row in rows:
            for month_data in months_data:
                if row['year'] == month_data['year'] and row['month'] == month_data['month_num']:
                    month_data['availability'] = row['value']
                    break

        # Converter para DataFrame
        df = pd.DataFrame(months_data)

        # Garantir que os meses estejam na ordem cronológica
        df = df.sort_values(by=['year', 'month_num'])

        # Remover colunas auxiliares
        df = df[['month', 'availability']]

        avg_availability = 0
        if not df.empty and 'availability' in df.columns:
            avg_availability = df['availability'].mean()

        return df, avg_availability

    except Exception as e:
        trace(f"Erro ao obter dados de disponibilidade: {e}", color="red")
        print(traceback.format_exc())

        # Em caso de erro, retornar DataFrame vazio com a estrutura esperada
        return pd.DataFrame({
            'month': [],
            'availability': []
        })


def create_utilization_availability_column(dfs, ytd_utilization_percentage, ytd_availability_percentage):
    """
    Cria o layout da coluna de utilização e disponibilidade com dados reais do banco de dados.
    """
    try:
        # Obter dados de utilização e disponibilidade diretamente do banco
        utilization_df, avg_utilization = get_utilization_data()
        availability_df, avg_availability = get_availability_data()

        utilization_percentage = f"{avg_utilization:.1f}%" if avg_utilization > 0 else "0.0%"
        availability_percentage = f"{avg_availability:.1f}%" if avg_availability > 0 else "0.0%"

        # Registrar informações sobre os dados (para depuração)
        trace(f"Dados de utilização: {len(utilization_df)} registros", color="blue")
        trace(f"Dados de disponibilidade: {len(availability_df)} registros", color="blue")

        # Usar os dados reais para os gráficos ao invés dos dados do dfs
        utilization_graph = create_utilization_graph(utilization_df, height=None)
        availability_graph = create_availability_graph(availability_df, height=None)

        # Extrair o valor numérico do total de horas
        if isinstance(dfs.get('total_hours', ''), str) and ':' in dfs.get('total_hours', ''):
            try:
                horas, minutos = map(int, dfs.get('total_hours', '').split(':'))
                total_horas_decimal = horas + (minutos / 60.0)
            except Exception:
                total_horas_decimal = 0
        else:
            try:
                total_horas_decimal = float(dfs.get('total_hours', 0))
            except Exception:
                total_horas_decimal = 0

        # Calcular somas para cada categoria
        programas_horas = float(dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0)
        outras_equipes_horas = float(dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0)
        usuarios_internos_horas = float(dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0)
        vendas_externas_horas = float(dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0)

        # Calcular percentuais com segurança
        def safe_calculate_percentage(part, total):
            if total > 0:
                return f"{(part / total * 100):.1f}%"
            return "0.0%"

        programas_perc_fmt = safe_calculate_percentage(programas_horas, total_horas_decimal)
        outras_equipes_perc_fmt = safe_calculate_percentage(outras_equipes_horas, total_horas_decimal)
        usuarios_internos_perc_fmt = safe_calculate_percentage(usuarios_internos_horas, total_horas_decimal)
        vendas_externas_perc_fmt = safe_calculate_percentage(vendas_externas_horas, total_horas_decimal)

    except Exception as e:
        trace(f"Erro ao calcular percentuais: {e}", color="red")
        print(traceback.format_exc())

        # Em caso de erro, usar os valores e gráficos anteriores
        utilization_graph = create_utilization_graph(dfs['utilization'], height=None)
        availability_graph = create_availability_graph(dfs['availability'], height=None)

        # Valores padrão em caso de erro
        programas_horas = 89
        outras_equipes_horas = 130
        usuarios_internos_horas = 778
        vendas_externas_horas = 34
        programas_perc_fmt = "9%"
        outras_equipes_perc_fmt = "13%"
        usuarios_internos_perc_fmt = "75%"
        vendas_externas_perc_fmt = "3%"

    return [
        # Seção de Utilização (%)
        create_section_container([
            create_section_header('Utilization (%)', utilization_percentage),
            html.Div(
                className='panel-content',
                children=[
                    # Cards de resumo agrupados
                    html.Div(
                        className='flex-container',
                        style={'marginBottom': '2px'},
                        children=[
                            create_info_card('Programs', f"{int(programas_horas)} hr",
                                             f"{programas_perc_fmt} of total", color='#1E88E5'),
                            create_info_card('Other Skill Teams', f"{int(outras_equipes_horas)} hr",
                                             f"{outras_equipes_perc_fmt} of total", color='#673AB7'),
                            create_info_card('Internal Users', f"{int(usuarios_internos_horas)} hr",
                                             f"{usuarios_internos_perc_fmt} of total", color='#2E7D32'),
                            create_info_card('External Sales', f"{int(vendas_externas_horas)} hr",
                                             f"{vendas_externas_perc_fmt} of total", color='#F57C00')
                        ]
                    ),
                    # Gráfico - sem altura fixa para ajuste automático
                    create_graph_section(
                        'utilization-graph',
                        utilization_graph
                    )
                ]
            )
        ], margin_bottom='2px'),

        # Seção de Disponibilidade de Tracks (%)
        create_section_container([
            create_section_header('Tracks Availability (%)', availability_percentage),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'availability-graph',
                        availability_graph
                    )
                ]
            )
        ], margin_bottom='2px')
    ]
