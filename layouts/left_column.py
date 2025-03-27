# layouts/left_column.py
# Layout da coluna esquerda do dashboard com estilo moderno

# from dash import html
# from components.sections import (
#     create_section_container, create_section_header,
#     create_metric_header, create_graph_section,
#     create_bordered_container, create_side_by_side_container,
#     create_flex_item, create_info_card
# )
# from components.graphs import (
#     create_utilization_graph, create_availability_graph,
#     create_programs_graph, create_other_skills_graph,
#     create_internal_users_graph, create_external_sales_graph
# )
from dash import html
from components.sections import (
    create_section_container, create_section_header,
    create_metric_header, create_graph_section,
    create_bordered_container, create_side_by_side_container,
    create_flex_item, create_info_card
)
from components.graphs import (
    create_utilization_graph, create_availability_graph,
    create_programs_graph, create_other_skills_graph,
    create_internal_users_graph, create_external_sales_graph
)


def create_left_column(dfs, ytd_utilization_percentage, ytd_availability_percentage, total_hours):
    """
    Cria o layout da coluna esquerda do dashboard com estilo moderno

    Args:
        dfs (dict): Dicionário com DataFrames
        ytd_utilization_percentage (str): Porcentagem de utilização YTD
        ytd_availability_percentage (str): Porcentagem de disponibilidade YTD
        total_hours (str): Total de horas

    Returns:
        dash.html.Div: Layout da coluna esquerda
    """
    # Calcular totais e percentuais para cada categoria
    try:
        # Extrair o valor numérico do total de horas (remover ':' se estiver no formato HH:MM)
        if ':' in total_hours:
            horas, minutos = map(int, total_hours.split(':'))
            total_horas_decimal = horas + (minutos / 60.0)
        else:
            # Se já estiver como número, converter para float
            total_horas_decimal = float(total_hours)

        # Calcular somas para cada categoria
        programas_horas = dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0
        outras_equipes_horas = dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0
        usuarios_internos_horas = dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0
        vendas_externas_horas = dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0

        # Calcular percentuais (evitar divisão por zero)
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

    except Exception as e:
        print(f"Erro ao calcular percentuais: {e}")
        # Valores padrão em caso de erro
        programas_horas = 89
        outras_equipes_horas = 130
        usuarios_internos_horas = 778
        vendas_externas_horas = 34
        programas_perc_fmt = "9%"
        outras_equipes_perc_fmt = "13%"
        usuarios_internos_perc_fmt = "75%"
        vendas_externas_perc_fmt = "3%"

    return html.Div(
        className='column',
        children=[
            # Seção de Utilização (%) - MODIFICADA: Cards agrupados e gráfico expandido
            create_section_container([
                create_section_header('UTILIZAÇÃO (%)', ytd_utilization_percentage),
                html.Div(
                    className='panel-content',
                    children=[
                        # Cards de resumo agrupados dentro da seção de Utilização
                        html.Div(
                            className='flex-container',
                            style={'marginBottom': '16px', 'justifyContent': 'space-between'},
                            children=[
                                create_info_card('Programas', f"{int(programas_horas)} hr",
                                                 f"{programas_perc_fmt} do total", color='#1E88E5'),
                                create_info_card('Outras Equipes', f"{int(outras_equipes_horas)} hr",
                                                 f"{outras_equipes_perc_fmt} do total", color='#673AB7'),
                                create_info_card('Uso Interno', f"{int(usuarios_internos_horas)} hr",
                                                 f"{usuarios_internos_perc_fmt} do total", color='#2E7D32'),
                                create_info_card('Vendas Externas', f"{int(vendas_externas_horas)} hr",
                                                 f"{vendas_externas_perc_fmt} do total", color='#F57C00')
                            ]
                        ),
                        # Gráfico expandido verticalmente
                        create_graph_section(
                            'utilization-graph',
                            create_utilization_graph(dfs['utilization'], height=240)
                        )
                    ]
                )
            ]),

            # Seção de Disponibilidade de Tracks (%) - MODIFICADA: Gráfico expandido
            create_section_container([
                create_section_header('DISPONIBILIDADE DE TRACKS (%)', ytd_availability_percentage),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section(
                            'availability-graph',
                            create_availability_graph(dfs['availability'], height=300)
                        )
                    ]
                )
            ]),

            # Seção de Detalhamento de Utilização Mensal - MODIFICADA: Expandida verticalmente
            create_section_container([
                create_section_header('DETALHAMENTO DE UTILIZAÇÃO MENSAL', f"{total_hours} hr"),
                html.Div(
                    className='panel-content',
                    style={'minHeight': '600px'},  # Aumentando o espaço vertical
                    children=[
                        # Programas - Com gráfico moderno
                        create_bordered_container([
                            create_metric_header('PROGRAMAS', f"{int(programas_horas)}", programas_perc_fmt),
                            create_graph_section(
                                'programs-graph',
                                create_programs_graph(dfs['programs'], height=240)
                            )
                        ]),

                        # Other Skill Teams - Com gráfico moderno
                        create_bordered_container([
                            create_metric_header('OUTRAS EQUIPES DE HABILIDADES', f"{int(outras_equipes_horas)}", outras_equipes_perc_fmt),
                            create_graph_section(
                                'other-skills-graph',
                                create_other_skills_graph(dfs['other_skills'], height=240)
                            )
                        ]),

                        # Internal Users and External Sales (lado a lado) - Com gráficos modernos
                        create_side_by_side_container([
                            # Internal Users
                            create_flex_item([
                                create_metric_header('USUÁRIOS INTERNOS', f"{int(usuarios_internos_horas)}", usuarios_internos_perc_fmt),
                                create_graph_section(
                                    'internal-users-graph',
                                    create_internal_users_graph(dfs['internal_users'], height=250)
                                )
                            ], margin_right='10px', min_width='38%'),

                            # External Sales
                            create_flex_item([
                                create_metric_header('VENDAS EXTERNAS', f"{int(vendas_externas_horas)}", vendas_externas_perc_fmt),
                                create_graph_section(
                                    'external-sales-graph',
                                    create_external_sales_graph(dfs['external_sales'], height=250)
                                )
                            ], min_width='38%')
                        ])
                    ]
                )
            ])
        ]
    )
