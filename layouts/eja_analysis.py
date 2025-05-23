# layouts/eja_analysis.py
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime as dt
from data.eja_manager import get_eja_manager
from data.database import ReportGenerator, get_available_months
from utils.tracer import trace
from config.layout_config import layout_config
from layouts.header import create_header  # Importar a função create_header


def create_eja_analysis_table(analysis_data, page_current=0, page_size=20):
    """
    Cria uma tabela com análise de tempo por EJA (com estilo simples)
    """
    if not analysis_data:
        return html.Div("Nenhum dado disponível para análise.", className="text-center my-4")

    # Converter para DataFrame para facilitar manipulação
    df = pd.DataFrame(analysis_data)

    # Ordenar por horas (decrescente)
    df = df.sort_values('hours_decimal', ascending=False)

    # Calcular índices para paginação
    start_idx = page_current * page_size
    end_idx = start_idx + page_size
    paged_data = df.iloc[start_idx:end_idx].to_dict('records')

    # Cabeçalhos da tabela
    headers = ["#", "EJA CODE", "TÍTULO", "CLASSIFICAÇÃO", "HORAS", "PERCENTUAL"]

    # Criar linha de cabeçalho
    header_row = html.Tr([html.Th(h) for h in headers])

    # Criar linhas de dados
    data_rows = []
    for i, row in enumerate(paged_data):
        # Calcular o número da linha considerando a paginação
        row_number = start_idx + i + 1

        # Criar linha da tabela
        tr = html.Tr([
            html.Td(row_number),
            html.Td(row['eja_code']),
            html.Td(row['title'], title=row['title']),
            html.Td(row['classification']),
            html.Td(row['hours_formatted']),
            html.Td(f"{row['percentage']:.2f}%"),
            # html.Td(f"{row['cumulative_percentage']:.2f}%"),
        ])

        data_rows.append(tr)

    # Criar tabela com classe table-striped para alternância de cores
    table = html.Table(
        [html.Thead(header_row), html.Tbody(data_rows)],
        className="table table-striped table-hover"
    )

    # Calcular o número total de páginas
    total_pages = (len(df) - 1) // page_size + 1 if len(df) > 0 else 1

    # Criar paginação
    pagination = dbc.Pagination(
        id="eja-analysis-pagination",
        active_page=page_current + 1,
        max_value=total_pages,
        fully_expanded=False,
        first_last=True,
        previous_next=True,
        className="mt-3 justify-content-center"
    )

    # Estatísticas resumidas
    total_hours = df['hours_decimal'].sum()
    total_ejas = len(df)
    # top_20_count = len(df[df['cumulative_percentage'] <= 20])

    summary = dbc.Row([
        dbc.Col([], md=3),
        dbc.Col([
            html.Div(
                className='card-metric',
                children=[
                    html.Div("Total de Horas", className="metric-title"),
                    html.Div(f"{int(total_hours):,} hrs", className="metric-value")
                ]
            )
        ], md=3),
        dbc.Col([
            html.Div(
                className='card-metric',
                children=[
                    html.Div("Total de EJAs", className="metric-title"),
                    html.Div(str(total_ejas), className="metric-value")
                ]
            )
        ], md=3),
        dbc.Col([], md=3),
    ], className="mb-4")

    return html.Div([
        # summary,
        table,
        pagination,
        html.Div(f"Mostrando {len(paged_data)} de {len(df)} registros",
                 className="text-muted text-center mt-2")
    ])


def create_eja_analysis_layout():
    """
    Cria o layout para análise de utilização de EJAs
    """
    return html.Div(
        className='dashboard-container',
        children=[
            # Header
            create_header(
                get_available_months(20),
                month_selector_id="analysis-month-selector"
            ),

            # Body
            html.Div(
                className='dashboard-body',
                style={'padding': '20px'},
                children=[
                    dbc.Card([
                        dbc.CardBody([
                            # Filtros
                            # dbc.Row([
                            #     dbc.Col([
                            #         dbc.Label("Classificação:"),
                            #         dcc.Dropdown(
                            #             id="analysis-classification-filter",
                            #             options=[{"label": "Todas", "value": "ALL"}],
                            #             value="ALL",
                            #             placeholder="Filtrar por classificação...",
                            #             className="mb-2"
                            #         )
                            #     ], md=4),

                            #     dbc.Col([
                            #         html.Div([
                            #             dbc.Button(
                            #                 "Analisar",
                            #                 id="analyze-button",
                            #                 color="primary",
                            #                 className="me-2",
                            #                 disabled=False
                            #             ),
                            #             dbc.Button(
                            #                 "Exportar Análise",
                            #                 id="export-analysis-button",
                            #                 color="success",
                            #                 disabled=True
                            #             )
                            #         ], className="d-flex align-items-end h-100")
                            #     ], md=8)
                            # ], className="mb-3"),
                            dbc.Row([dbc.Label("Classificação:")]),
                            dbc.Row([
                                dbc.Col([
                                    # dbc.Label("Classificação:", className="mb-1"),
                                    dcc.Dropdown(
                                        id="analysis-classification-filter",
                                        options=[{"label": "Todas", "value": "ALL"}],
                                        value="ALL",
                                        placeholder="Filtrar por classificação...",
                                        className="w-100"
                                    )
                                ], md=6),

                                dbc.Col(
                                    dbc.Button(
                                        "Analisar",
                                        id="analyze-button",
                                        color="primary",
                                        className="me-2"
                                    ),
                                    md="auto",
                                    className="d-flex align-items-center"
                                ),

                                dbc.Col(
                                    dbc.Button(
                                        "Exportar Análise",
                                        id="export-analysis-button",
                                        color="success"
                                    ),
                                    md="auto",
                                    className="d-flex align-items-center"
                                )
                            ], className="mb-3 align-items-center"),

                            # Container para a tabela
                            html.Div(
                                id="eja-analysis-table-container",
                                className="table-responsive",
                                style={
                                    "maxHeight": "calc(100vh - 300px)",
                                    "overflowY": "auto"
                                },
                                children=[
                                    html.Div(
                                        "Selecione um mês e clique em 'Analisar' para visualizar os dados.",
                                        className="text-center text-muted my-5"
                                    )
                                ]
                            ),
                        ])
                    ])
                ]
            ),

            # Store para armazenar dados
            dcc.Store(id="eja-analysis-data-store", data={}),

            # Toast para feedback
            dbc.Toast(
                id="analysis-status",
                header="Status da Análise",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 80, "right": 20, "width": 350, "zIndex": 1000}
            ),

            # Componente para download
            dcc.Download(id="download-analysis-csv")
        ]
    )
