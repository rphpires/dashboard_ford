# app.py
import os
import base64
import json
import tempfile
import threading

from datetime import datetime as dt

import dash
import dash_bootstrap_components as dbc
import pandas as pd

from dash import html, dcc, Input, Output, State, callback, no_update, callback_context
from dash.exceptions import PreventUpdate
from dash.long_callback import DiskcacheLongCallbackManager
import diskcache

from utils.tracer import *
from utils.helpers import *

from layouts.header import create_header
from layouts.left_column import create_utilization_availability_column
from layouts.center_column import create_tracks_areas_column
from layouts.right_column import create_optimized_utilization_breakdown
from layouts.eja_manager import create_eja_manager_layout, get_eja_manager, create_eja_table
from layouts.tracks_usage_manager import create_tracks_usage_manager_layout

from data.database import get_available_months, load_dashboard_data
from data.weekly_processor import setup_scheduler, check_and_process_if_needed


cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

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


# Definição inicial do layout com navegação por abas
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='eja-store', data={}),
    dcc.Store(id='eja-data-store', data={}),
    html.Div(id='dummy-div-edit', style={'display': 'none'}),
    html.Div(id='dummy-div-delete', style={'display': 'none'}),
    html.Div(id='eja-delete-refresh', style={'display': 'none'}),
    html.Div(id='import-refresh', style={'display': 'none'}),
    html.Div(id='resize-trigger', style={'display': 'none'}),

    # Overlay de carregamento global
    html.Div(
        id='loading-overlay',
        style={
            'display': 'none',
            'position': 'fixed',
            'width': '100%',
            'height': '100%',
            'top': '0',
            'left': '0',
            'backgroundColor': 'rgba(0, 0, 0, 0.5)',
            'zIndex': '9999',
            'alignItems': 'center',
            'justifyContent': 'center'
        },
        children=[
            html.Div(
                style={
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '5px',
                    'textAlign': 'center'
                },
                children=[
                    dcc.Loading(
                        type="circle",
                        color="#007bff",
                        children=html.Div("Carregando dados...", style={'marginTop': '10px'})
                    )
                ]
            )
        ]
    ),
    html.Div(id='loading-trigger', style={'display': 'none'}),

    # Header
    html.Div([
        dbc.Row([
            # Coluna da esquerda para as abas (ocupa 9/12 do espaço)
            dbc.Col([
                dbc.Tabs(
                    id='tabs',
                    children=[
                        dbc.Tab(label='Dashboard', tab_id='tab-dashboard'),
                        dbc.Tab(label='Gerenciar EJAs', tab_id='tab-eja-manager'),
                        dbc.Tab(label='Gerenciar Métricas', tab_id='tab-metrics-manager'),
                    ],
                    active_tab='tab-dashboard',
                ),
            ], width=9),

            # Coluna da direita para o logo (ocupa 3/12 do espaço)
            dbc.Col([
                html.Img(
                    src='/assets/r3s_logo.ico',  # Caminho para seu logo
                    height='60px',              # Altura aumentada
                    style={
                        'float': 'right',
                        'max-width': '100%'
                    }
                )
            ], width=3, className='d-flex align-items-center justify-content-end'),
        ], className='align-items-center'),  # Centraliza verticalmente os itens na linha
    ]),

    # Dashboard Content
    html.Div(id='tab-content', className='tabs-content-container'),

    # Footer
    html.Div(
        className='footer',
        children=[
            f"Dashboard • Atualizado em: {dt.now().strftime('%d/%m/%Y %H:%M')}"
        ]
    )
])


# Construção do layout principal do dashboard
main_layout = html.Div(
    id='dashboard-container',
    className='dashboard-container full-screen',
    style={'height': '100vh', 'overflow': 'hidden'},
    children=[
        # Header
        create_header(get_available_months(20)),

        # Body
        html.Div(
            id='dashboard-content',
            className='dashboard-content three-column-layout',
            style={
                'marginTop': '5px',  # Adicione margem para separar do header
                'paddingBottom': '5px',  # Espaço para o footer
                'maxHeight': 'calc(100vh - 80px)'  # Altura restrita para não sobrepor o footer
            },
            children=[html.Div("Selecione um mês para carregar os dados...", className="loading-message")]
        ),

        # Footer
        html.Div(
            className='footer',
            style={
                'position': 'fixed',
                'bottom': '0',
                'left': '0',
                'width': '100%',
                'backgroundColor': '#f8f9fa',
                'borderTop': '1px solid #e9ecef',
                'textAlign': 'center',
                'padding': '3px 0',
                'zIndex': '1000',
                'height': '25px'
            },
            children=[
                f"Dashboard • Atualizado em: {dt.now().strftime('%d/%m/%Y %H:%M')}"
            ]
        ),

        # Armazenamento de dados
        dcc.Store(id='dashboard-data-store')
    ]
)


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


app.clientside_callback(
    """
    function(value) {
        if (value) {
            document.getElementById('loading-overlay').style.display = 'flex';
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('loading-trigger', 'children'),
    Input('month-selector', 'value'),
    prevent_initial_call=True
)


app.clientside_callback(
    """
    function(trigger) {
        // Esta função é executada após o elemento dashboard-rendered-trigger ser adicionado ao DOM,
        // o que significa que o dashboard foi completamente renderizado

        // Definir um pequeno atraso para garantir que todos os gráficos tenham sido renderizados
        setTimeout(function() {
            // Esconder o overlay após o atraso
            var overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
        }, 500); // 500ms de atraso para garantir que os gráficos foram renderizados

        return '';
    }
    """,
    Output('loading-trigger', 'children', allow_duplicate=True),
    Input('dashboard-rendered-trigger', 'children'),
    prevent_initial_call=True
)


@app.callback(
    [
        Output('dashboard-data-store', 'data'),
        Output('header-date-display', 'children'),
        Output('loading-overlay', 'style')
    ],
    [Input('month-selector', 'value')]
)
def load_month_data(selected_month_value):
    """Callback para carregar dados do mês selecionado"""
    # Para debugging
    print(f"Valor selecionado no dropdown: {selected_month_value}")

    # Estilo para mostrar o overlay de carregamento
    loading_style = {
        'display': 'flex',
        'position': 'fixed',
        'width': '100%',
        'height': '100%',
        'top': '0',
        'left': '0',
        'backgroundColor': 'rgba(0, 0, 0, 0.5)',
        'zIndex': '9999',
        'alignItems': 'center',
        'justifyContent': 'center'
    }

    # Estilo para esconder o overlay
    hidden_style = {
        'display': 'none',
        'position': 'fixed',
        'width': '100%',
        'height': '100%',
        'top': '0',
        'left': '0',
        'backgroundColor': 'rgba(0, 0, 0, 0.5)',
        'zIndex': '9999',
        'alignItems': 'center',
        'justifyContent': 'center'
    }

    if not selected_month_value:
        # Retornar dados vazios se nenhum valor for selecionado
        empty_data = {
            'status': 'no_selection',
            'message': 'Nenhum mês selecionado'
        }
        return empty_data, "Selecione um mês", hidden_style

    try:
        # Extrair datas do valor selecionado (formato: "YYYY-MM-DD|YYYY-MM-DD")
        start_date_str, end_date_str = selected_month_value.split('|')

        # Formatar para exibição
        display_date = dt.strptime(start_date_str, '%Y-%m-%d')
        header_display = f"{display_date.strftime('%B').upper()} {display_date.day}"

        # Criar dados para o store com as datas de início e fim
        data = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'display_month': display_date.strftime('%B').upper(),
            'display_day': display_date.day
        }

        print(f"Período selecionado: {start_date_str} até {end_date_str}")
        return data, header_display, loading_style

    except Exception as e:
        # Em caso de erro, retornar dados de erro
        error_message = str(e)
        print(f"Erro no callback do seletor de mês: {error_message}")
        error_data = {
            'status': 'error',
            'message': f'Erro: {error_message}'
        }
        return error_data, f"Erro: {error_message[:20]}...", hidden_style


@app.callback(
    [
        Output('dashboard-content', 'children'),
        Output('loading-overlay', 'style', allow_duplicate=True)
    ],
    [Input('dashboard-data-store', 'data')],
    prevent_initial_call=True
)
def update_dashboard_content(data):
    """Callback para atualizar o conteúdo do dashboard e controlar o overlay de carregamento"""
    # Estilo para esconder o overlay
    hidden_style = {
        'display': 'none',
        'position': 'fixed',
        'width': '100%',
        'height': '100%',
        'top': '0',
        'left': '0',
        'backgroundColor': 'rgba(0, 0, 0, 0.5)',
        'zIndex': '9999',
        'alignItems': 'center',
        'justifyContent': 'center'
    }

    if not data:
        # Caso não haja dados, exibir mensagem
        return html.Div("Selecione um mês para carregar os dados...", className="loading-message"), hidden_style

    # Verificar se há erro nos dados
    if 'status' in data and data['status'] == 'error':
        return html.Div(f"Erro ao carregar dados: {data.get('message', 'Erro desconhecido')}",
                        className="error-message"), hidden_style

    tracks_data = {}
    periodo_info = {}
    try:
        # Carregar os dados novamente com base nas datas armazenadas
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date or not end_date:
            return html.Div("Datas inválidas. Selecione um período válido.",
                            className="error-message"), hidden_style

        print(f"Carregando dados para o período: {start_date} até {end_date}")

        # Tentar carregar os dados, com tratamento para erro
        try:
            result = load_dashboard_data(start_date, end_date)

            # Desempacotar o resultado
            dfs, tracks_data, areas_data_df, periodo_info = result

        except Exception as e:
            # Capturar qualquer erro durante o carregamento de dados
            print(f"Erro ao carregar dados: {str(e)}")
            print(traceback.format_exc())

            dfs, tracks_data, areas_data_df, periodo_info = None, None, None, None

        # Garantir que tracks_data não é None antes de passar para create_tracks_graph
        if tracks_data is None:
            tracks_data = {}  # Usar um dicionário vazio se tracks_data for None
            print("Aviso: tracks_data é None, usando dicionário vazio como fallback")

        # Garantir que areas_data_df não é None antes de passar para create_areas_graph
        if areas_data_df is None:
            _, _, areas_data_df, _ = None, None, None, None
            print("Aviso: areas_data_df é None, usando dados simulados como fallback")

        # Extrair informações do período com fallbacks seguros
        if periodo_info is None:
            periodo_info = {}
            print("Aviso: periodo_info é None, usando dicionário vazio como fallback")

        ytd_utilization_percentage = periodo_info.get('ytd_utilization_percentage', '0%')
        ytd_availability_percentage = periodo_info.get('ytd_availability_percentage', '0%')
        total_hours = periodo_info.get('total_hours', '0')
        total_hours_ytd = periodo_info.get('total_hours_ytd', '0')

        print(
            f"Valores extraídos: ytd_util={ytd_utilization_percentage}, ytd_avail={ytd_availability_percentage}, total_hours={total_hours}, total_hours_ytd={total_hours_ytd}")

        # Garantir que dfs tem todas as chaves necessárias
        required_keys = ['utilization', 'availability', 'programs', 'other_skills',
                         'internal_users', 'external_sales', 'customers_ytd']

        for key in required_keys:
            if key not in dfs:
                print(f"Aviso: chave '{key}' ausente em dfs, adicionando DataFrame vazio")
                dfs[key] = pd.DataFrame()

        dfs['tracks_data'] = tracks_data
        dfs['areas_data_df'] = areas_data_df

        # Criar o layout de três colunas
        dashboard_content = html.Div(
            className='dashboard-content three-column-layout',
            children=[
                # Coluna 1 [Left]: Utilização e Disponibilidade
                html.Div(
                    className='column column-small',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
                        'paddingBottom': '5px',
                    },
                    children=create_utilization_availability_column(
                        dfs,
                        ytd_utilization_percentage,
                        ytd_availability_percentage
                    )
                ),

                # Coluna 2 [Center]: Utilização por Tracks, Áreas e Clientes
                html.Div(
                    className='column column-medium',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
                        'paddingBottom': '5px',
                    },
                    children=create_tracks_areas_column(
                        dfs,
                        total_hours,
                        total_hours_ytd
                    )
                ),

                # Coluna 3 [Right]: Detalhamento de Utilização
                html.Div(
                    className='column column-large',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
                        'paddingBottom': '5px',
                    },
                    children=[
                        create_optimized_utilization_breakdown(
                            dfs,
                            total_hours
                        )
                    ]
                ),

                # pelo callback clientside para detectar quando o dashboard terminou de renderizar
                html.Div(id='dashboard-rendered-trigger', style={'display': 'none'})
            ]
        )

        # O overlay será escondido pelo callback clientside quando o dashboard estiver completamente renderizado
        return dashboard_content, no_update

    except Exception as e:
        print(f"Erro ao atualizar conteúdo do dashboard: {e}")
        print(traceback.format_exc())
        return html.Div([
            html.H4("Erro ao renderizar dashboard:"),
            html.Pre(str(e)),
            html.Hr(),
            html.P("Detalhes técnicos:"),
            html.Pre(traceback.format_exc())
        ], className="error-message"), hidden_style


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
    elif active_tab == 'tab-metrics-manager':
        return create_tracks_usage_manager_layout()

    return html.Div("Conteúdo não encontrado")


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


@app.callback(
    Output("track-table-container", "children"),
    Output("track-data-store", "data"),
    [
        Input({"type": "track-search-button", "action": "search"}, "n_clicks"),
        Input("track-delete-refresh", "children"),
        Input("track-pagination", "active_page")
    ],
    [
        State("track-search-year", "value"),
        State("track-search-month", "value"),
        State("track-data-store", "data")
    ],
    prevent_initial_call=True
)
def update_track_table(
    search_clicks, delete_refresh, active_page,
    search_year, search_month, data_store
):
    """Callback para atualizar a tabela de track availability"""
    # Determinar qual input acionou o callback
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Identificar o acionador
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Carregar o gerenciador
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()

    # Processar com base no acionador
    if trigger_id == '{"type":"track-search-button","action":"search"}' and search_clicks:
        # Buscar tracks
        filtered_tracks = manager.search_tracks(
            year=int(search_year) if search_year else None,
            month=int(search_month) if search_month else None
        )

        # Atualizar o data store
        data_store['filtered_tracks'] = filtered_tracks
        data_store['page_current'] = 0

        from layouts.tracks_usage_manager import create_tracks_table
        return create_tracks_table(filtered_tracks, page_current=0), data_store

    elif trigger_id == "track-delete-refresh":
        # Atualizar após exclusão
        all_tracks = manager.get_all_tracks()

        # Atualizar o data store
        data_store['filtered_tracks'] = all_tracks
        data_store['page_current'] = 0

        from layouts.tracks_usage_manager import create_tracks_table
        return create_tracks_table(all_tracks, page_current=0), data_store

    elif trigger_id == "track-pagination":
        # Atualização de paginação
        if not active_page:
            raise PreventUpdate

        # Ajustar página (UI é base 1, código é base 0)
        page_current = active_page - 1
        data_store['page_current'] = page_current

        # Usar os dados filtrados atuais
        filtered_tracks = data_store.get('filtered_tracks', [])
        if not filtered_tracks:
            filtered_tracks = manager.get_all_tracks()
            data_store['filtered_tracks'] = filtered_tracks

        from layouts.tracks_usage_manager import create_tracks_table
        return create_tracks_table(filtered_tracks, page_current=page_current), data_store

    # Caso padrão
    raise PreventUpdate


@app.callback(
    Output("track-table-container", "children", allow_duplicate=True),
    Input("tracks-usage-tabs", "active_tab"),
    prevent_initial_call=True
)
def load_initial_track_data(active_tab):
    """Carrega os dados iniciais quando a aba de track availability é selecionada"""
    if active_tab != "tab-track-availability":
        raise PreventUpdate

    # Carregar todos os tracks
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()
    all_tracks = manager.get_all_tracks()

    # Criar tabela
    from layouts.tracks_usage_manager import create_tracks_table
    return create_tracks_table(all_tracks, page_current=0)


@app.callback(
    [
        Output("track-form-modal", "is_open"),
        Output("track-form-title", "children"),
        Output("track-form-mode", "value"),
        Output("track-year-input", "value"),
        Output("track-month-input", "value"),
        Output("track-value-input", "value"),
        Output("track-edit-id", "value")
    ],
    [
        Input("add-track-button", "n_clicks"),
        Input("track-cancel-form-button", "n_clicks"),
        Input({"type": "track-edit-button", "index": dash.ALL}, "n_clicks"),
    ],
    [
        State("track-form-modal", "is_open"),
    ],
    prevent_initial_call=True
)
def toggle_track_form_modal(add_clicks, cancel_clicks, edit_clicks, is_open):
    """Toggle o modal de formulário de track availability"""
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Adicionar novo track
    if trigger_id == "add-track-button":
        return True, "Adicionar Novo Track Availability", "add", None, None, None, ""

    # Cancelar
    if trigger_id == "track-cancel-form-button":
        return False, "", "", None, None, None, ""

    # Editar track existente
    if isinstance(trigger_id, dict) and trigger_id.get("type") == "track-edit-button":
        track_id = trigger_id.get("index")
        if track_id:
            # Obter os dados do track para edição
            from data.tracks_usage_manager import get_tracks_usage_manager
            manager = get_tracks_usage_manager()
            track = manager.get_track_by_id(track_id)

            if track:
                return True, f"Editar Track Availability #{track_id}", "edit", track['year'], track['month'], track['value'], track_id

    # Caso padrão
    return is_open, "", "", None, None, None, ""


@app.callback(
    [
        Output("track-operation-status", "is_open"),
        Output("track-operation-status", "children"),
        Output("track-operation-status", "header"),
        Output("track-operation-status", "color"),
        Output("track-form-modal", "is_open", allow_duplicate=True),
        Output("track-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("track-save-form-button", "n_clicks"),
    [
        State("track-form-mode", "value"),
        State("track-edit-id", "value"),
        State("track-year-input", "value"),
        State("track-month-input", "value"),
        State("track-value-input", "value"),
    ],
    prevent_initial_call=True
)
def save_track_form(n_clicks, form_mode, edit_track_id, year, month, value):
    """Salva o formulário de track availability"""
    if not n_clicks:
        raise PreventUpdate

    # Validar campos obrigatórios
    if not year or not month or value is None:
        return True, "Preencha todos os campos obrigatórios.", "Erro", "danger", True, dash.no_update

    try:
        # Preparar os dados
        track_data = {
            "year": year,
            "month": month,
            "value": value
        }

        # Obter gerenciador
        from data.tracks_usage_manager import get_tracks_usage_manager
        manager = get_tracks_usage_manager()

        # Adicionar ou atualizar o track
        if form_mode == "add":
            result = manager.add_track(track_data)
            success_message = "Track availability adicionado com sucesso!"
            error_prefix = "Erro ao adicionar track availability:"
        else:  # mode == "edit"
            result = manager.update_track(edit_track_id, track_data)
            success_message = "Track availability atualizado com sucesso!"
            error_prefix = "Erro ao atualizar track availability:"

        # Verificar resultado
        if isinstance(result, dict) and result.get('error'):
            return True, f"{error_prefix} {result['error']}", "Erro", "danger", True, dash.no_update

        # Gerar timestamp para atualizar a tabela
        import time
        refresh_time = str(time.time())

        # Sucesso
        return True, success_message, "Sucesso", "success", False, refresh_time

    except Exception as e:
        return True, f"Erro: {str(e)}", "Erro", "danger", True, dash.no_update


@app.callback(
    Output("track-delete-modal", "is_open"),
    Output("track-delete-confirmation-message", "children"),
    Output("track-delete-id", "value"),
    Input({"type": "track-delete-button", "index": dash.ALL, "action": "delete"}, "n_clicks"),
    Input("track-cancel-delete-button", "n_clicks"),
    prevent_initial_call=True
)
def show_track_delete_confirmation(delete_clicks, cancel_click):
    """Exibe a confirmação de exclusão de track availability"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Botão cancelar
    if "track-cancel-delete-button" in trigger_id:
        return False, "", ""

    # Botões de exclusão
    if delete_clicks and any(click for click in delete_clicks if click):
        # Identificar qual botão foi clicado
        triggered_id = json.loads(trigger_id)
        row_id = triggered_id["index"]

        # Obter informações do track
        from data.tracks_usage_manager import get_tracks_usage_manager
        manager = get_tracks_usage_manager()
        track = manager.get_track_by_id(row_id)

        if track:
            # Criar mensagem de confirmação
            message = f"Tem certeza que deseja excluir o track availability #{row_id} ({track['year']}-{track['month']})?"
            return True, message, row_id

    # Caso padrão
    return False, "", ""


@app.callback(
    [
        Output("track-operation-status", "is_open", allow_duplicate=True),
        Output("track-operation-status", "children", allow_duplicate=True),
        Output("track-operation-status", "header", allow_duplicate=True),
        Output("track-operation-status", "color", allow_duplicate=True),
        Output("track-delete-modal", "is_open", allow_duplicate=True),
        Output("track-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("track-confirm-delete-button", "n_clicks"),
    State("track-delete-id", "value"),
    prevent_initial_call=True
)
def delete_track(confirm_click, track_id):
    """Exclui um track availability"""
    if not confirm_click or not track_id:
        raise PreventUpdate

    # Realizar a exclusão
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()
    success = manager.delete_track(track_id)

    # Gerar timestamp único para atualização da tabela
    import time
    refresh_time = str(time.time())

    if success:
        return True, "Track availability excluído com sucesso!", "Exclusão Concluída", "success", False, refresh_time
    else:
        return True, "Erro ao excluir o track availability.", "Erro", "danger", False, dash.no_update


# Callbacks para Usage Percentage

@app.callback(
    Output("usage-table-container", "children"),
    Output("usage-data-store", "data"),
    [
        Input({"type": "usage-search-button", "action": "search"}, "n_clicks"),
        Input("usage-delete-refresh", "children"),
        Input("usage-pagination", "active_page")
    ],
    [
        State("usage-search-year", "value"),
        State("usage-search-month", "value"),
        State("usage-data-store", "data")
    ],
    prevent_initial_call=True
)
def update_usage_table(
    search_clicks, delete_refresh, active_page,
    search_year, search_month, data_store
):
    """Callback para atualizar a tabela de usage percentage"""
    # Determinar qual input acionou o callback
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Identificar o acionador
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Carregar o gerenciador
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()

    # Processar com base no acionador
    if trigger_id == '{"type":"usage-search-button","action":"search"}' and search_clicks:
        # Buscar usage percentages
        filtered_usage = manager.search_usage(
            year=int(search_year) if search_year else None,
            month=int(search_month) if search_month else None
        )

        # Atualizar o data store
        data_store['filtered_usage'] = filtered_usage
        data_store['page_current'] = 0

        from layouts.tracks_usage_manager import create_usage_table
        return create_usage_table(filtered_usage, page_current=0), data_store

    elif trigger_id == "usage-delete-refresh":
        # Atualizar após exclusão
        all_usage = manager.get_all_usage()

        # Atualizar o data store
        data_store['filtered_usage'] = all_usage
        data_store['page_current'] = 0

        from layouts.tracks_usage_manager import create_usage_table
        return create_usage_table(all_usage, page_current=0), data_store

    elif trigger_id == "usage-pagination":
        # Atualização de paginação
        if not active_page:
            raise PreventUpdate

        # Ajustar página (UI é base 1, código é base 0)
        page_current = active_page - 1
        data_store['page_current'] = page_current

        # Usar os dados filtrados atuais
        filtered_usage = data_store.get('filtered_usage', [])
        if not filtered_usage:
            filtered_usage = manager.get_all_usage()
            data_store['filtered_usage'] = filtered_usage

        from layouts.tracks_usage_manager import create_usage_table
        return create_usage_table(filtered_usage, page_current=page_current), data_store

    # Caso padrão
    raise PreventUpdate


@app.callback(
    Output("usage-table-container", "children", allow_duplicate=True),
    Input("tracks-usage-tabs", "active_tab"),
    prevent_initial_call=True
)
def load_initial_usage_data(active_tab):
    """Carrega os dados iniciais quando a aba de usage percentage é selecionada"""
    if active_tab != "tab-usage-percentage":
        raise PreventUpdate

    # Carregar todos os usage percentages
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()
    all_usage = manager.get_all_usage()

    # Criar tabela
    from layouts.tracks_usage_manager import create_usage_table
    return create_usage_table(all_usage, page_current=0)


@app.callback(
    [
        Output("usage-form-modal", "is_open"),
        Output("usage-form-title", "children"),
        Output("usage-form-mode", "value"),
        Output("usage-year-input", "value"),
        Output("usage-month-input", "value"),
        Output("usage-value-input", "value"),
        Output("usage-edit-id", "value")
    ],
    [
        Input("add-usage-button", "n_clicks"),
        Input("usage-cancel-form-button", "n_clicks"),
        Input({"type": "usage-edit-button", "index": dash.ALL}, "n_clicks"),
    ],
    [
        State("usage-form-modal", "is_open"),
    ],
    prevent_initial_call=True
)
def toggle_usage_form_modal(add_clicks, cancel_clicks, edit_clicks, is_open):
    """Toggle o modal de formulário de usage percentage"""
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Adicionar novo usage
    if trigger_id == "add-usage-button":
        return True, "Adicionar Novo Usage Percentage", "add", None, None, None, ""

    # Cancelar
    if trigger_id == "usage-cancel-form-button":
        return False, "", "", None, None, None, ""

    # Editar usage existente
    if isinstance(trigger_id, dict) and trigger_id.get("type") == "usage-edit-button":
        usage_id = trigger_id.get("index")
        if usage_id:
            # Obter os dados do usage para edição
            from data.tracks_usage_manager import get_tracks_usage_manager
            manager = get_tracks_usage_manager()
            usage = manager.get_usage_by_id(usage_id)

            if usage:
                return True, f"Editar Usage Percentage #{usage_id}", "edit", usage['year'], usage['month'], usage['value'], usage_id

    # Caso padrão
    return is_open, "", "", None, None, None, ""


@app.callback(
    [
        Output("usage-operation-status", "is_open"),
        Output("usage-operation-status", "children"),
        Output("usage-operation-status", "header"),
        Output("usage-operation-status", "color"),
        Output("usage-form-modal", "is_open", allow_duplicate=True),
        Output("usage-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("usage-save-form-button", "n_clicks"),
    [
        State("usage-form-mode", "value"),
        State("usage-edit-id", "value"),
        State("usage-year-input", "value"),
        State("usage-month-input", "value"),
        State("usage-value-input", "value"),
    ],
    prevent_initial_call=True
)
def save_usage_form(n_clicks, form_mode, edit_usage_id, year, month, value):
    """Salva o formulário de usage percentage"""
    if not n_clicks:
        raise PreventUpdate

    # Validar campos obrigatórios
    if not year or not month or value is None:
        return True, "Preencha todos os campos obrigatórios.", "Erro", "danger", True, dash.no_update

    try:
        # Preparar os dados
        usage_data = {
            "year": year,
            "month": month,
            "value": value
        }

        # Obter gerenciador
        from data.tracks_usage_manager import get_tracks_usage_manager
        manager = get_tracks_usage_manager()

        # Adicionar ou atualizar o usage
        if form_mode == "add":
            result = manager.add_usage(usage_data)
            success_message = "Usage percentage adicionado com sucesso!"
            error_prefix = "Erro ao adicionar usage percentage:"
        else:  # mode == "edit"
            result = manager.update_usage(edit_usage_id, usage_data)
            success_message = "Usage percentage atualizado com sucesso!"
            error_prefix = "Erro ao atualizar usage percentage:"

        # Verificar resultado
        if isinstance(result, dict) and result.get('error'):
            return True, f"{error_prefix} {result['error']}", "Erro", "danger", True, dash.no_update

        # Gerar timestamp para atualizar a tabela
        import time
        refresh_time = str(time.time())

        # Sucesso
        return True, success_message, "Sucesso", "success", False, refresh_time

    except Exception as e:
        return True, f"Erro: {str(e)}", "Erro", "danger", True, dash.no_update


@app.callback(
    Output("usage-delete-modal", "is_open"),
    Output("usage-delete-confirmation-message", "children"),
    Output("usage-delete-id", "value"),
    Input({"type": "usage-delete-button", "index": dash.ALL, "action": "delete"}, "n_clicks"),
    Input("usage-cancel-delete-button", "n_clicks"),
    prevent_initial_call=True
)
def show_usage_delete_confirmation(delete_clicks, cancel_click):
    """Exibe a confirmação de exclusão de usage percentage"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Botão cancelar
    if "usage-cancel-delete-button" in trigger_id:
        return False, "", ""

    # Botões de exclusão
    if delete_clicks and any(click for click in delete_clicks if click):
        # Identificar qual botão foi clicado
        triggered_id = json.loads(trigger_id)
        row_id = triggered_id["index"]

        # Obter informações do usage
        from data.tracks_usage_manager import get_tracks_usage_manager
        manager = get_tracks_usage_manager()
        usage = manager.get_usage_by_id(row_id)

        if usage:
            # Criar mensagem de confirmação
            message = f"Tem certeza que deseja excluir o usage percentage #{row_id} ({usage['year']}-{usage['month']})?"
            return True, message, row_id

    # Caso padrão
    return False, "", ""


@app.callback(
    [
        Output("usage-operation-status", "is_open", allow_duplicate=True),
        Output("usage-operation-status", "children", allow_duplicate=True),
        Output("usage-operation-status", "header", allow_duplicate=True),
        Output("usage-operation-status", "color", allow_duplicate=True),
        Output("usage-delete-modal", "is_open", allow_duplicate=True),
        Output("usage-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("usage-confirm-delete-button", "n_clicks"),
    State("usage-delete-id", "value"),
    prevent_initial_call=True
)
def delete_usage(confirm_click, usage_id):
    """Exclui um usage percentage"""
    if not confirm_click or not usage_id:
        raise PreventUpdate

    # Realizar a exclusão
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()
    success = manager.delete_usage(usage_id)

    # Gerar timestamp único para atualização da tabela
    import time
    refresh_time = str(time.time())

    if success:
        return True, "Usage percentage excluído com sucesso!", "Exclusão Concluída", "success", False, refresh_time
    else:
        return True, "Erro ao excluir o usage percentage.", "Erro", "danger", False, dash.no_update


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

            /* Container principal com espaço reservado para o footer */
            .dashboard-container {
                height: calc(100vh - 35px) !important;
                max-height: calc(100vh - 35px) !important;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                padding-bottom: 35px;
            }

            /* Conteúdo principal com altura limitada */
            .dashboard-content {
                flex: 1;
                overflow: hidden;
                display: flex;
                /* Altura máxima para não sobrepor o footer */
                max-height: calc(100vh - 80px) !important;
                padding-bottom: 40px;
            }

            /* Estilo das colunas */
            .column {
                height: 100%;
                overflow-y: auto;
                padding: 0 8px;
                /* Importante: limitar a altura da coluna também */
                max-height: calc(100vh - 90px);
                padding-bottom: 40px;
            }

            /* Footer sempre na parte inferior */
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 30px; /* Altura fixa para o footer */
                background-color: #f8f9fa;
                text-align: center;
                padding: 5px 0;
                font-size: 12px;
                color: #666;
                border-top: 1px solid #e9ecef;
                z-index: 1000;
            }

            /* Garantir que o conteúdo das abas respeite o footer */
            #tab-content, .tabs-content-container {
                padding-bottom: 35px; /* Espaço para o footer */
                overflow: hidden;
                height: calc(100vh - 75px); /* header + tabs + footer */
            }

            /* Ajustes para a tabela EJA */
            .eja-table-container {
                height: calc(100vh - 270px) !important;
                overflow-y: auto !important;
                max-height: none !important;
                margin-bottom: 40px; /* Espaço extra no final */
            }

            /* Ajustes para gráficos */
            .chart-container {
                min-height: 0 !important;
                height: auto !important;
                margin-bottom: 4px !important;
            }

            /* Garantir que os conteúdos dos painéis sejam visíveis */
            .panel-content {
                height: auto !important;
                min-height: 0 !important;
                overflow: visible !important;
            }

            /* Estilos para o overlay de carregamento */
            .loading-message-container {
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }

            .loading-text {
                margin-top: 15px;
                font-weight: bold;
                color: #007bff;
            }

            /* Responsividade */
            @media (max-height: 768px) {
                .dashboard-content, .column, #tab-content, .tabs-content-container {
                    max-height: calc(100vh - 75px);
                }

                .footer {
                    height: 25px;
                    padding: 3px 0;
                }

                .dashboard-container {
                    height: calc(100vh - 30px);
                    max-height: calc(100vh - 30px);
                }
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


def init_weekly_processor():
    # Verificar se é necessário processar dados
    needs_processing = check_and_process_if_needed()
    # Configurar agendamento semanal (executar imediatamente apenas se for necessário)
    setup_scheduler(run_immediately=needs_processing)
    trace("Inicialização do processador semanal concluída", color="green")


if __name__ == '__main__':
    threading.Thread(target=init_weekly_processor, daemon=True).start()

    debug_mode = os.environ.get('DASH_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('DASH_HOST', '0.0.0.0')  # 0.0.0.0 permite acesso externo
    port = int(os.environ.get('DASH_PORT', 8050))

    app.run_server(debug=debug_mode, host=host, port=port)
    # app.run_server(debug=True)
