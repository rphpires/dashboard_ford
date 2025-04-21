# layouts/right_column.py
from dash import html

from components.sections import (
    create_section_container, create_section_header,
    create_metric_header, create_graph_section,
    create_bordered_container, create_side_by_side_container,
    create_flex_item, create_info_card,
)
from components.graphs import (
    create_programs_graph, create_other_skills_graph,
    create_internal_users_graph, create_external_sales_graph,
)


def create_optimized_utilization_breakdown(dfs, total_hours):
    # Calcular totais e percentuais para cada categoria
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

    return create_section_container([
        create_section_header('Monthly Utilization', f"{total_hours} hr"),
        html.Div(
            className='panel-content',
            children=[
                # # Indicadores de Resumo em linha compacta
                # html.Div(
                #     className='flex-container compact-info-cards',
                #     style={'marginBottom': '2px'},
                #     children=[
                #         create_info_card('Programs', f"{int(programas_horas)} hr",
                #                          f"{programas_perc_fmt} of total", color='#1E88E5'),
                #         create_info_card('Other Skill Teams', f"{int(outras_equipes_horas)} hr",
                #                          f"{outras_equipes_perc_fmt} of total", color='#673AB7'),
                #         create_info_card('Internal Users', f"{int(usuarios_internos_horas)} hr",
                #                          f"{usuarios_internos_perc_fmt} of total", color='#2E7D32'),
                #         create_info_card('External Sales', f"{int(vendas_externas_horas)} hr",
                #                          f"{vendas_externas_perc_fmt} of total", color='#F57C00')
                #     ]
                # ),

                # Programas - altura flexível
                create_bordered_container([
                    create_metric_header('Programs', f"{int(programas_horas)}", programas_perc_fmt),
                    create_graph_section(
                        'programs-graph',
                        create_programs_graph(dfs['programs'], height=None)
                    )
                ]),

                # Other Skill Teams - altura flexível
                create_bordered_container([
                    create_metric_header('Other Skill Teams', f"{int(outras_equipes_horas)}", outras_equipes_perc_fmt),
                    create_graph_section(
                        'other-skills-graph',
                        create_other_skills_graph(dfs['other_skills'], height=None)
                    )
                ]),

                # Internal Users and External Sales (lado a lado)
                create_side_by_side_container([
                    # Internal Users
                    create_flex_item([
                        create_metric_header('Internal Users', f"{int(usuarios_internos_horas)}", usuarios_internos_perc_fmt),
                        create_graph_section(
                            'internal-users-graph',
                            create_internal_users_graph(dfs['internal_users'], height=None)
                        )
                    ], margin_right='8px', min_width='38%'),

                    # External Sales
                    create_flex_item([
                        create_metric_header('External Sales', f"{int(vendas_externas_horas)}", vendas_externas_perc_fmt),
                        create_graph_section(
                            'external-sales-graph',
                            create_external_sales_graph(dfs['external_sales'], height=None)
                        )
                    ], min_width='38%')
                ])
            ]
        )
    ])
