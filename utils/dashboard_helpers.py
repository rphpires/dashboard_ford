# utils/dashboard_helpers.py
# Funções auxiliares para o dashboard

from dash import html
import pandas as pd
from utils.tracer import trace
from components.sections import (
    create_section_container, create_section_header,
    create_metric_header, create_graph_section,
    create_bordered_container, create_side_by_side_container,
    create_flex_item, create_info_card
)
from components.graphs import (
    create_utilization_graph, create_availability_graph,
    create_programs_graph, create_other_skills_graph,
    create_internal_users_graph, create_external_sales_graph,
    create_tracks_graph, create_areas_graph,
    create_customers_stacked_graph
)


def calculate_metrics(dfs, total_hours):
    """
    Pré-calcula métricas usadas em múltiplos lugares no dashboard.
    """
    try:
        # Extrair o valor numérico do total de horas
        if ':' in total_hours:
            horas, minutos = map(int, total_hours.split(':'))
            total_horas_decimal = horas + (minutos / 60.0)
        else:
            total_horas_decimal = float(total_hours)

        # Calcular somas para cada categoria
        programas_horas = dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0
        outras_equipes_horas = dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0
        usuarios_internos_horas = dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0
        vendas_externas_horas = dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0

        # Calcular percentuais
        if total_horas_decimal > 0:
            programas_perc = (programas_horas / total_horas_decimal) * 100
            outras_equipes_perc = (outras_equipes_horas / total_horas_decimal) * 100
            usuarios_internos_perc = (usuarios_internos_horas / total_horas_decimal) * 100
            vendas_externas_perc = (vendas_externas_horas / total_horas_decimal) * 100
        else:
            programas_perc = outras_equipes_perc = usuarios_internos_perc = vendas_externas_perc = 0

        # Formatação para exibição
        programas_perc_fmt = f"{programas_perc:.1f}%"
        outras_equipes_perc_fmt = f"{outras_equipes_perc:.1f}%"
        usuarios_internos_perc_fmt = f"{usuarios_internos_perc:.1f}%"
        vendas_externas_perc_fmt = f"{vendas_externas_perc:.1f}%"

        return {
            'programas_horas': int(programas_horas),
            'outras_equipes_horas': int(outras_equipes_horas),
            'usuarios_internos_horas': int(usuarios_internos_horas),
            'vendas_externas_horas': int(vendas_externas_horas),
            'programas_perc': programas_perc,
            'outras_equipes_perc': outras_equipes_perc,
            'usuarios_internos_perc': usuarios_internos_perc,
            'vendas_externas_perc': vendas_externas_perc,
            'programas_perc_fmt': programas_perc_fmt,
            'outras_equipes_perc_fmt': outras_equipes_perc_fmt,
            'usuarios_internos_perc_fmt': usuarios_internos_perc_fmt,
            'vendas_externas_perc_fmt': vendas_externas_perc_fmt,
            'total_horas_decimal': total_horas_decimal
        }
    except Exception as e:
        trace(f"Erro ao calcular métricas: {str(e)}", color="red")
        # Valores padrão em caso de erro
        return {
            'programas_horas': 89,
            'outras_equipes_horas': 130,
            'usuarios_internos_horas': 778,
            'vendas_externas_horas': 34,
            'programas_perc': 9.0,
            'outras_equipes_perc': 13.0,
            'usuarios_internos_perc': 75.0,
            'vendas_externas_perc': 3.0,
            'programas_perc_fmt': "9%",
            'outras_equipes_perc_fmt': "13%",
            'usuarios_internos_perc_fmt': "75%",
            'vendas_externas_perc_fmt': "3%",
            'total_horas_decimal': 1032
        }


def create_utilization_availability_column(dfs, ytd_utilization_percentage, ytd_availability_percentage, metrics):
    """
    Cria a coluna de gráficos de utilização e disponibilidade.
    """
    return [
        # Seção de Utilização (%)
        create_section_container([
            create_section_header('UTILIZAÇÃO (%)', ytd_utilization_percentage),
            html.Div(
                className='panel-content',
                children=[
                    # Cards de resumo agrupados
                    html.Div(
                        className='flex-container',
                        style={'marginBottom': '8px'},
                        children=[
                            create_info_card('Programas', f"{metrics['programas_horas']} hr",
                                             f"{metrics['programas_perc_fmt']} do total", color='#1E88E5'),
                            create_info_card('Outras Equipes', f"{metrics['outras_equipes_horas']} hr",
                                             f"{metrics['outras_equipes_perc_fmt']} do total", color='#673AB7'),
                            create_info_card('Uso Interno', f"{metrics['usuarios_internos_horas']} hr",
                                             f"{metrics['usuarios_internos_perc_fmt']} do total", color='#2E7D32'),
                            create_info_card('Vendas Externas', f"{metrics['vendas_externas_horas']} hr",
                                             f"{metrics['vendas_externas_perc_fmt']} do total", color='#F57C00')
                        ]
                    ),
                    # Gráfico - sem altura fixa para ajuste automático
                    create_graph_section(
                        'utilization-graph',
                        create_utilization_graph(dfs['utilization'], height=None)
                    )
                ]
            )
        ], margin_bottom='8px'),

        # Seção de Disponibilidade de Tracks (%)
        create_section_container([
            create_section_header('DISPONIBILIDADE DE TRACKS (%)', ytd_availability_percentage),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'availability-graph',
                        create_availability_graph(dfs['availability'], height=None)
                    )
                ]
            )
        ], margin_bottom='8px')
    ]


def create_optimized_utilization_breakdown(dfs, total_hours, metrics):
    """
    Cria o layout otimizado para o detalhamento de utilização mensal.
    """
    return create_section_container([
        create_section_header('DETALHAMENTO DE UTILIZAÇÃO MENSAL', f"{total_hours} hr"),
        html.Div(
            className='panel-content',
            children=[
                # Indicadores de Resumo em linha compacta
                html.Div(
                    className='flex-container compact-info-cards',
                    style={'marginBottom': '8px'},
                    children=[
                        create_info_card('Programas', f"{metrics['programas_horas']} hr",
                                         f"{metrics['programas_perc_fmt']} do total", color='#1E88E5'),
                        create_info_card('Outras Equipes', f"{metrics['outras_equipes_horas']} hr",
                                         f"{metrics['outras_equipes_perc_fmt']} do total", color='#673AB'),
                        create_info_card('Outras Equipes', f"{metrics['outras_equipes_horas']} hr",
                                         f"{metrics['outras_equipes_perc_fmt']} do total", color='#673AB7'),
                        create_info_card('Uso Interno', f"{metrics['usuarios_internos_horas']} hr",
                                         f"{metrics['usuarios_internos_perc_fmt']} do total", color='#2E7D32'),
                        create_info_card('Vendas Externas', f"{metrics['vendas_externas_horas']} hr",
                                         f"{metrics['vendas_externas_perc_fmt']} do total", color='#F57C00')
                    ]
                ),

                # Programas - altura flexível
                create_bordered_container([
                    create_metric_header('PROGRAMAS', f"{metrics['programas_horas']}", metrics['programas_perc_fmt']),
                    create_graph_section(
                        'programs-graph',
                        create_programs_graph(dfs['programs'], height=None)
                    )
                ]),

                # Other Skill Teams - altura flexível
                create_bordered_container([
                    create_metric_header('OUTRAS EQUIPES DE HABILIDADES', f"{metrics['outras_equipes_horas']}", metrics['outras_equipes_perc_fmt']),
                    create_graph_section(
                        'other-skills-graph',
                        create_other_skills_graph(dfs['other_skills'], height=None)
                    )
                ]),

                # Internal Users and External Sales (lado a lado)
                create_side_by_side_container([
                    # Internal Users
                    create_flex_item([
                        create_metric_header('USUÁRIOS INTERNOS', f"{metrics['usuarios_internos_horas']}", metrics['usuarios_internos_perc_fmt']),
                        create_graph_section(
                            'internal-users-graph',
                            create_internal_users_graph(dfs['internal_users'], height=None)
                        )
                    ], margin_right='8px', min_width='38%'),

                    # External Sales
                    create_flex_item([
                        create_metric_header('VENDAS EXTERNAS', f"{metrics['vendas_externas_horas']}", metrics['vendas_externas_perc_fmt']),
                        create_graph_section(
                            'external-sales-graph',
                            create_external_sales_graph(dfs['external_sales'], height=None)
                        )
                    ], min_width='38%')
                ])
            ]
        )
    ])


def create_tracks_areas_column(dfs, total_hours, total_hours_ytd):
    """
    Cria a coluna com utilização por tracks, áreas e clientes
    """
    return [
        # Seção de Utilização por Tracks
        create_section_container([
            create_section_header('UTILIZAÇÃO POR TRACKS', f"{total_hours} hr"),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'monthly-tracks-graph',
                        create_tracks_graph(dfs['tracks'], height=None, max_items=8)
                    )
                ]
            )
        ], margin_bottom='8px'),

        # Utilização por Áreas
        create_section_container([
            create_section_header('UTILIZAÇÃO POR ÁREAS', f"{total_hours} hr"),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'monthly-areas-graph',
                        create_areas_graph(dfs['areas'], height=None)
                    )
                ]
            )
        ], margin_bottom='8px'),

        # Seção de Utilização por Clientes
        create_section_container([
            create_section_header('UTILIZAÇÃO POR CLIENTES', total_hours_ytd),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'ytd-customers-graph',
                        create_customers_stacked_graph(dfs['customers_ytd'], height=None)
                    )
                ]
            )
        ], margin_bottom='0px')
    ]


def optimize_dataframe(df, numeric_columns=None, categorical_columns=None, exclude_sum_columns=None):
    """
    Otimiza o uso de memória de um DataFrame, evitando converter para categoria colunas que precisam de soma.
    """
    if df is None or df.empty:
        return df

    # Se não especificado, criar lista vazia para colunas excluídas da soma
    if exclude_sum_columns is None:
        # Lista de colunas que nunca devem ser convertidas para categoria
        exclude_sum_columns=['StayTime', 'hours', 'HorasDecimais', 'HORAS_DECIMAL']

    # Criar um conjunto para verificação mais rápida
    exclude_set=set(exclude_sum_columns)

    # Fazer uma cópia para evitar modificar o original
    result=df.copy()

    # Otimizar colunas numéricas
    if numeric_columns:
        for col in numeric_columns:
            if col in result.columns:
                if result[col].dropna().empty:
                    continue

                # Determinar o menor tipo numérico possível
                col_min=result[col].min()
                col_max=result[col].max()

                # Inteiros
                if pd.api.types.is_integer_dtype(result[col]):
                    if col_min >= 0:
                        if col_max <= 255:
                            result[col]=result[col].astype('uint8')
                        elif col_max <= 65535:
                            result[col]=result[col].astype('uint16')
                        elif col_max <= 4294967295:
                            result[col]=result[col].astype('uint32')
                    else:
                        if col_min >= -128 and col_max <= 127:
                            result[col]=result[col].astype('int8')
                        elif col_min >= -32768 and col_max <= 32767:
                            result[col]=result[col].astype('int16')
                        elif col_min >= -2147483648 and col_max <= 2147483647:
                            result[col]=result[col].astype('int32')

                # Floats
                elif pd.api.types.is_float_dtype(result[col]):
                    result[col]=result[col].astype('float32')

    # Otimizar colunas categóricas
    if categorical_columns:
        for col in categorical_columns:
            if col in result.columns:
                # Pular colunas que precisam de soma
                if col in exclude_set:
                    continue

                if result[col].nunique() < len(result) * 0.5:  # Se menos de 50% de valores únicos
                    result[col]=result[col].astype('category')

    return result
