# app.py
# Aplicação principal do dashboard zeentech VEV (versão otimizada sem rolagem)
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, callback_context
import dash_bootstrap_components as dbc
import datetime
from utils.tracer import *
from layouts.header import create_header
from config.layout_config import layout_config, get_responsive_config
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
from data.eja_manager import get_eja_manager
from data.tracks_manager import adjust_tracks_names
from layouts.eja_manager import create_eja_table
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

# # Obter dados reais
dfs, tracks_data, areas_data_df = load_dashboard_data()

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
            children=[
                # Indicadores de Resumo em linha compacta
                html.Div(
                    className='flex-container compact-info-cards',
                    style={'marginBottom': '8px'},
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

                # Programas - altura flexível
                create_bordered_container([
                    create_metric_header('PROGRAMAS', f"{int(programas_horas)}", programas_perc_fmt),
                    create_graph_section(
                        'programs-graph',
                        create_programs_graph(dfs['programs'], height=None)
                    )
                ]),

                # Other Skill Teams - altura flexível
                create_bordered_container([
                    create_metric_header('OUTRAS EQUIPES DE HABILIDADES', f"{int(outras_equipes_horas)}", outras_equipes_perc_fmt),
                    create_graph_section(
                        'other-skills-graph',
                        create_other_skills_graph(dfs['other_skills'], height=None)
                    )
                ]),

                # Internal Users and External Sales (lado a lado)
                create_side_by_side_container([
                    # Internal Users
                    create_flex_item([
                        create_metric_header('USUÁRIOS INTERNOS', f"{int(usuarios_internos_horas)}", usuarios_internos_perc_fmt),
                        create_graph_section(
                            'internal-users-graph',
                            create_internal_users_graph(dfs['internal_users'], height=None)
                        )
                    ], margin_right='8px', min_width='38%'),

                    # External Sales
                    create_flex_item([
                        create_metric_header('VENDAS EXTERNAS', f"{int(vendas_externas_horas)}", vendas_externas_perc_fmt),
                        create_graph_section(
                            'external-sales-graph',
                            create_external_sales_graph(dfs['external_sales'], height=None)
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
        # Seção de Utilização por Tracks
        create_section_container([
            create_section_header('UTILIZAÇÃO POR TRACKS', f"{total_hours} hr"),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'monthly-tracks-graph',
                        create_tracks_graph(adjust_tracks_names(tracks_data), height=None, max_items=8)
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
                        create_areas_graph(areas_data_df, height=None)  # TODO: Use real data on this graph
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
                        create_customers_stacked_graph(dfs['customers_ytd'], height=None)  # TODO: Use real data on this graph
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
        # Conteúdo principal - reorganizado para 3 colunas
        html.Div(
            className='dashboard-content three-column-layout',
            children=[
                # Coluna 1: Utilização e Disponibilidade
                html.Div(
                    className='column column-small',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
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
                        'width': '33.33%',
                        'minWidth': '200px',
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
                        'width': '33.33%',
                        'minWidth': '200px',
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
    html.Div(id='resize-trigger', style={'display': 'none'}),
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
        eja_manager = get_eja_manager()
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


app.clientside_callback(
    """
    function() {
        // Calcula a altura disponível quando a aba é carregada
        var windowHeight = window.innerHeight;
        var tableContainer = document.querySelector('.eja-table-container');

        if (tableContainer) {
            var tableTop = tableContainer.offsetTop;
            var paginationHeight = 100; // Espaço para paginação e outras informações
            var availableHeight = windowHeight - tableTop - paginationHeight;

            // Certifique-se de que a altura não seja muito pequena
            availableHeight = Math.max(availableHeight, 300);

            // Define a variável CSS
            document.documentElement.style.setProperty('--table-height', availableHeight + 'px');
        }

        return '';
    }
    """,
    Output('resize-trigger', 'children'),
    Input('tabs', 'active_tab')
)


# Callback para abrir o modal de importação
@callback(
    Output("import-modal", "is_open"),
    Input("import-csv-button", "n_clicks"),
    Input("cancel-import-button", "n_clicks"),
    State("import-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_import_modal(import_click, cancel_click, is_open):
    if import_click or cancel_click:
        return not is_open
    return is_open


@callback(
    Output("delete-eja-modal", "is_open"),
    Output("delete-confirmation-message", "children"),
    Output("delete-eja-id", "value"),
    Input({"type": "delete-button", "index": dash.ALL, "action": "delete"}, "n_clicks"),
    Input("cancel-delete-button", "n_clicks"),
    prevent_initial_call=True
)
def show_delete_confirmation(delete_clicks, cancel_click):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Obter o ID completo do elemento que disparou o callback
    trigger_full = ctx.triggered[0]['prop_id']
    trigger_id = trigger_full.split('.')[0]

    trace(f"show_delete_confirmation: {trigger_full=}")

    # Para o botão cancelar
    if "cancel-delete-button" in trigger_full:
        return False, "", ""

    if delete_clicks and any(click for click in delete_clicks if click):
        # Identificar qual botão foi clicado
        triggered_id = json.loads(trigger_full.split(".")[0])
        row_id = triggered_id["index"]

        # Buscar informações do EJA
        eja_manager = get_eja_manager()
        eja = eja_manager.get_eja_by_id(row_id)

        if eja:
            # Obter código e título
            eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
            title = eja.get('TITLE', eja.get('title', ''))

            # Criar mensagem de confirmação
            message = f"Tem certeza que deseja excluir o EJA #{row_id} ({eja_code} - {title})?"
            return True, message, row_id

    # Log para depuração
    print(f"DEBUG - show_delete_confirmation triggered by: {trigger_full}")

    # Para o botão cancelar
    if trigger_id == "cancel-delete-button":
        return False, "", ""

    # Para botões de exclusão - verificação mais rigorosa
    try:
        # Verificar explicitamente se o ID corresponde ao padrão esperado
        if '{"type":"delete-button"' in trigger_id:
            try:
                trigger_dict = json.loads(trigger_id)
                if isinstance(trigger_dict, dict) and trigger_dict.get("type") == "delete-button":
                    row_id = trigger_dict.get("index")
                    if row_id:
                        # Buscar informações do EJA
                        eja_manager = get_eja_manager()
                        eja = eja_manager.get_eja_by_id(row_id)

                        if eja:
                            # Obter código e título
                            eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
                            title = eja.get('TITLE', eja.get('title', ''))
                            # Criar mensagem de confirmação
                            message = f"Tem certeza que deseja excluir o EJA #{row_id} ({eja_code} - {title})?"
                            return True, message, row_id
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSONDecodeError: {str(e)} for trigger_id: {trigger_id}")
                raise PreventUpdate

        # Se chegou aqui, o trigger não é um botão de exclusão válido
        print(f"DEBUG - Not a valid delete button: {trigger_id}")
        raise PreventUpdate
    except Exception as e:
        print(f"DEBUG - Erro ao processar clique: {type(e).__name__}: {str(e)}")
        raise PreventUpdate


# Callback para abrir o modal de adição de EJA
@app.callback(
    [
        Output("eja-form-modal", "is_open"),
        Output("eja-form-title", "children"),
        Output("form-mode", "value"),
        Output("eja-code-input", "value"),
        Output("eja-title-input", "value"),
        Output("eja-classification-input", "value"),
        Output("edit-eja-id", "value")
    ],
    [
        Input("add-eja-button", "n_clicks"),
        Input("cancel-eja-form-button", "n_clicks"),
        Input({"type": "edit-button", "index": dash.ALL}, "n_clicks"),
    ],
    [
        State("eja-form-modal", "is_open"),
    ],
    prevent_initial_call=True
)
def toggle_eja_form_modal(add_clicks, cancel_clicks, edit_clicks, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Adicionar novo EJA - abrir modal vazio
    if trigger_id == "add-eja-button":
        return True, "Adicionar Novo EJA", "add", "", "", "", ""

    # Cancelar - fechar modal
    if trigger_id == "cancel-eja-form-button":
        return False, "", "", "", "", "", ""

    # Editar EJA existente
    if isinstance(trigger_id, dict) and trigger_id.get("type") == "edit-button":
        eja_id = trigger_id.get("index")
        if eja_id:
            # Obter os dados do EJA para edição
            eja_manager = get_eja_manager()
            eja = eja_manager.get_eja_by_id(eja_id)

            if eja:
                # Obter os valores para os campos do formulário
                eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
                title = eja.get('TITLE', eja.get('title', ''))
                classification = eja.get('NEW CLASSIFICATION', eja.get('new_classification', ''))

                return True, f"Editar EJA #{eja_id}", "edit", eja_code, title, classification, eja_id

    # Caso padrão - não altera o estado atual
    return is_open, "", "", "", "", "", ""


# Callback unificado para gerenciar todas as atualizações da tabela EJA
@callback(
    Output("eja-table-container", "children"),
    Output("eja-data-store", "data"),
    [
        Input({"type": "search-button", "action": "search"}, "n_clicks"),
        Input("eja-delete-refresh", "children"),
        Input("import-refresh", "children"),
        Input("eja-pagination", "active_page")
    ],
    [
        State("search-term", "value"),
        State("search-eja-code", "value"),
        State("eja-data-store", "data")
    ],
    prevent_initial_call=True
)
def update_eja_table(
    search_clicks, delete_refresh, import_refresh, active_page,
    search_term, eja_code, data_store
):
    # Determinar qual input disparou o callback
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Identificar o acionador com informações completas
    trigger_full = ctx.triggered[0]['prop_id']
    trigger_id = trigger_full.split('.')[0]

    # Log para depuração
    print(f"DEBUG - update_eja_table triggered by: {trigger_full}")

    # Carregar o gerenciador de EJAs
    eja_manager = get_eja_manager()

    # Processar de acordo com o acionador
    if trigger_id == "search-button" and search_clicks:
        # Busca de EJAs
        print(f"DEBUG - Search triggered with: term={search_term}, code={eja_code}")
        filtered_ejas = eja_manager.search_ejas(search_term=search_term, eja_code=eja_code)
        print(f"DEBUG - Search returned {len(filtered_ejas)} items")

        # Atualizar o data_store com os resultados filtrados
        data_store['filtered_ejas'] = filtered_ejas
        data_store['page_current'] = 0

        return create_eja_table(filtered_ejas, page_current=0), data_store

    elif trigger_id in ["eja-delete-refresh", "import-refresh"]:
        # Atualização após exclusão ou importação
        all_ejas = eja_manager.get_all_ejas()

        # Resetar para mostrar todos os EJAs
        data_store['filtered_ejas'] = all_ejas
        data_store['page_current'] = 0

        return create_eja_table(all_ejas, page_current=0), data_store

    elif trigger_id == "eja-pagination":
        # Atualização de paginação
        if not active_page:
            raise PreventUpdate

        # Ajustar página (UI é base 1, código é base 0)
        page_current = active_page - 1
        data_store['page_current'] = page_current

        # Usar os dados filtrados atuais (não buscar todos novamente)
        filtered_ejas = data_store.get('filtered_ejas', [])
        if not filtered_ejas:
            filtered_ejas = eja_manager.get_all_ejas()
            data_store['filtered_ejas'] = filtered_ejas

        return create_eja_table(filtered_ejas, page_current=page_current), data_store

    # Caso padrão - não atualizar
    raise PreventUpdate


def create_search_button():
    """
    Cria um botão de busca com um ID exclusivo para evitar conflitos com outros callbacks
    """
    return dbc.Button(
        "Buscar",
        id={"type": "search-button", "action": "search"},
        color="primary",
        className="mr-2"
    )


@callback(
    Output("eja-table-container", "children", allow_duplicate=True),
    Output("eja-data-store", "data", allow_duplicate=True),
    [
        Input({"type": "search-button", "action": "search"}, "n_clicks"),
    ],
    [
        State("search-term", "value"),
        State("search-eja-code", "value"),
        State("eja-data-store", "data")
    ],
    prevent_initial_call=True
)
def handle_search_button(
    search_clicks, search_term, eja_code, data_store
):
    if not search_clicks:
        raise PreventUpdate

    # Log para depuração
    print(f"DEBUG - handle_search_button triggered with: term={search_term}, code={eja_code}")

    # Carregar o gerenciador de EJAs
    eja_manager = get_eja_manager()

    # Busca de EJAs
    filtered_ejas = eja_manager.search_ejas(search_term=search_term, eja_code=eja_code)
    print(f"DEBUG - Search returned {len(filtered_ejas)} items")

    # Atualizar o data_store com os resultados filtrados
    data_store['filtered_ejas'] = filtered_ejas
    data_store['page_current'] = 0

    return create_eja_table(filtered_ejas, page_current=0), data_store


@callback(
    [
        Output("eja-delete-status", "is_open", allow_duplicate=True),
        Output("eja-delete-status", "children", allow_duplicate=True),
        Output("eja-delete-status", "header", allow_duplicate=True),
        Output("eja-delete-status", "color", allow_duplicate=True),
        Output("eja-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("confirm-delete-button", "n_clicks"),
    State("delete-eja-id", "value"),
    prevent_initial_call=True
)
def delete_eja(confirm_click, eja_id):
    if not confirm_click or not eja_id:
        raise PreventUpdate

    # Realizar a exclusão
    eja_manager = get_eja_manager()
    success = eja_manager.delete_eja(eja_id)

    # Gerar timestamp único para atualização da tabela
    import time
    refresh_time = str(time.time())

    if success:
        return True, "EJA excluído com sucesso!", "Exclusão Concluída", "success", refresh_time
    else:
        return True, "Erro ao excluir o EJA.", "Erro", "danger", no_update


@callback(
    Output("delete-eja-modal", "is_open", allow_duplicate=True),
    Input("confirm-delete-button", "n_clicks"),
    prevent_initial_call=True
)
def close_delete_modal(n_clicks):
    if n_clicks:
        return False
    raise PreventUpdate


# Callback para salvar o EJA (novo ou editado)
@app.callback(
    [
        Output("eja-form-status", "is_open"),
        Output("eja-form-status", "children"),
        Output("eja-form-status", "header"),
        Output("eja-form-status", "color"),
        Output("eja-form-modal", "is_open", allow_duplicate=True),
        Output("eja-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("save-eja-form-button", "n_clicks"),
    [
        State("form-mode", "value"),
        State("edit-eja-id", "value"),
        State("eja-code-input", "value"),
        State("eja-title-input", "value"),
        State("eja-classification-input", "value"),
    ],
    prevent_initial_call=True
)
def save_eja_form(n_clicks, form_mode, edit_eja_id, eja_code, title, classification):
    if not n_clicks:
        raise PreventUpdate

    # Validar campos obrigatórios
    if not eja_code or not title:
        return True, "Preencha todos os campos obrigatórios.", "Erro", "danger", True, no_update

    try:
        # Preparar os dados do EJA
        eja_data = {
            "eja_code": eja_code,
            "title": title,
            "new_classification": classification or ""  # Garantir que nunca seja None
        }

        # Obter gerenciador de EJAs
        eja_manager = get_eja_manager()

        # Adicionar ou atualizar o EJA dependendo do modo
        if form_mode == "add":
            result = eja_manager.add_eja(eja_data)
            success_message = "EJA adicionado com sucesso!"
            error_prefix = "Erro ao adicionar EJA:"
        else:  # mode == "edit"
            result = eja_manager.update_eja(edit_eja_id, eja_data)
            success_message = "EJA atualizado com sucesso!"
            error_prefix = "Erro ao atualizar EJA:"

        # Verificar resultado
        if isinstance(result, dict) and result.get('error'):
            return True, f"{error_prefix} {result['error']}", "Erro", "danger", True, no_update

        # Gerar timestamp para atualizar a tabela
        import time
        refresh_time = str(time.time())

        # Sucesso - fechar modal e mostrar mensagem
        return True, success_message, "Sucesso", "success", False, refresh_time

    except Exception as e:
        # Erro - mostrar mensagem mas manter modal aberto
        return True, f"Erro: {str(e)}", "Erro", "danger", True, no_update


# Callback for handling CSV export
@callback(
    Input("export-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_csv_export(n_clicks):
    if not n_clicks:
        raise PreventUpdate

    try:
        # Export the EJA data using the manager
        eja_manager = get_eja_manager()
        export_path = eja_manager.export_csv()

        if export_path and os.path.exists(export_path):
            return True, f"Dados exportados com sucesso para: {export_path}", "Exportação Concluída", "success"
        else:
            return True, f"Erro ao exportar: {export_path}", "Erro", "danger"
    except Exception as e:
        return True, f"Erro ao exportar: {str(e)}", "Erro", "danger"


# Callback para processar a importação de CSV
@callback(
    Input("import-csv-button", "n_clicks"),
    State("upload-csv", "contents"),
    State("upload-csv", "filename"),
    State("overwrite-checkbox", "value"),
    prevent_initial_call=True
)
def process_csv_import(n_clicks, contents, filename, overwrite):
    if not n_clicks or not contents:
        raise PreventUpdate

    try:
        # Decodificar o conteúdo do arquivo
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp:
            temp.write(decoded)
            temp_path = temp.name

        # Importar usando o gerenciador de EJAs
        eja_manager = get_eja_manager()
        overwrite_flag = overwrite and "overwrite" in overwrite
        result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

        # Remover o arquivo temporário
        os.unlink(temp_path)

        # Verificar resultado
        if 'error' in result:
            return True, result['error'], "Erro na Importação", "danger", no_update, False

        # Mensagem de sucesso
        if overwrite_flag:
            message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
        else:
            message = f"Importação concluída! Adicionados: {result.get('imported', 0)}, Atualizados: {result.get('updated', 0)}, Ignorados: {result.get('skipped', 0)}."

        # Gerar timestamp único para atualização da tabela
        import time
        refresh_time = str(time.time())

        return True, message, "Importação Concluída", "success", refresh_time, False

    except Exception as e:
        return True, f"Erro ao processar arquivo: {str(e)}", "Erro", "danger", no_update, False


# Callback for handling file upload and import
@callback(
    Input("upload-csv", "contents"),
    Input("import-csv-button", "n_clicks"),
    Input("cancel-import-button", "n_clicks"),
    State("upload-csv", "filename"),
    State("overwrite-checkbox", "value"),
    State("import-modal", "is_open"),
    prevent_initial_call=True
)
def handle_csv_import(contents, import_click, cancel_click, filename, overwrite, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Cancel button - close modal
    if trigger_id == "cancel-import-button":
        return False, "", "", "", False, no_update

    # Upload file - store content
    if trigger_id == "upload-csv" and contents is not None:
        # Store content in hidden div for later use
        return False, "", "", "", is_open, json.dumps({"filename": filename, "content": contents})

    # Import button - process file
    if trigger_id == "import-csv-button" and import_click:
        # Get stored content
        if not dash.callback_context.states['import-refresh.children']:
            return True, "Nenhum arquivo selecionado", "Erro", "danger", False, no_update

        try:
            # Parse stored content
            stored_data = json.loads(dash.callback_context.states['import-refresh.children'])
            content_string = stored_data['content'].split(',')[1]
            decoded = base64.b64decode(content_string)

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                tmp.write(decoded)
                temp_path = tmp.name

            # Import CSV using the EJA manager
            eja_manager = get_eja_manager()
            overwrite_flag = overwrite and "overwrite" in overwrite
            result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

            # Remove temp file
            os.unlink(temp_path)

            # Handle result
            if 'error' in result:
                return True, result['error'], "Erro na Importação", "danger", False, ""

            # Success message
            if overwrite_flag:
                message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
            else:
                message = f"Importação concluída! Adicionados: {result.get('imported', 0)}, Atualizados: {result.get('updated', 0)}, Ignorados: {result.get('skipped', 0)}."

            # Generate unique timestamp for refreshing the table
            import time
            refresh_time = str(time.time())

            return True, message, "Importação Concluída", "success", False, refresh_time

        except Exception as e:
            return True, f"Erro ao processar arquivo: {str(e)}", "Erro", "danger", False, ""

    # Open/close modal on button click
    if trigger_id == "import-csv-button":
        return False, "", "", "", not is_open, no_update

    # Default - no change
    return False, "", "", "", is_open, no_update


# Callback unificado para gerenciar todas as mensagens de status
@callback(
    [
        Output("export-status", "is_open"),
        Output("export-status", "children"),
        Output("export-status", "header"),
        Output("export-status", "color"),
        Output("import-status", "is_open"),
        Output("import-status", "children"),
        Output("import-status", "header"),
        Output("import-status", "color"),
        Output("import-refresh", "children"),
        Output("eja-delete-status", "is_open", allow_duplicate=True),
        Output("eja-delete-status", "children", allow_duplicate=True),
        Output("eja-delete-status", "header", allow_duplicate=True),
        Output("eja-delete-status", "color", allow_duplicate=True),
        Output("eja-delete-refresh", "children", allow_duplicate=True),
    ],
    [
        Input("export-button", "n_clicks"),
        Input("import-csv-button", "n_clicks"),
        Input("confirm-delete-button", "n_clicks")
    ],
    [
        State("upload-csv", "contents"),
        State("upload-csv", "filename"),
        State("overwrite-checkbox", "value"),
        State("delete-eja-id", "value")
    ],
    prevent_initial_call=True
)
def handle_all_status_messages(
    export_clicks, import_clicks, confirm_delete_clicks,
    csv_contents, csv_filename, overwrite, eja_id
):
    # Valores padrão para todos os outputs (para não alterar componentes não afetados)
    defaults = [
        False, "", "", "",  # export-status
        False, "", "", "", None,  # import-status e refresh
        False, "", "", "", None   # delete-status e refresh
    ]

    # Determinar qual input disparou o callback
    ctx = callback_context

    if not ctx.triggered:
        return defaults

    # Identificar o acionador
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Gerar timestamp para atualização quando necessário
    import time
    refresh_time = str(time.time())

    # Processar exportação CSV
    if trigger_id == "export-button" and export_clicks:
        try:
            # Exportar usando o gerenciador de EJAs
            eja_manager = get_eja_manager()
            export_path = eja_manager.export_csv()

            if export_path and os.path.exists(export_path):
                # Atualizar apenas os outputs do export-status
                results = defaults.copy()
                results[0] = True  # is_open
                results[1] = f"Dados exportados com sucesso para: {export_path}"  # children
                results[2] = "Exportação Concluída"  # header
                results[3] = "success"  # color
                return results
            else:
                results = defaults.copy()
                results[0] = True
                results[1] = f"Erro ao exportar: {export_path}"
                results[2] = "Erro"
                results[3] = "danger"
                return results
        except Exception as e:
            results = defaults.copy()
            results[0] = True
            results[1] = f"Erro ao exportar: {str(e)}"
            results[2] = "Erro"
            results[3] = "danger"
            return results

    # Processar importação CSV
    elif trigger_id == "import-csv-button" and import_clicks:
        if not csv_contents:
            results = defaults.copy()
            results[4] = True
            results[5] = "Nenhum arquivo selecionado"
            results[6] = "Erro"
            results[7] = "danger"
            return results

        try:
            # Decodificar o conteúdo do arquivo
            content_type, content_string = csv_contents.split(',')
            decoded = base64.b64decode(content_string)

            # Salvar em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp:
                temp.write(decoded)
                temp_path = temp.name

            # Importar usando o gerenciador de EJAs
            eja_manager = get_eja_manager()
            overwrite_flag = overwrite and "overwrite" in overwrite
            result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

            # Remover o arquivo temporário
            os.unlink(temp_path)

            # Verificar resultado
            if 'error' in result:
                results = defaults.copy()
                results[4] = True
                results[5] = result['error']
                results[6] = "Erro na Importação"
                results[7] = "danger"
                return results

            # Mensagem de sucesso
            if overwrite_flag:
                message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
            else:
                message = f"Importação concluída! Adicionados: {result.get('imported', 0)}, Atualizados: {result.get('updated', 0)}, Ignorados: {result.get('skipped', 0)}."

            results = defaults.copy()
            results[4] = True  # import-status.is_open
            results[5] = message  # import-status.children
            results[6] = "Importação Concluída"  # import-status.header
            results[7] = "success"  # import-status.color
            results[8] = refresh_time  # import-refresh.children
            return results

        except Exception as e:
            results = defaults.copy()
            results[4] = True
            results[5] = f"Erro ao processar arquivo: {str(e)}"
            results[6] = "Erro"
            results[7] = "danger"
            return results

    # Processar exclusão de EJA
    elif trigger_id == "confirm-delete-button" and confirm_delete_clicks and eja_id:
        # Realizar a exclusão
        eja_manager = get_eja_manager()
        success = eja_manager.delete_eja(eja_id)

        if success:
            results = defaults.copy()
            results[9] = True  # eja-delete-status.is_open
            results[10] = "EJA excluído com sucesso!"  # eja-delete-status.children
            results[11] = "Exclusão Concluída"  # eja-delete-status.header
            results[12] = "success"  # eja-delete-status.color
            results[13] = refresh_time  # eja-delete-refresh.children
            return results
        else:
            results = defaults.copy()
            results[9] = True
            results[10] = "Erro ao excluir o EJA."
            results[11] = "Erro"
            results[12] = "danger"
            return results

    # Caso padrão
    return defaults


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
            .dashboard-container {
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .dashboard-content {
                flex: 1;
                overflow: hidden;
                display: flex;
            }
            .column {
                height: 100%;
                overflow-y: auto;
                padding: 0 8px;
            }
            .eja-table-container {
                height: calc(100vh - 250px) !important;
                overflow-y: auto !important;
                max-height: none !important;
            }
            .card-body {
                display: flex;
                flex-direction: column;
            }
            .row {
                flex-shrink: 0;
            }
            /* Estilos Bootstrap 5 */
            .me-2 {
                margin-right: 0.5rem !important;
            }
            .ms-2 {
                margin-left: 0.5rem !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
