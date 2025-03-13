# layouts/left_column.py
# Layout da coluna esquerda do dashboard com estilo moderno
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
    return html.Div(
        className='column',
        children=[
            # Seção de Utilização (%)
            create_section_container([
                create_section_header('UTILIZAÇÃO (%)', ytd_utilization_percentage),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section(
                            'utilization-graph',
                            create_utilization_graph(dfs['utilization'])
                        )
                    ]
                )
            ]),

            # Seção de Disponibilidade de Tracks (%)
            create_section_container([
                create_section_header('DISPONIBILIDADE DE TRACKS (%)', ytd_availability_percentage),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section(
                            'availability-graph',
                            create_availability_graph(dfs['availability'])
                        )
                    ]
                )
            ]),

            # Seção de Month Utilization Breakdown
            create_section_container([
                create_section_header('DETALHAMENTO DE UTILIZAÇÃO MENSAL', f"{total_hours} hr"),
                html.Div(
                    className='panel-content',
                    children=[
                        # Indicadores de Resumo
                        html.Div(
                            className='flex-container',
                            style={'marginBottom': '16px'},
                            children=[
                                create_info_card('Programas', '89 hr', '9% do total', color='#1E88E5'),
                                create_info_card('Outras Equipes', '130 hr', '13% do total', color='#673AB7'),
                                create_info_card('Uso Interno', '778 hr', '75% do total', color='#2E7D32'),
                                create_info_card('Vendas Externas', '34 hr', '3% do total', color='#F57C00')
                            ]
                        ),

                        # Programas - Com gráfico moderno
                        create_bordered_container([
                            create_metric_header('PROGRAMAS', '89', '9%'),
                            create_graph_section(
                                'programs-graph',
                                create_programs_graph(dfs['programs'])
                            )
                        ]),

                        # Other Skill Teams - Com gráfico moderno
                        create_bordered_container([
                            create_metric_header('OUTRAS EQUIPES DE HABILIDADES', '130', '13%'),
                            create_graph_section(
                                'other-skills-graph',
                                create_other_skills_graph(dfs['other_skills'])
                            )
                        ]),

                        # Internal Users and External Sales (lado a lado) - Com gráficos modernos
                        create_side_by_side_container([
                            # Internal Users
                            create_flex_item([
                                create_metric_header('USUÁRIOS INTERNOS', '778', '75%'),
                                create_graph_section(
                                    'internal-users-graph',
                                    create_internal_users_graph(dfs['internal_users'])
                                )
                            ], margin_right='10px'),

                            # External Sales
                            create_flex_item([
                                create_metric_header('VENDAS EXTERNAS', '34', '3%'),
                                create_graph_section(
                                    'external-sales-graph',
                                    create_external_sales_graph(dfs['external_sales'])
                                )
                            ])
                        ])
                    ]
                )
            ])
        ]
    )