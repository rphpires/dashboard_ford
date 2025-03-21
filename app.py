# app.py
# Aplicação principal do dashboard zeentech VEV (versão otimizada sem rolagem)
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import datetime
from layouts.header import create_header
from components.sections import (
    create_section_container, create_section_header,
    create_metric_header, create_graph_section,
    create_bordered_container, create_side_by_side_container,
    create_flex_item, create_info_card, create_compact_metric_box, create_summary_metrics
)
from components.graphs import (
    create_utilization_graph, create_availability_graph,
    create_programs_graph, create_other_skills_graph,
    create_internal_users_graph, create_external_sales_graph,
    create_tracks_graph, create_areas_graph,
    create_customers_stacked_graph  # Nova função para gráfico de clientes
)
from layouts.eja_manager import create_eja_manager_layout
from layouts.left_column import create_left_column
from layouts.right_column import create_right_column

from data.database import load_dashboard_data, get_current_period_info
from data.eja_manager import EJAManager
import os
import base64
import json
import tempfile
from dash.exceptions import PreventUpdate

# Inicializar a aplicação Dash com Bootstrap para melhor estilo
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    title='Ford Dashboard',
    update_title='Carregando...',
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ],
)

# Obter dados reais
dfs = load_dashboard_data()

# Obter informações do período atual
periodo_info = get_current_period_info()
current_month = periodo_info['current_month']
current_day = periodo_info['current_day']
ytd_utilization_percentage = periodo_info['ytd_utilization_percentage']
ytd_availability_percentage = periodo_info['ytd_availability_percentage']
total_hours = periodo_info['total_hours']
total_hours_ytd = periodo_info['total_hours_ytd']

# Função para criar a coluna de gráficos de utilização e disponibilidade


def create_utilization_availability_column(dfs, ytd_utilization_percentage, ytd_availability_percentage):
    """
    Cria a coluna de gráficos de utilização e disponibilidade
    """
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

    return [
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
        ], margin_bottom='10px'),

        # Seção de Disponibilidade de Tracks (%) - MODIFICADA: Gráfico expandido
        create_section_container([
            create_section_header('DISPONIBILIDADE DE TRACKS (%)', ytd_availability_percentage),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'availability-graph',
                        create_availability_graph(dfs['availability'], height=240)
                    )
                ]
            )
        ], margin_bottom='10px')
    ]

# Função para criar o detalhamento de utilização mensal otimizado e expandido
def create_optimized_utilization_breakdown(dfs, total_hours):
    """
    Cria o layout otimizado para o detalhamento de utilização mensal,
    com gráficos maiores e melhor distribuídos.
    """
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
        create_section_header('DETALHAMENTO DE UTILIZAÇÃO MENSAL', f"{total_hours} hr"),
        html.Div(
            className='panel-content',
            style={'minHeight': '600px'},
            children=[
                # Indicadores de Resumo em linha compacta - espalhados horizontalmente
                html.Div(
                    className='flex-container compact-info-cards',
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

                # Programas - Com gráfico moderno e expandido
                create_bordered_container([
                    create_metric_header('PROGRAMAS', f"{int(programas_horas)}", programas_perc_fmt),
                    create_graph_section(
                        'programs-graph',
                        create_programs_graph(dfs['programs'], height=200)
                    )
                ]),

                # Other Skill Teams - Com gráfico moderno e expandido
                create_bordered_container([
                    create_metric_header('OUTRAS EQUIPES DE HABILIDADES', f"{int(outras_equipes_horas)}", outras_equipes_perc_fmt),
                    create_graph_section(
                        'other-skills-graph',
                        create_other_skills_graph(dfs['other_skills'], height=200)
                    )
                ]),

                # Internal Users and External Sales (lado a lado) - Com gráficos modernos
                create_side_by_side_container([
                    # Internal Users
                    create_flex_item([
                        create_metric_header('USUÁRIOS INTERNOS', f"{int(usuarios_internos_horas)}", usuarios_internos_perc_fmt),
                        create_graph_section(
                            'internal-users-graph',
                            create_internal_users_graph(dfs['internal_users'], height=200)
                        )
                    ], margin_right='10px', min_width='38%'),

                    # External Sales
                    create_flex_item([
                        create_metric_header('VENDAS EXTERNAS', f"{int(vendas_externas_horas)}", vendas_externas_perc_fmt),
                        create_graph_section(
                            'external-sales-graph',
                            create_external_sales_graph(dfs['external_sales'], height=200)
                        )
                    ], min_width='38%')
                ])
            ]
        )
    ])

# Função para criar a coluna com tracks, áreas e clientes (modificada)


def create_tracks_areas_column(dfs, total_hours, total_hours_ytd):
    """
    Cria a coluna com utilização por tracks, áreas e clientes
    Modificada para exibir apenas 8 tracks e usar novo tipo de gráfico para clientes
    """
    return [
        # Seção de Utilização por Tracks - MODIFICADA: Limitada aos 8 principais itens
        create_section_container([
            create_section_header('UTILIZAÇÃO POR TRACKS', f"{total_hours} hr"),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'monthly-tracks-graph',
                        create_tracks_graph(dfs['tracks'], height=260, max_items=8)
                    )
                ]
            )
        ], margin_bottom='10px'),

        # Utilização por Áreas - MODIFICADA: Layout simplificado e maior
        create_section_container([
            create_section_header('UTILIZAÇÃO POR ÁREAS', f"{total_hours} hr"),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'monthly-areas-graph',
                        create_areas_graph(dfs['areas'], height=260)  # MODIFICADO: Aumentando altura
                    )
                ]
            )
        ], margin_bottom='10px'),

        # Seção de Utilização por Clientes - MODIFICADA: Novo modelo de gráfico
        create_section_container([
            create_section_header('UTILIZAÇÃO POR CLIENTES', total_hours_ytd),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'ytd-customers-graph',
                        create_customers_stacked_graph(dfs['customers_ytd'], height=260)  # NOVO: Usando o novo tipo de gráfico
                    )
                ]
            )
        ], margin_bottom='0px')
    ]


# Layout da aplicação principal - versão otimizada com as modificações solicitadas
main_layout = html.Div(
    id='dashboard-container',
    className='dashboard-container full-screen',
    style={'height': '100vh', 'overflow': 'hidden'},  # Evitar barras de rolagem
    children=[
        # Cabeçalho
        create_header(current_month, current_day),

        # # Métricas de resumo - dispostas em linha para ocupar menos espaço vertical
        # html.Div(
        #     className='summary-metrics',
        #     children=[
        #         create_summary_metrics(ytd_utilization_percentage, ytd_availability_percentage, total_hours)
        #     ]
        # ),

        # Conteúdo principal - reorganizado para 3 colunas
        html.Div(
            className='dashboard-content three-column-layout',
            style={
                'display': 'flex',
                'flex': '1',
                'flexWrap': 'nowrap',  # Impedir quebra para garantir 3 colunas
                'overflow': 'hidden',
                'height': 'calc(100vh - 150px)'  # Ajustar altura para evitar rolagem
            },
            children=[
                # Coluna 1: Utilização e Disponibilidade
                html.Div(
                    className='column column-small',
                    style={
                        'width': '25%',
                        'minWidth': '180px',
                        'overflow': 'auto',
                        'paddingRight': '8px'
                    },
                    children=create_utilization_availability_column(
                        dfs,
                        ytd_utilization_percentage,
                        ytd_availability_percentage
                    )
                ),

                # Coluna 2: Utilização por Tracks, Áreas e Clientes
                html.Div(
                    className='column column-medium',
                    style={
                        'width': '37.5%',
                        'minWidth': '250px',
                        'overflow': 'auto'
                    },
                    children=create_tracks_areas_column(
                        dfs,
                        total_hours,
                        total_hours_ytd
                    )
                ),

                # Coluna 3: Detalhamento de Utilização
                html.Div(
                    className='column column-large',
                    style={
                        'width': '37.5%',
                        'minWidth': '250px',
                        'overflow': 'auto',
                        'paddingRight': '8px'
                    },
                    children=[
                        # Detalhamento da utilização mensal com layout otimizado e expandido
                        create_optimized_utilization_breakdown(
                            dfs,
                            total_hours
                        )
                    ]
                )
            ]
        ),

        # Rodapé com tamanho fixo
        html.Div(
            className='footer',
            style={
                'textAlign': 'center',
                'padding': '5px',
                'fontSize': '12px',
                'color': '#546E7A',
                'height': '30px'
            },
            children=[
                f"zeentech VEV Dashboard • Atualizado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ]
        )
    ]
)

# Definir o layout com navegação por abas
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='eja-store', data={}),
    dcc.Store(id='eja-data-store', data={}),
    html.Div(id='dummy-div-edit', style={'display': 'none'}),
    html.Div(id='dummy-div-delete', style={'display': 'none'}),
    html.Div(id='eja-delete-refresh', style={'display': 'none'}),
    html.Div(id='import-refresh', style={'display': 'none'}),
    html.Div([
        dbc.Tabs(
            id='tabs',
            children=[
                dbc.Tab(label='Dashboard', tab_id='tab-dashboard'),
                dbc.Tab(label='Gerenciar EJAs', tab_id='tab-eja-manager'),
            ],
            active_tab='tab-dashboard',
        ),
    ]),
    html.Div(id='tab-content')
])

# Callback para atualizar o conteúdo baseado na aba selecionada


@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab')
)
def render_tab_content(active_tab):
    if active_tab == 'tab-dashboard':
        return main_layout
    elif active_tab == 'tab-eja-manager':
        # Ao renderizar o layout do EJA Manager, também carregamos os dados iniciais
        layout = create_eja_manager_layout()

        # Pré-carregar a tabela com todos os EJAs
        eja_manager = EJAManager()
        all_ejas = eja_manager.get_all_ejas()

        # Encontrar o container da tabela no layout e atualizar seu conteúdo
        for child in layout.children:
            if isinstance(child, dbc.Card) and hasattr(child, 'children'):
                for card_child in child.children:
                    if isinstance(card_child, dbc.CardBody) and hasattr(card_child, 'children'):
                        for body_child in card_child.children:
                            if hasattr(body_child, 'id') and body_child.id == "eja-table-container":
                                body_child.children = create_eja_table(all_ejas)

        return layout
    return html.Div("Conteúdo não encontrado")

# Função auxiliar para criar a tabela de EJAs com paginação


def create_eja_table(ejas, page_current=0, page_size=15):
    if not ejas:
        return html.Div("Nenhum EJA encontrado.", className="mt-3 text-center")

    # Aplicar paginação
    start_idx = page_current * page_size
    end_idx = (page_current + 1) * page_size
    paginated_ejas = ejas[start_idx:end_idx]

    # Calcular total de páginas
    total_pages = (len(ejas) - 1) // page_size + 1

    # Criar cabeçalho da tabela
    header = html.Thead(html.Tr([
        html.Th("Nº"),
        html.Th("EJA CODE"),
        html.Th("TITLE"),
        html.Th("CLASSIFICATION"),
        html.Th("Ações", style={"width": "120px", "text-align": "center"})
    ]))

    # Criar linhas da tabela
    rows = []
    for eja in paginated_ejas:
        eja_id = eja.get('Nº', '')

        # Criar menu dropdown para ações
        action_menu = dbc.DropdownMenu(
            label="Ações",
            size="sm",
            color="light",
            children=[
                # Botões dentro do dropdown
                dbc.DropdownMenuItem(
                    "Editar",
                    id={"type": "edit-button", "index": eja_id}
                ),
                dbc.DropdownMenuItem(
                    "Excluir",
                    id={"type": "delete-button", "index": eja_id},
                    style={"color": "red"}
                ),
            ],
        )

        row = html.Tr([
            html.Td(eja_id),
            html.Td(eja.get('EJA CODE', '')),
            html.Td(eja.get('TITLE', '')),
            html.Td(eja.get('NEW CLASSIFICATION', '')),
            html.Td(action_menu, style={"text-align": "center"})
        ])
        rows.append(row)

    body = html.Tbody(rows)

    # Montar tabela completa
    table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)

    # Controles de paginação
    pagination = dbc.Pagination(
        id="eja-pagination",
        max_value=total_pages,
        first_last=True,
        previous_next=True,
        size="sm",
        fully_expanded=False,
        active_page=page_current + 1,  # Páginas na UI começam em 1
        className="mt-3 d-flex justify-content-center"
    )

    # Informação sobre a paginação
    pagination_info = html.Div(
        f"Mostrando {min(start_idx + 1, len(ejas))} a {min(end_idx, len(ejas))} de {len(ejas)} registros",
        className="text-muted text-center small mt-2"
    )

    return html.Div([table, pagination, pagination_info])


# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
