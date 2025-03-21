# layouts/eja_manager.py
# Layout para gerenciamento de EJAs com suporte a SQLite
from dash import html, dcc
import dash_bootstrap_components as dbc
from data.eja_manager import EJAManager


def create_eja_table(ejas, page_current=0, page_size=15):
    """
    Cria a tabela de EJAs com paginação

    Args:
        ejas (list): Lista de EJAs
        page_current (int): Página atual
        page_size (int): Tamanho da página

    Returns:
        dash.html.Div: Layout da tabela
    """
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
        # Garantir que os valores corretos sejam usados independente da fonte (CSV ou SQLite)
        eja_id = eja.get('Nº', eja.get('id', ''))
        eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
        title = eja.get('TITLE', eja.get('title', ''))
        classification = eja.get('NEW CLASSIFICATION', eja.get('new_classification', ''))

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
            html.Td(eja_code),
            html.Td(title),
            html.Td(classification),
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


def create_eja_manager_layout():
    """
    Cria o layout para a página de gerenciamento de EJAs com dados pré-carregados
    e suporte a paginação.

    Returns:
        dash.html.Div: Layout da página de gerenciamento de EJAs
    """
    # Obter um gerenciador de EJAs para carregar dados iniciais
    eja_manager = EJAManager()
    all_ejas = eja_manager.get_all_ejas()
    # classifications = eja_manager.get_all_classifications()

    # Criar layout
    return html.Div(
        className='container-fluid py-4',
        children=[
            # Elementos dummy para receber outputs dos callbacks de clique
            html.Div(id='dummy-div-edit', style={'display': 'none'}),
            html.Div(id='dummy-div-delete', style={'display': 'none'}),
            html.Div(id='eja-delete-refresh', style={"display": "none"}),
            html.Div(id='import-refresh', style={"display": "none"}),

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

            # Banner informativo sobre SQLite - mostrado apenas quando SQLite está ativo
            dbc.Alert(
                [
                    html.I(className="fas fa-database me-2"),
                    "Os dados de EJA estão sendo armazenados em um banco de dados SQLite local para melhor desempenho."
                ],
                color="info",
                id="sqlite-info-banner",
                className="mb-4",
                style={"display": "block" if eja_manager.use_sqlite else "none"}
            ),

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
            ], id="import-modal", is_open=False),

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
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(id="eja-form-title")),
                dbc.ModalBody([
                    # Campo oculto para indicar modo (add/edit) e id em caso de edição
                    dbc.Input(id="form-mode", type="hidden"),
                    dbc.Input(id="edit-eja-id", type="hidden"),

                    # Campos do formulário
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("EJA CODE:", html_for="eja-code-input", className="required"),
                            dbc.Input(
                                id="eja-code-input",
                                type="text",
                                placeholder="Ex: 12345",
                                required=True
                            ),
                            dbc.FormFeedback(
                                "Este campo é obrigatório",
                                type="invalid",
                            ),
                        ], width=12, className="mb-3"),

                        dbc.Col([
                            dbc.Label("Título:", html_for="eja-title-input", className="required"),
                            dbc.Input(
                                id="eja-title-input",
                                type="text",
                                placeholder="Digite o título do EJA",
                                required=True
                            ),
                            dbc.FormFeedback(
                                "Este campo é obrigatório",
                                type="invalid",
                            ),
                        ], width=12, className="mb-3"),

                        dbc.Col([
                            dbc.Label("Classificação:", html_for="eja-classification-input"),
                            dbc.Input(
                                id="eja-classification-input",
                                type="text",
                                placeholder="Digite a classificação"
                            ),
                        ], width=12, className="mb-3"),

                        # Aqui você pode adicionar campos adicionais conforme necessário
                    ]),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancelar", id="cancel-eja-form-button", color="secondary", className="me-2"),
                    dbc.Button("Salvar", id="save-eja-form-button", color="primary"),
                ]),
            ], id="eja-form-modal", is_open=False, size="lg"),
        ]
    )
