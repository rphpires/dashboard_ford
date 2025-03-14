# layouts/eja_manager.py
# Layout para gerenciamento de EJAs
from dash import html, dcc
import dash_bootstrap_components as dbc
from data.eja_manager import EJAManager


def create_eja_manager_layout():
    """
    Cria o layout para a página de gerenciamento de EJAs com dados pré-carregados
    e suporte a paginação.

    Returns:
        dash.html.Div: Layout da página de gerenciamento de EJAs
    """
    from app import create_eja_table
    # Obter um gerenciador de EJAs para carregar dados iniciais
    eja_manager = EJAManager()
    all_ejas = eja_manager.get_all_ejas()
    classifications = eja_manager.get_all_classifications()

    # Criar layout
    return html.Div(
        className='container-fluid py-4',
        children=[
            # Elementos dummy para receber outputs dos callbacks de clique
            html.Div(id='dummy-div-edit', style={'display': 'none'}),
            html.Div(id='dummy-div-delete', style={'display': 'none'}),
            
            # Store para paginação e filtragem - inicializado com todos os EJAs
            dcc.Store(
                id='eja-data-store', 
                data={
                    'all_ejas': all_ejas,
                    'filtered_ejas': all_ejas,
                    'page_current': 0
                }
            ),
            
            # Título da página
            html.H2("Gerenciador de EJAs", className="mb-4 text-primary"),

            # Painel de pesquisa e ações
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        # Campo de pesquisa por texto
                        dbc.Col([
                            dbc.Label("Buscar por título:", html_for="search-term"),
                            dbc.Input(
                                id="search-term",
                                type="text",
                                placeholder="Digite o título do EJA...",
                                debounce=True,
                            ),
                        ], width=4),

                        # Campo de pesquisa por código EJA
                        dbc.Col([
                            dbc.Label("Buscar por EJA CODE:", html_for="search-eja-code"),
                            dbc.Input(
                                id="search-eja-code",
                                type="number",
                                placeholder="Digite o código EJA...",
                                debounce=True,
                            ),
                        ], width=3),

                        # Botão de busca
                        dbc.Col([
                            html.Div(
                                dbc.Button(
                                    "Buscar",
                                    id="search-button",
                                    color="primary",
                                    className="mt-4"
                                ),
                                className="d-flex justify-content-start"
                            ),
                        ], width=1),

                        # Botões de ação
                        dbc.Col([
                            html.Div([
                                dbc.Button(
                                    "Adicionar EJA",
                                    id="add-eja-button",
                                    color="success",
                                    className="mt-4 me-2"
                                ),
                                dbc.Button(
                                    "Importar CSV",
                                    id="import-csv-button",
                                    color="info",
                                    className="mt-4 me-2"
                                ),
                                dbc.Button(
                                    "Exportar CSV",
                                    id="export-button",
                                    color="secondary",
                                    className="mt-4"
                                ),
                            ], className="d-flex justify-content-end")
                        ], width=4),
                    ]),
                ])
            ], className="mb-4"),

            # Tabela de resultados
            dbc.Card([
                dbc.CardHeader("Lista de EJAs"),
                dbc.CardBody([
                    # Inicialmente carregamos a tabela com a primeira página
                    html.Div(
                        id="eja-table-container",
                        children=create_eja_table(all_ejas, page_current=0)
                    ),

                    # Elemento escondido para refreshes
                    html.Div(id="eja-delete-refresh", style={"display": "none"}),
                    html.Div(id="import-refresh", style={"display": "none"}),
                ])
            ]),


            # Modal para confirmar exclusão
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Confirmar Exclusão")),
                dbc.ModalBody([
                    html.P(id="delete-confirmation-message"),
                    dbc.Input(id="delete-eja-id", type="hidden"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="cancel-delete-button", color="secondary", className="me-2"),
                    dbc.Button("Confirmar", id="confirm-delete-button", color="danger"),
                ]),
            ], id="delete-eja-modal", is_open=False),

            # Modal para importação de CSV
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Importar CSV")),
                dbc.ModalBody([
                    html.P("Selecione um arquivo CSV para importar os dados de EJA:"),
                    dcc.Upload(
                        id='upload-csv',
                        children=html.Div([
                            'Arraste e solte ou ',
                            html.A('clique para selecionar um arquivo')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px 0'
                        },
                        multiple=False
                    ),
                    dbc.Checkbox(
                        id="overwrite-checkbox",
                        label="Sobrescrever todos os dados existentes",
                        value=["overwrite"],  # Pré-selecionado
                        className="mt-3"
                    ),
                    html.P("Nota: Se não selecionado, apenas adicionará novos registros ou atualizará existentes.", className="text-muted"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="cancel-import-button", color="secondary", className="me-2"),
                    dbc.Button("Importar", id="import-button", color="primary"),
                ]),
            ], id="import-modal"),

            # Toasts para mensagens
            dbc.Toast(
                id="eja-form-status",
                header="Status",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 1999},
            ),
            dbc.Toast(
                id="eja-delete-status",
                header="Status",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 1999},
            ),
            dbc.Toast(
                id="import-status",
                header="Status da Importação",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 1999},
            ),
            dbc.Toast(
                id="export-status",
                header="Status da Exportação",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 1999},
            ),
        ]
    )
