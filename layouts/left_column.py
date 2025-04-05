# layouts/left_column.py
from dash import html

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


def create_utilization_availability_column(dfs, ytd_utilization_percentage, ytd_availability_percentage):
    try:
        # Extrair o valor numérico do total de horas
        if isinstance(total_hours, str) and ':' in total_hours:
            horas, minutos = map(int, total_hours.split(':'))
            total_horas_decimal = horas + (minutos / 60.0)
        else:
            total_horas_decimal = safe_convert_to_float(total_hours)

        # Calcular somas para cada categoria
        programas_horas = safe_convert_to_float(dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0)
        outras_equipes_horas = safe_convert_to_float(dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0)
        usuarios_internos_horas = safe_convert_to_float(dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0)
        vendas_externas_horas = safe_convert_to_float(dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0)

        # Calcular percentuais com função segura
        programas_perc_fmt = safe_calculate_percentage(programas_horas, total_horas_decimal)
        outras_equipes_perc_fmt = safe_calculate_percentage(outras_equipes_horas, total_horas_decimal)
        usuarios_internos_perc_fmt = safe_calculate_percentage(usuarios_internos_horas, total_horas_decimal)
        vendas_externas_perc_fmt = safe_calculate_percentage(vendas_externas_horas, total_horas_decimal)

    except Exception as e:
        print(f"Erro ao calcular percentuais: {e}")
        traceback.print_exc()
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
            create_section_header('Utilization (%)', ytd_utilization_percentage),
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
                        create_utilization_graph(dfs['utilization'], height=None)
                    )
                ]
            )
        ], margin_bottom='2px'),

        # Seção de Disponibilidade de Tracks (%)
        create_section_container([
            create_section_header('Tracks Availability (%)', ytd_availability_percentage),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'availability-graph',
                        create_availability_graph(dfs['availability'], height=None)
                    )
                ]
            )
        ], margin_bottom='2px')
    ]
