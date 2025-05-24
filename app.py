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
from layouts.eja_analysis import create_eja_analysis_layout, create_eja_analysis_table

from data.database import get_available_months, load_dashboard_data
from data.weekly_processor import setup_scheduler, check_and_process_if_needed
from data.database import ReportGenerator


cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)


def init_weekly_processor():
    # Verificar se é necessário processar dados
    needs_processing = check_and_process_if_needed()
    # Configurar agendamento semanal (executar imediatamente apenas se for necessário)
    setup_scheduler(run_immediately=needs_processing)
    trace("Inicialização do processador semanal concluída", color="green")


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
                        dbc.Tab(label='Análise de EJAs', tab_id='tab-eja-analysis'),
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
        dcc.Store(id='dashboard-data-store'),
        dcc.Store(id='missing-ejas-store', data=[]),
        dbc.Toast(
            id="eja-not-found-notification",
            header="⚠️ EJAs Não Cadastrados Encontrados",
            icon="warning",
            dismissable=True,
            is_open=False,
            duration=None,  # Não fecha automaticamente
            style={
                "position": "fixed",
                "top": "80px",
                "right": "20px",
                "zIndex": "9999",
                "width": "400px",
                "maxHeight": "500px",
                "overflowY": "auto"
            },
            className="border-warning",
            children=[]
        )
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
    print(f"Aba ativa: {active_tab}")  # Debug
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
    elif active_tab == 'tab-eja-analysis':
        return create_eja_analysis_layout()
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


@app.callback(
    Output("track-table-container", "children", allow_duplicate=True),
    Input("tab-content", "children"),  # Este é acionado quando o conteúdo da tab é carregado
    State("tabs", "active_tab"),
    prevent_initial_call=True
)
def load_initial_metrics_data(tab_content, active_tab):
    """
    Carrega os dados iniciais de track availability quando a aba "Gerenciar Métricas" é aberta
    """
    if active_tab != "tab-metrics-manager":
        raise PreventUpdate

    # Carregar todos os tracks
    from data.tracks_usage_manager import get_tracks_usage_manager
    manager = get_tracks_usage_manager()
    all_tracks = manager.get_all_tracks()

    # Criar tabela
    from layouts.tracks_usage_manager import create_tracks_table
    return create_tracks_table(all_tracks, page_current=0)

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

            /* Estilo para notificação de EJAs não cadastrados */
            .toast-warning {
                border-left: 5px solid #ffc107 !important;
                box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3) !important;
                animation: slideInRight 0.5s ease-out;
            }

            .toast-warning .toast-header {
                background-color: #fff3cd !important;
                border-bottom: 1px solid #ffeaa7 !important;
                font-weight: bold !important;
            }

            .border-left-warning {
                border-left: 4px solid #ffc107 !important;
                background-color: #fefefe !important;
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @media (max-width: 768px) {
                .toast-warning {
                    width: calc(100vw - 40px) !important;
                    right: 20px !important;
                    left: 20px !important;
                    max-width: none !important;
                }
            }

            /* Estilos adicionais para a nova notificação */
            .border-left-danger {
                border-left: 4px solid #dc3545 !important;
                background-color: #fff5f5 !important;
            }

            .border-left-danger:hover {
                background-color: #ffe6e6 !important;
            }

            .border-left-warning {
                border-left: 4px solid #ffc107 !important;
                background-color: #fefefe !important;
            }

            .border-left-warning:hover {
                background-color: #fff9e6 !important;
            }

            .text-danger {
                color: #dc3545 !important;
            }

            .text-warning {
                color: #856404 !important;
            }

            /* Melhorar espaçamento dos ícones */
            .me-2 {
                margin-right: 0.5rem !important;
            }

            /* Estilo para seções diferentes */
            .notification-section {
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
            }

            .notification-section.danger {
                background-color: #fff5f5;
                border: 1px solid #fecaca;
            }

            .notification-section.warning {
                background-color: #fffbeb;
                border: 1px solid #fed7aa;
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


@app.callback(
    [
        Output("analysis-month-selector", "options"),
        Output("analysis-month-selector", "value"),
        Output("analysis-classification-filter", "options")
    ],
    [
        Input("tabs", "active_tab"),
        Input("analysis-month-selector", "value")
    ]
)
def populate_analysis_filters(active_tab, dashboard_month_value):
    trace('######### populating analysis filters #########')
    """Popula os filtros quando a aba de análise é aberta"""
    if active_tab != "tab-eja-analysis":
        # Retornar valores vazios se não estiver na aba de análise
        return [], None, [{"label": "Todas", "value": "ALL"}]

    trace('######### populating analysis filters 2 #########')
    # Obter períodos disponíveis
    periods = get_available_months(20)
    period_options = [{"label": p["display"], "value": p["value"]} for p in periods]

    # Usar o valor do mês selecionado no dashboard se disponível
    selected_month = dashboard_month_value if dashboard_month_value else None

    # Obter classificações disponíveis
    eja_manager = get_eja_manager()
    classifications = eja_manager.get_all_classifications()

    classification_options = [{"label": "Todas", "value": "ALL"}]
    classification_options.extend([{"label": c, "value": c} for c in classifications if c])

    return period_options, selected_month, classification_options


@app.callback(
    Output("analyze-button", "disabled"),
    Input("analysis-month-selector", "value")
)
def enable_analyze_button(month_value):
    """Habilita o botão de análise quando um mês é selecionado"""
    return month_value is None or month_value == ""


@app.callback(
    [
        Output("eja-analysis-table-container", "children"),
        Output("eja-analysis-data-store", "data"),
        Output("analysis-status", "is_open"),
        Output("analysis-status", "children"),
        Output("analysis-status", "color"),
        Output("export-analysis-button", "disabled")
    ],
    Input("analyze-button", "n_clicks"),
    [
        State("analysis-month-selector", "value"),
        State("analysis-classification-filter", "value")
    ],
    prevent_initial_call=True
)
def analyze_eja_usage(n_clicks, month_value, classification_filter):
    """Analisa a utilização de EJAs para o período selecionado"""
    if not n_clicks or not month_value:
        raise PreventUpdate

    print('######### button clicked #########')
    try:
        # Extrair datas do período
        start_date, end_date = month_value.split('|')

        # Obter conexão com o banco
        from data.database import get_db_connection
        sql = get_db_connection()

        if not sql:
            return (
                html.Div("Erro ao conectar ao banco de dados.", className="text-center text-danger my-4"),
                {},
                True,
                "Erro ao conectar ao banco de dados",
                "danger",
                True
            )

        # Formatar datas para a stored procedure
        start_date_formatted = f"{start_date} 00:00:00.000"
        end_date_formatted = f"{end_date} 23:59:59.999"

        # Obter dados do banco
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport",
                                                       [start_date_formatted, end_date_formatted])

        if dashboard_df is None or dashboard_df.empty:
            return (
                html.Div("Nenhum dado encontrado para o período selecionado.",
                         className="text-center text-warning my-4"),
                {},
                True,
                "Nenhum dado encontrado para o período",
                "warning",
                True
            )

        # Processar dados
        report_gen = ReportGenerator(dashboard_df=dashboard_df)

        # Converter tempo para horas decimais
        dashboard_df['HorasDecimais'] = dashboard_df['StayTime'].apply(report_gen.converter_tempo_para_horas)

        # Obter todos os EJAs do banco
        eja_manager = get_eja_manager()
        all_ejas = eja_manager.get_all_ejas()

        # Criar dicionário de EJAs para lookup rápido
        eja_dict = {str(eja['eja_code']): eja for eja in all_ejas}

        # Agrupar por EJA
        eja_usage = dashboard_df.groupby('EJA')['HorasDecimais'].sum().reset_index()

        # Calcular total de horas
        total_hours = eja_usage['HorasDecimais'].sum()

        # Processar dados para análise
        analysis_data = []
        # cumulative_percentage = 0

        # Aplicar filtro de classificação primeiro
        if classification_filter != "ALL":
            # Filtrar EJAs pela classificação
            filtered_eja_codes = [
                str(eja['eja_code']) for eja in all_ejas
                if eja.get('new_classification') == classification_filter
            ]
            eja_usage = eja_usage[eja_usage['EJA'].isin(filtered_eja_codes)]
            # Recalcular total após filtro
            total_hours = eja_usage['HorasDecimais'].sum()

        # Reordenar após filtro
        eja_usage = eja_usage.sort_values('HorasDecimais', ascending=False)

        for _, row in eja_usage.iterrows():
            eja_code = str(row['EJA'])
            hours = row['HorasDecimais']
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            # cumulative_percentage += percentage

            # Obter informações do EJA
            eja_info = eja_dict.get(eja_code, {})

            # Se não encontrar o título, usar o código EJA
            if eja_info:
                title = eja_info.get('title', f'EJA {eja_code} - Não cadastrado')
            else:
                title = f'EJA {eja_code} - Não cadastrado'

            analysis_data.append({
                'eja_code': eja_code,
                'title': title,
                'classification': eja_info.get('new_classification', 'Não classificado'),
                'hours_decimal': hours,
                'hours_formatted': report_gen.format_datetime(hours),
                'percentage': percentage
            })

        # Se não houver dados após o filtro
        if not analysis_data:
            return (
                html.Div("Nenhum EJA encontrado com os filtros selecionados.",
                         className="text-center text-warning my-4"),
                {},
                True,
                "Nenhum EJA encontrado com os filtros aplicados",
                "warning",
                True
            )

        # Criar tabela
        table = create_eja_analysis_table(analysis_data, page_current=0)

        # Armazenar dados para exportação
        store_data = {
            'analysis_data': analysis_data,
            'period': month_value,
            'filter': classification_filter
        }

        # Formatar total de horas para o header
        total_hours_formatted = report_gen.format_datetime(total_hours)

        return (
            table,
            store_data,
            True,
            f"Análise concluída: {len(analysis_data)} EJAs processados",
            "success",
            False
        )

    except Exception as e:
        trace(f"Erro na análise de EJAs: {str(e)}", color="red")
        return (
            html.Div(f"Erro ao processar análise: {str(e)}", className="text-center text-danger my-4"),
            {},
            True,
            f"Erro ao processar análise: {str(e)}",
            "danger",
            True
        )


@app.callback(
    Output("eja-analysis-table-container", "children", allow_duplicate=True),
    Input("eja-analysis-pagination", "active_page"),
    State("eja-analysis-data-store", "data"),
    prevent_initial_call=True
)
def update_analysis_pagination(active_page, store_data):
    """Atualiza a tabela quando a página muda"""
    if not active_page or not store_data or 'analysis_data' not in store_data:
        raise PreventUpdate

    # Ajustar página (UI é base 1, código é base 0)
    page_current = active_page - 1

    # Recriar tabela com a nova página
    table = create_eja_analysis_table(store_data['analysis_data'], page_current=page_current)

    return table


@app.callback(
    Input("export-analysis-button", "n_clicks"),
    State("eja-analysis-data-store", "data"),
    prevent_initial_call=True
)
def export_analysis(n_clicks, store_data):
    """Exporta a análise para CSV"""
    if not n_clicks or not store_data or 'analysis_data' not in store_data:
        raise PreventUpdate

    try:
        import os
        from datetime import datetime

        # Criar DataFrame com os dados
        df = pd.DataFrame(store_data['analysis_data'])

        # Reorganizar colunas para exportação
        export_df = df[[
            'eja_code', 'title', 'classification',
            'hours_formatted', 'percentage'
        ]].copy()

        # Renomear colunas
        export_df.columns = [
            'EJA CODE', 'TÍTULO', 'CLASSIFICAÇÃO',
            'HORAS', 'PERCENTUAL (%)'
        ]

        # Formatar percentuais
        export_df['PERCENTUAL (%)'] = export_df['PERCENTUAL (%)'].apply(lambda x: f"{x:.2f}")

        # Gerar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.join(export_dir, f"eja_analysis_{timestamp}.csv")

        # Exportar para CSV
        export_df.to_csv(file_path, index=False, encoding='latin-1')

    except Exception as e:
        report_exception(e)


@app.callback(
    Output("download-analysis-csv", "data"),
    Input("export-analysis-button", "n_clicks"),
    State("eja-analysis-data-store", "data"),
    prevent_initial_call=True
)
def export_analysis_to_csv(n_clicks, store_data):
    """Exporta a análise de EJAs para CSV com download direto"""
    if not n_clicks or not store_data or 'analysis_data' not in store_data:
        raise PreventUpdate

    try:
        # Obter dados da análise
        analysis_data = store_data['analysis_data']

        # Criar DataFrame
        df = pd.DataFrame(analysis_data)

        # Renomear colunas para português
        df = df.rename(columns={
            'eja_code': 'Código EJA',
            'title': 'Título',
            'classification': 'Classificação',
            'hours_formatted': 'Horas',
            'percentage': 'Percentual (%)'
        })

        # Formatar percentuais
        df['Percentual (%)'] = df['Percentual (%)'].round(2)

        # Remover coluna hours_decimal (não necessária no export)
        if 'hours_decimal' in df.columns:
            df = df.drop('hours_decimal', axis=1)

        # Gerar nome do arquivo com timestamp
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        filename = f'analise_eja_{timestamp}.csv'

        # Retornar o download
        return dcc.send_data_frame(df.to_csv, filename, index=False, encoding='latin-1')

    except Exception as e:
        trace(f"Erro ao exportar análise: {str(e)}", color="red")
        return None


# Substitua o callback no app.py por esta versão corrigida:

@app.callback(
    [
        Output("eja-not-found-notification", "is_open"),
        Output("eja-not-found-notification", "children"),
        Output("missing-ejas-store", "data")
    ],
    [Input('dashboard-data-store', 'data')],
    prevent_initial_call=True
)
def check_missing_ejas_with_vehicle_fixed(dashboard_data):
    """Versão corrigida - cria HorasDecimais ANTES de usar"""
    if not dashboard_data or 'status' in dashboard_data:
        return False, [], []

    try:
        # Extrair datas
        start_date = dashboard_data.get('start_date')
        end_date = dashboard_data.get('end_date')

        if not start_date or not end_date:
            return False, [], []

        # Carregar dados do banco
        from data.database import get_db_connection
        sql = get_db_connection()

        if not sql:
            return False, [], []

        # Formatar datas
        start_date_formatted = f"{start_date} 00:00:00.000"
        end_date_formatted = f"{end_date} 23:59:59.999"

        # Obter dados
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport",
                                                       [start_date_formatted, end_date_formatted])

        if dashboard_df is None or dashboard_df.empty:
            return False, [], []

        print(f"DEBUG: Processando {len(dashboard_df)} registros")
        print(f"DEBUG: Colunas disponíveis: {list(dashboard_df.columns)}")

        # Verificar se as colunas necessárias existem
        if 'Vehicle' not in dashboard_df.columns:
            print("AVISO: Coluna 'Vehicle' não encontrada nos dados")
            return False, [], []

        # ====== CRIAR COLUNA HorasDecimais PRIMEIRO ======
        from data.database import ReportGenerator
        report_gen = ReportGenerator(dashboard_df=dashboard_df)
        dashboard_df['HorasDecimais'] = dashboard_df['StayTime'].apply(report_gen.converter_tempo_para_horas)

        print(f"DEBUG: Coluna HorasDecimais criada com {dashboard_df['HorasDecimais'].sum():.2f} horas totais")

        # ====== ANÁLISE DE EJA E VEHICLE ======
        def analyze_eja_vehicle(row):
            """Analisa cada linha e determina o tipo de problema"""
            eja_val = row['EJA']
            vehicle_val = row['Vehicle']

            # Processar valor do EJA
            eja_is_empty = False
            eja_clean = None

            if eja_val is None or pd.isna(eja_val):
                eja_is_empty = True
            else:
                try:
                    eja_str = str(eja_val).strip()
                    if not eja_str or eja_str.lower() in ['nan', 'none', 'null', '']:
                        eja_is_empty = True
                    else:
                        eja_clean = eja_str
                except:
                    eja_is_empty = True

            # Processar valor do Vehicle
            vehicle_clean = "N/A"
            if vehicle_val is not None and not pd.isna(vehicle_val):
                try:
                    vehicle_str = str(vehicle_val).strip()
                    if vehicle_str and vehicle_str.lower() not in ['nan', 'none', 'null', '']:
                        vehicle_clean = vehicle_str
                except:
                    pass

            return pd.Series({
                'eja_is_empty': eja_is_empty,
                'eja_clean': eja_clean,
                'vehicle_clean': vehicle_clean
            })

        # Aplicar análise (usando apply com result_type='expand' para criar múltiplas colunas)
        analysis_cols = dashboard_df.apply(analyze_eja_vehicle, axis=1)
        dashboard_df = pd.concat([dashboard_df, analysis_cols], axis=1)

        # Separar registros problemáticos
        empty_eja_df = dashboard_df[dashboard_df['eja_is_empty'] == True].copy()
        valid_eja_df = dashboard_df[dashboard_df['eja_is_empty'] == False].copy()

        print(f"DEBUG: {len(empty_eja_df)} registros com EJA vazio")
        print(f"DEBUG: {len(valid_eja_df)} registros com EJA válido")

        # Obter EJAs cadastrados
        from layouts.eja_manager import get_eja_manager
        eja_manager = get_eja_manager()
        all_ejas = eja_manager.get_all_ejas()
        ejas_cadastrados = set()

        for eja in all_ejas:
            eja_code = eja.get('eja_code')
            if eja_code is not None:
                ejas_cadastrados.add(str(eja_code).strip())

        print(f"DEBUG: {len(ejas_cadastrados)} EJAs cadastrados no sistema")

        # Preparar dados para relatório
        missing_data = []

        # ====== PROCESSAR EJAs VAZIOS (MOSTRAR VEHICLE) ======
        if not empty_eja_df.empty:
            print(f"DEBUG: Processando {len(empty_eja_df)} registros com EJA vazio")

            # Verificar se a coluna HorasDecimais existe no dataframe filtrado
            if 'HorasDecimais' not in empty_eja_df.columns:
                print("ERRO: Coluna HorasDecimais não existe no dataframe filtrado")
                return False, [], []

            # Agrupar por Vehicle
            try:
                vehicle_groups = empty_eja_df.groupby('vehicle_clean')['HorasDecimais'].sum().reset_index()
                vehicle_groups.columns = ['vehicle_clean', 'total_hours']

                print(f"DEBUG: {len(vehicle_groups)} grupos de vehicles encontrados")

                for _, row in vehicle_groups.iterrows():
                    vehicle_name = row['vehicle_clean']
                    total_hours = row['total_hours']

                    # Contar eventos para este vehicle
                    event_count = len(empty_eja_df[empty_eja_df['vehicle_clean'] == vehicle_name])

                    # Obter amostra de vehicles originais
                    original_vehicles = empty_eja_df[empty_eja_df['vehicle_clean'] == vehicle_name]['Vehicle'].unique()

                    missing_data.append({
                        'problem_type': 'eja_vazio',
                        'identifier': vehicle_name,
                        'display_title': f"Veículo: {vehicle_name}",
                        'display_subtitle': "EJA não informado",
                        'total_hours': total_hours,
                        'total_hours_formatted': report_gen.format_datetime(total_hours),
                        'event_count': event_count,
                        'additional_info': f"Variações: {', '.join(original_vehicles[:2])}" if len(original_vehicles) > 1 else "",
                        'color_class': 'border-left-danger',
                        'icon': '🚗'
                    })

                    print(f"DEBUG: Vehicle {vehicle_name}: {event_count} eventos, {total_hours:.2f} horas")

            except Exception as e:
                print(f"ERRO ao agrupar vehicles: {str(e)}")
                # Fallback: processar individualmente
                unique_vehicles = empty_eja_df['vehicle_clean'].unique()
                for vehicle_name in unique_vehicles:
                    vehicle_data = empty_eja_df[empty_eja_df['vehicle_clean'] == vehicle_name]
                    total_hours = vehicle_data['HorasDecimais'].sum()
                    event_count = len(vehicle_data)

                    missing_data.append({
                        'problem_type': 'eja_vazio',
                        'identifier': vehicle_name,
                        'display_title': f"Veículo: {vehicle_name}",
                        'display_subtitle': "EJA não informado",
                        'total_hours': total_hours,
                        'total_hours_formatted': report_gen.format_datetime(total_hours),
                        'event_count': event_count,
                        'additional_info': "",
                        'color_class': 'border-left-danger',
                        'icon': '🚗'
                    })

        # ====== PROCESSAR EJAs VÁLIDOS NÃO CADASTRADOS ======
        if not valid_eja_df.empty:
            print(f"DEBUG: Processando {len(valid_eja_df)} registros com EJA válido")

            # Encontrar EJAs não cadastrados
            ejas_validos = set(str(eja) for eja in valid_eja_df['eja_clean'].unique() if eja is not None)
            ejas_nao_cadastrados = ejas_validos - ejas_cadastrados

            print(f"DEBUG: {len(ejas_nao_cadastrados)} EJAs não cadastrados encontrados")

            for eja_code in ejas_nao_cadastrados:
                eja_data = valid_eja_df[valid_eja_df['eja_clean'] == eja_code]
                total_hours = eja_data['HorasDecimais'].sum()
                event_count = len(eja_data)

                # Obter alguns vehicles que usam este EJA
                sample_vehicles = eja_data['Vehicle'].dropna().unique()[:3]
                vehicles_info = f"Ex: {', '.join(sample_vehicles)}" if len(sample_vehicles) > 0 else ""

                missing_data.append({
                    'problem_type': 'eja_nao_cadastrado',
                    'identifier': eja_code,
                    'display_title': f"EJA: {eja_code}",
                    'display_subtitle': "Não cadastrado no sistema",
                    'total_hours': total_hours,
                    'total_hours_formatted': report_gen.format_datetime(total_hours),
                    'event_count': event_count,
                    'additional_info': vehicles_info,
                    'color_class': 'border-left-warning',
                    'icon': '⚠️'
                })

                print(f"DEBUG: EJA {eja_code}: {event_count} eventos, {total_hours:.2f} horas")

        if not missing_data:
            print("DEBUG: Nenhum problema encontrado")
            return False, [], []

        # Ordenar por impacto
        missing_data.sort(key=lambda x: x['total_hours'], reverse=True)

        # Calcular totais
        total_missing_hours = sum(item['total_hours'] for item in missing_data)
        total_events = sum(item['event_count'] for item in missing_data)

        # Separar por tipo
        eja_vazios = [item for item in missing_data if item['problem_type'] == 'eja_vazio']
        eja_nao_cadastrados = [item for item in missing_data if item['problem_type'] == 'eja_nao_cadastrado']

        print(f"DEBUG: {len(eja_vazios)} veículos com EJA vazio, {len(eja_nao_cadastrados)} EJAs não cadastrados")

        # ====== CRIAR NOTIFICAÇÃO ======
        notification_content = [
            html.P([
                "Foram encontrados eventos com problemas de EJA que precisam de atenção. ",
                "Isso pode afetar a precisão dos relatórios."
            ], className="mb-3"),

            html.Hr(),

            html.P([
                html.Strong("Resumo:"),
                html.Br(),
                f"• {len(eja_vazios)} veículos com EJA não informado" if eja_vazios else "",
                html.Br() if eja_vazios else None,
                f"• {len(eja_nao_cadastrados)} EJAs não cadastrados" if eja_nao_cadastrados else "",
                html.Br() if eja_nao_cadastrados else None,
                f"• {total_events} eventos afetados",
                html.Br(),
                f"• {report_gen.format_datetime(total_missing_hours)} horas totais"
            ], className="mb-3"),

            html.Hr()
        ]

        # Seção de EJAs vazios
        if eja_vazios:
            notification_content.extend([
                html.P([
                    html.Span("🚗 ", style={"fontSize": "1.2em"}),
                    html.Strong(f"Veículos sem EJA informado ({len(eja_vazios)}):")
                ], className="mb-2 text-danger"),

                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6([
                                html.Span(item['icon'], className="me-2"),
                                item['display_title']
                            ], className="card-title mb-1"),
                            html.P(item['display_subtitle'], className="text-muted small mb-1"),
                            html.P([
                                f"Horas: {item['total_hours_formatted']} | ",
                                f"Eventos: {item['event_count']}"
                            ], className="card-text small mb-0"),
                            html.P(item['additional_info'], className="card-text text-muted small mb-0") if item.get('additional_info') else None
                        ], className="py-2")
                    ], className=f"mb-2 {item['color_class']}")
                    for item in eja_vazios[:8]
                ], style={"maxHeight": "250px", "overflowY": "auto"}),

                html.P(
                    f"... e mais {len(eja_vazios) - 8} veículos sem EJA.",
                    className="text-muted small"
                ) if len(eja_vazios) > 8 else None
            ])

        # Seção de EJAs não cadastrados
        if eja_nao_cadastrados:
            if eja_vazios:
                notification_content.append(html.Hr())

            notification_content.extend([
                html.P([
                    html.Span("⚠️ ", style={"fontSize": "1.2em"}),
                    html.Strong(f"EJAs não cadastrados ({len(eja_nao_cadastrados)}):")
                ], className="mb-2 text-warning"),

                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6([
                                html.Span(item['icon'], className="me-2"),
                                item['display_title']
                            ], className="card-title mb-1"),
                            html.P(item['display_subtitle'], className="text-muted small mb-1"),
                            html.P([
                                f"Horas: {item['total_hours_formatted']} | ",
                                f"Eventos: {item['event_count']}"
                            ], className="card-text small mb-0"),
                            html.P(item.get('additional_info', ''), className="card-text text-muted small mb-0") if item.get('additional_info') else None
                        ], className="py-2")
                    ], className=f"mb-2 {item['color_class']}")
                    for item in eja_nao_cadastrados[:8]
                ], style={"maxHeight": "250px", "overflowY": "auto"}),

                html.P(
                    f"... e mais {len(eja_nao_cadastrados) - 8} EJAs não cadastrados.",
                    className="text-muted small"
                ) if len(eja_nao_cadastrados) > 8 else None
            ])

        # Finalizar
        notification_content.extend([
            html.Hr(),

            html.P([
                html.Strong("Recomendações:"),
                html.Br(),
                "• Para veículos sem EJA: Verificar configuração no sistema de origem",
                html.Br(),
                "• Para EJAs não cadastrados: Acessar 'Gerenciar EJAs' para cadastrá-los"
            ], className="mb-2"),

            dbc.Button(
                "Ir para Gerenciar EJAs",
                id="go-to-eja-manager-btn",
                color="warning",
                size="sm",
                className="mt-2"
            )
        ])

        print(f"DEBUG: Notificação criada com {len(missing_data)} problemas")
        return True, notification_content, missing_data

    except Exception as e:
        print(f"Erro ao verificar EJAs não cadastrados: {str(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        return False, [], []


@app.callback(
    [
        Output('tabs', 'active_tab'),
        Output("eja-not-found-notification", "is_open", allow_duplicate=True)
    ],
    Input("go-to-eja-manager-btn", "n_clicks"),
    prevent_initial_call=True
)
def redirect_to_eja_manager(n_clicks):
    """Redireciona para a aba de gerenciamento de EJAs"""
    if n_clicks:
        return 'tab-eja-manager', False
    raise PreventUpdate


@app.callback(
    Output('dummy-div-edit', 'children', allow_duplicate=True),
    Input('dashboard-data-store', 'data'),
    prevent_initial_call=True
)
def diagnostic_eja_data(dashboard_data):
    """Callback para diagnosticar problemas com dados de EJA"""
    if not dashboard_data or 'status' in dashboard_data:
        return ""

    try:
        # Extrair datas
        start_date = dashboard_data.get('start_date')
        end_date = dashboard_data.get('end_date')

        if not start_date or not end_date:
            return ""

        # Carregar dados do banco
        from data.database import get_db_connection
        sql = get_db_connection()

        if not sql:
            return ""

        # Formatar datas
        start_date_formatted = f"{start_date} 00:00:00.000"
        end_date_formatted = f"{end_date} 23:59:59.999"

        # Obter dados
        dashboard_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport",
                                                       [start_date_formatted, end_date_formatted])

        if dashboard_df is None or dashboard_df.empty:
            return ""

        print("\n" + "=" * 50)
        print("DIAGNÓSTICO DOS DADOS DE EJA")
        print("=" * 50)

        print(f"Total de registros: {len(dashboard_df)}")
        print(f"Colunas disponíveis: {list(dashboard_df.columns)}")

        if 'EJA' in dashboard_df.columns:
            print(f"\n--- ANÁLISE DA COLUNA EJA ---")
            print(f"Tipo de dados: {dashboard_df['EJA'].dtype}")
            print(f"Valores únicos: {dashboard_df['EJA'].nunique()}")
            print(f"Valores nulos: {dashboard_df['EJA'].isna().sum()}")

            # Mostrar todos os valores únicos com seus tipos
            print(f"\n--- VALORES ÚNICOS NA COLUNA EJA ---")
            unique_values = dashboard_df['EJA'].unique()
            for i, val in enumerate(unique_values):
                val_type = type(val).__name__
                val_repr = repr(val)
                is_null = pd.isna(val)
                print(f"{i+1:2d}: {val_repr:15} | Tipo: {val_type:10} | Null: {is_null}")

            # Contar tipos de valores
            print(f"\n--- CONTAGEM POR TIPO ---")
            type_counts = dashboard_df['EJA'].apply(lambda x: type(x).__name__).value_counts()
            for tipo, count in type_counts.items():
                print(f"{tipo}: {count}")

            # Mostrar amostra dos dados
            print(f"\n--- AMOSTRA DOS DADOS (primeiros 10) ---")
            sample_data = dashboard_df[['EJA']].head(10)
            for idx, row in sample_data.iterrows():
                eja_val = row['EJA']
                print(f"Linha {idx}: EJA = {repr(eja_val)} (tipo: {type(eja_val).__name__})")

            # Verificar valores problemáticos
            print(f"\n--- VALORES PROBLEMÁTICOS ---")
            problematic = dashboard_df[dashboard_df['EJA'].isna() | (dashboard_df['EJA'] == '')]
            print(f"Registros com EJA nulo ou vazio: {len(problematic)}")

            if len(problematic) > 0:
                print("Primeiras 5 linhas problemáticas:")
                print(problematic[['EJA']].head().to_string())

        print("=" * 50)
        print("FIM DO DIAGNÓSTICO")
        print("=" * 50 + "\n")

        return ""

    except Exception as e:
        print(f"Erro no diagnóstico: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return ""


if __name__ == '__main__':
    threading.Thread(target=init_weekly_processor, daemon=True).start()

    debug_mode = os.environ.get('DASH_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('DASH_HOST', '0.0.0.0')  # 0.0.0.0 permite acesso externo
    port = int(os.environ.get('DASH_PORT', 8050))

    app.run_server(debug=debug_mode, host=host, port=port)
    # app.run_server(debug=True)
