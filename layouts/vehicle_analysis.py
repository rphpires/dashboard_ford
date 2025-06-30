# layouts/vehicle_analysis.py
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime as dt
from data.database import get_available_months
from utils.tracer import trace
from layouts.header import create_header


def create_vehicle_analysis_table(analysis_data, page_current=0, page_size=20):
    """
    Cria uma tabela com análise de tempo por veículo e empresa
    """
    if not analysis_data:
        return html.Div("Nenhum dado disponível para análise.", className="text-center my-4")

    # Converter para DataFrame para facilitar manipulação
    df = pd.DataFrame(analysis_data)

    # Ordenar por horas decimais (decrescente) - mantendo a lógica do script SQL
    df = df.sort_values('hours_decimal', ascending=False)

    # Calcular índices para paginação
    start_idx = page_current * page_size
    end_idx = start_idx + page_size
    paged_data = df.iloc[start_idx:end_idx].to_dict('records')

    # Cabeçalhos da tabela
    headers = ["#", "NOME", "TIPO", "DEPARTAMENTO", "TEMPO TOTAL"]

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
            html.Td(row['name'], title=row['name']),
            html.Td(row['type']),
            html.Td(row['department']),
            html.Td(row['hours_formatted'])
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
        id="vehicle-analysis-pagination",
        active_page=page_current + 1,
        max_value=total_pages,
        fully_expanded=False,
        first_last=True,
        previous_next=True,
        className="mt-3 justify-content-center"
    )

    # Estatísticas resumidas (calculadas a partir do total de dados, não apenas da página)
    total_hours = df['hours_decimal'].sum()
    total_items = len(df)

    # Converter total de horas para formato HH:MM
    total_minutes = int(total_hours * 60)
    hours_part = total_minutes // 60
    minutes_part = total_minutes % 60
    total_formatted = f"{hours_part:02d}:{minutes_part:02d}"

    summary = dbc.Row([
        dbc.Col([], md=3),
        dbc.Col([
            html.Div(
                className='card-metric',
                children=[
                    html.Div("Tempo Total", className="metric-title"),
                    html.Div(total_formatted, className="metric-value",
                             style={
                                 'textAlign': 'center',
                                 'width': '100%',
                                 'display': 'block',
                                 'margin': '0 auto'
                             })  # ✅ Múltiplas propriedades para forçar centralização
                ]
            )
        ], md=3),
        dbc.Col([
            html.Div(
                className='card-metric',
                children=[
                    html.Div("Total de Itens", className="metric-title"),
                    html.Div(str(total_items), className="metric-value",
                             style={
                                 'textAlign': 'center',
                                 'width': '100%',
                                 'display': 'block',
                                 'margin': '0 auto'
                    })  # ✅ Múltiplas propriedades para forçar centralização
                ]
            )
        ], md=3),
        dbc.Col([], md=3),
    ], className="mb-4")

    return html.Div([
        summary,
        table,
        pagination,
        html.Div(f"Mostrando {len(paged_data)} de {len(df)} registros",
                 className="text-muted text-center mt-2")
    ])


def create_vehicle_analysis_layout():
    """
    Cria o layout para análise de utilização de veículos e empresas
    """
    return html.Div(
        className='dashboard-container',
        children=[
            # Header - usando o mesmo sistema da aba de EJAs
            create_header(
                get_available_months(20),
                month_selector_id="vehicle-analysis-month-selector"
            ),

            # Body
            html.Div(
                className='dashboard-body',
                style={'padding': '20px'},
                children=[
                    dbc.Card([
                        dbc.CardBody([
                            # Container com altura fixa para filtros - igual ao da aba EJAs
                            html.Div(
                                className="analysis-filters-container",
                                children=[
                                    # Label separado
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("Buscar por nome:", className="mb-2")
                                        ], width=12)
                                    ]),

                                    # Linha com campo de busca e botões
                                    dbc.Row([
                                        # Coluna para o campo de busca
                                        dbc.Col([
                                            html.Div(
                                                className="filter-dropdown-container",
                                                children=[
                                                    dbc.Input(
                                                        id="vehicle-search-term",
                                                        type="text",
                                                        placeholder="Digite parte do nome do veículo ou empresa...",
                                                        className="w-100",
                                                        style={
                                                            'position': 'relative',
                                                            'zIndex': 100
                                                        }
                                                    )
                                                ]
                                            )
                                        ], md=6, className="pe-3"),

                                        # Coluna para os botões
                                        dbc.Col([
                                            html.Div(
                                                className="analysis-buttons-container",
                                                children=[
                                                    dbc.Button(
                                                        "Analisar",
                                                        id="vehicle-analyze-button",
                                                        color="primary",
                                                        className="me-2"
                                                    )
                                                ]
                                            )
                                        ], md=6, className="text-end")
                                    ], className="align-items-end")
                                ]
                            ),

                            # Espaçamento antes da tabela
                            html.Hr(className="my-3"),

                            # Container para a tabela
                            html.Div(
                                id="vehicle-analysis-table-container",
                                className="table-responsive",
                                style={
                                    "maxHeight": "calc(100vh - 350px)",
                                    "overflowY": "auto",
                                    "position": "relative",
                                    "zIndex": 1
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
            dcc.Store(id="vehicle-analysis-data-store", data={}),

            # Toast para feedback
            dbc.Toast(
                id="vehicle-analysis-status",
                header="Status da Análise",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 80, "right": 20, "width": 350, "zIndex": 1000}
            )
        ]
    )
