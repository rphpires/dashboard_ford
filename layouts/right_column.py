# layouts/right_column.py
# Layout da coluna direita do dashboard com estilo moderno
from dash import html
from components.sections import (
    create_section_container, create_section_header, create_graph_section
)
from components.graphs import (
    create_tracks_graph, create_areas_graph, create_customers_graph
)


def create_right_column(dfs, total_hours, total_hours_ytd):
    """
    Cria o layout da coluna direita do dashboard com estilo moderno

    Args:
        dfs (dict): Dicionário com DataFrames
        total_hours (str): Total de horas
        total_hours_ytd (str): Total de horas YTD

    Returns:
        dash.html.Div: Layout da coluna direita
    """
    return html.Div(
        className='column',
        children=[
            # Seção de Month Utilization by Tracks - Usando treemap moderno
            create_section_container([
                create_section_header('UTILIZAÇÃO MENSAL POR TRACKS', f"{total_hours} hr"),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section(
                            'monthly-tracks-graph',
                            create_tracks_graph(dfs['tracks'])
                        )
                    ]
                )
            ]),

            # Seção de YTD Utilization by Tracks - Usando treemap moderno
            create_section_container([
                create_section_header('UTILIZAÇÃO YTD POR TRACKS', total_hours_ytd),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section(
                            'ytd-tracks-graph',
                            create_tracks_graph(dfs['tracks_ytd'], height=220, bottom_margin=10)
                        )
                    ]
                )
            ]),

            # Utilization by Areas - Combinando mensal e YTD em um único container
            create_section_container([
                create_section_header('UTILIZAÇÃO POR ÁREAS', f"{total_hours} hr (Mensal) / {total_hours_ytd} (YTD)"),
                html.Div(
                    className='panel-content',
                    children=[
                        html.Div(
                            className='flex-container',
                            children=[
                                # Month Utilization by Areas
                                html.Div(
                                    className='flex-item',
                                    children=[
                                        html.Div(
                                            className='metric-box',
                                            style={'justifyContent': 'center', 'marginBottom': '10px'},
                                            children=[
                                                html.Div("MENSAL", className='metric-title')
                                            ]
                                        ),
                                        create_graph_section(
                                            'monthly-areas-graph',
                                            create_areas_graph(dfs['areas'], height=180)
                                        )
                                    ]
                                ),
                                
                                # YTD Utilization by Areas
                                html.Div(
                                    className='flex-item',
                                    children=[
                                        html.Div(
                                            className='metric-box',
                                            style={'justifyContent': 'center', 'marginBottom': '10px'},
                                            children=[
                                                html.Div("YTD", className='metric-title')
                                            ]
                                        ),
                                        create_graph_section(
                                            'ytd-areas-graph',
                                            create_areas_graph(dfs['areas_ytd'], height=180)
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]),

            # Seção de YTD Utilization by Customers - Usando sunburst moderno
            create_section_container([
                create_section_header('UTILIZAÇÃO YTD POR CLIENTES', total_hours_ytd),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section(
                            'ytd-customers-graph',
                            create_customers_graph(dfs['customers_ytd'])
                        )
                    ]
                )
            ], margin_bottom='0px')
        ]
    )