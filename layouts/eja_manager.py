# layouts/eja_manager.py
# Layout para gerenciamento de EJAs com suporte a SQLite
from dash import html, dcc
import dash_bootstrap_components as dbc
from data.eja_manager import get_eja_manager
from utils.tracer import *


def create_eja_table(ejas, page_current=0, page_size=10):
    """
    Cria uma tabela de EJAs com botões de ação de edição e exclusão com IDs melhorados
    """
    # Calcular índices para paginação
    start_idx = page_current * page_size
    end_idx = start_idx + page_size

    paged_ejas = ejas[start_idx:end_idx] if ejas else []

    # Se não houver EJAs, mostrar mensagem
    if not paged_ejas:
        return html.Div("Nenhum EJA encontrado.", className="text-center my-4")

    # Cabeçalhos da tabela
    headers = ["ID", "EJA CODE", "TITLE", "NEW CLASSIFICATION", "AÇÕES"]

    # Criar linha de cabeçalho
    header_row = html.Tr([html.Th(h) for h in headers])

    # Criar linhas de dados
    data_rows = []
    for i, eja in enumerate(paged_ejas):
        # ID da linha - importante para garantir unicidade
        row_id = eja.get('id', str(i))

        # Criar botões de ação com IDs que incluem prefixos para evitar conflitos
        actions = html.Td([
            # Botão de edição - com ID exclusivo
            dbc.Button(
                html.I(className="fas fa-edit"),
                id={"type": "edit-button", "index": row_id, "action": "edit"},
                color="primary",
                size="sm",
                className="me-1",  # Atualizado para Bootstrap 5
                title="Editar"
            ),
            # Botão de exclusão - com ID exclusivo
            dbc.Button(
                html.I(className="fas fa-trash-alt"),
                id={"type": "delete-button", "index": row_id, "action": "delete"},
                color="danger",
                size="sm",
                title="Excluir"
            )
        ])

        # Criar linha da tabela
        row = html.Tr([
            html.Td(row_id),
            html.Td(eja.get('EJA CODE', eja.get('eja_code', ''))),
            html.Td(eja.get('TITLE', eja.get('title', ''))),
            html.Td(eja.get('NEW CLASSIFICATION', eja.get('new_classification', ''))),
            actions
        ])

        data_rows.append(row)

    # Criar tabela
    table = html.Table(
        [html.Thead(header_row), html.Tbody(data_rows)],
        className="table table-striped table-bordered table-hover"
    )

    # Calcular o número total de páginas
    total_pages = (len(ejas) - 1) // page_size + 1 if ejas else 1

    # Criar paginação
    pagination = dbc.Pagination(
        id="eja-pagination",
        active_page=page_current + 1,  # +1 porque a UI é base 1, mas o código é base 0
        max_value=total_pages,
        fully_expanded=False,
        first_last=True,
        previous_next=True,
        className="mt-3 justify-content-center"
    )

    # Retornar tabela com paginação
    return html.Div([
        table,
        pagination,
        html.Div(f"Mostrando {len(paged_ejas)} de {len(ejas)} registros",
                 className="text-muted text-center mt-2")
    ])


# def create_eja_manager_layout():
#     """
#     Cria o layout para o gerenciador de EJAs com identificadores de botões aprimorados
#     """
#     return dbc.Container([
#         dbc.Card([
#             dbc.CardHeader("Gerenciador de EJAs"),
#             dbc.CardBody([
#                 # Controles de busca e botões
#                 dbc.Row([
#                     # Coluna para o termo de busca
#                     dbc.Col([
#                         dbc.Label("Termo de Busca:"),
#                         dbc.Input(id="search-term", type="text", placeholder="Digite um termo para busca...", className="mb-2")
#                     ], md=4),

#                     dbc.Col([
#                         dbc.Label("Código EJA:"),
#                         dbc.Input(id="search-eja-code", type="text", placeholder="Digite um código EJA...", className="mb-2")
#                     ], md=3),

#                     # Coluna para os botões
#                     dbc.Col([
#                         html.Div([
#                             # Botão de busca - Modificado para usar um ID exclusivo
#                             dbc.Button(
#                                 "Buscar",
#                                 id={"type": "search-button", "action": "search"},  # ID específico para evitar conflitos
#                                 color="primary",
#                                 className="mr-2"
#                             ),

#                             # Botão para adicionar EJA
#                             dbc.Button(
#                                 "Adicionar EJA",
#                                 id="add-eja-button",
#                                 color="success",
#                                 className="mr-2"
#                             ),

#                             # Botão para exportar CSV
#                             dbc.Button(
#                                 "Exportar CSV",
#                                 id="export-button",
#                                 color="info",
#                                 className="mr-2"
#                             ),

#                             # Botão para importar CSV
#                             dbc.Button(
#                                 "Importar CSV",
#                                 id="import-csv-button",
#                                 color="warning"
#                             )
#                         ], className="d-flex align-items-end h-100")
#                     ], md=5)
#                 ], className="mb-3"),

#                 # Container para a tabela de EJAs
#                 html.Div(
#                     id="eja-table-container",
#                     className="eja-table-container",
#                     style={
#                         "height": "calc(100vh - 250px)",  # Altura dinâmica baseada na altura da janela
#                         "overflow-y": "auto",             # Adiciona rolagem vertical quando necessário
#                         "padding-right": "5px"            # Um pouco de padding para a barra de rolagem
#                     }
#                 ),

#                 # Status de exportação
#                 dbc.Toast(
#                     id="export-status",
#                     header="Status da Exportação",
#                     is_open=False,
#                     dismissable=True,
#                     duration=4000,  # 4 segundos
#                     style={"position": "fixed", "top": 20, "right": 20, "width": 350}
#                 ),

#                 # Status de importação
#                 dbc.Toast(
#                     id="import-status",
#                     header="Status da Importação",
#                     is_open=False,
#                     dismissable=True,
#                     duration=4000,
#                     style={"position": "fixed", "top": 80, "right": 20, "width": 350}
#                 ),

#                 # Status de exclusão
#                 dbc.Toast(
#                     id="eja-delete-status",
#                     header="Status da Exclusão",
#                     is_open=False,
#                     dismissable=True,
#                     duration=4000,
#                     style={"position": "fixed", "top": 140, "right": 20, "width": 350}
#                 ),

#                 # Status da operação de inclusão do item
#                 dbc.Toast(
#                     id="eja-form-status",
#                     header="Status da Operação",
#                     is_open=False,
#                     dismissable=True,
#                     duration=4000,
#                     style={"position": "fixed", "top": 200, "right": 20, "width": 350}
#                 ),

#                 # Adicione o modal de confirmação de exclusão
#                 dbc.Modal([
#                     dbc.ModalHeader(dbc.ModalTitle("Confirmar Exclusão")),
#                     dbc.ModalBody([
#                         html.P(id="delete-confirmation-message"),
#                         dbc.Input(id="delete-eja-id", type="hidden")
#                     ]),
#                     dbc.ModalFooter([
#                         dbc.Button("Cancelar", id="cancel-delete-button", color="secondary", className="me-2"),
#                         dbc.Button("Confirmar", id="confirm-delete-button", color="danger")
#                     ])
#                 ], id="delete-eja-modal", is_open=False),

#                 # Modal de manipulação dos arquivos CSV
#                 dbc.Modal([
#                     dbc.ModalHeader(dbc.ModalTitle("Importar CSV")),
#                     dbc.ModalBody([
#                         # Componente de upload
#                         dcc.Upload(
#                             id="upload-csv",
#                             children=html.Div([
#                                 'Arraste e solte ou ',
#                                 html.A('Selecione um Arquivo CSV')
#                             ]),
#                             style={
#                                 'width': '100%',
#                                 'height': '60px',
#                                 'lineHeight': '60px',
#                                 'borderWidth': '1px',
#                                 'borderStyle': 'dashed',
#                                 'borderRadius': '5px',
#                                 'textAlign': 'center',
#                                 'margin': '10px 0'
#                             },
#                             multiple=False
#                         ),

#                         # Checkbox para sobrescrever
#                         dbc.Checkbox(
#                             id="overwrite-checkbox",
#                             label="Sobrescrever registros existentes",
#                             value=["overwrite"]
#                         )
#                     ]),
#                     dbc.ModalFooter([
#                         dbc.Button("Cancelar", id="cancel-import-button", color="secondary", className="me-2"),
#                         dbc.Button("Importar", id="import-button", color="primary")
#                     ])
#                 ], id="import-modal", is_open=False),

#                 # Modal de formulário para adicionar/editar EJA
#                 dbc.Modal([
#                     dbc.ModalHeader(dbc.ModalTitle(id="eja-form-title")),
#                     dbc.ModalBody([
#                         # Campo oculto para o modo do formulário
#                         dbc.Input(id="form-mode", type="hidden", value="add"),
#                         dbc.Input(id="edit-eja-id", type="hidden", value=""),

#                         # Campos do formulário
#                         dbc.Label("Código EJA:", html_for="eja-code-input"),
#                         dbc.Input(
#                             id="eja-code-input",
#                             type="text",
#                             placeholder="Digite o código do EJA",
#                             className="mb-3"
#                         ),

#                         dbc.Label("Título:", html_for="eja-title-input"),
#                         dbc.Input(
#                             id="eja-title-input",
#                             type="text",
#                             placeholder="Digite o título do EJA",
#                             className="mb-3"
#                         ),

#                         dbc.Label("Classificação:", html_for="eja-classification-input"),
#                         dbc.Input(
#                             id="eja-classification-input",
#                             type="text",
#                             placeholder="Digite a classificação do EJA",
#                             className="mb-3"
#                         )
#                     ]),
#                     dbc.ModalFooter([
#                         dbc.Button("Cancelar", id="cancel-eja-form-button", color="secondary", className="me-2"),
#                         dbc.Button("Salvar", id="save-eja-form-button", color="primary")
#                     ])
#                 ], id="eja-form-modal", is_open=False),

#             ])
#         ])
#     ], fluid=True)


def create_eja_manager_layout():
    """
    Cria o layout para o gerenciador de EJAs com identificadores de botões aprimorados
    e expansão vertical adequada
    """
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader("Gerenciador de EJAs"),
            dbc.CardBody([
                # Controles de busca e botões
                dbc.Row([
                    # Coluna para o termo de busca
                    dbc.Col([
                        dbc.Label("Termo de Busca:"),
                        dbc.Input(id="search-term", type="text", placeholder="Digite um termo para busca...", className="mb-2")
                    ], md=4),

                    dbc.Col([
                        dbc.Label("Código EJA:"),
                        dbc.Input(id="search-eja-code", type="text", placeholder="Digite um código EJA...", className="mb-2")
                    ], md=3),

                    # Coluna para os botões
                    dbc.Col([
                        html.Div([
                            # Botão de busca - Modificado para usar um ID exclusivo
                            dbc.Button(
                                "Buscar",
                                id={"type": "search-button", "action": "search"},
                                color="primary",
                                className="me-2"  # Atualizado para Bootstrap 5
                            ),

                            # Botão para adicionar EJA
                            dbc.Button(
                                "Adicionar EJA",
                                id="add-eja-button",
                                color="success",
                                className="me-2"  # Atualizado para Bootstrap 5
                            ),

                            # Botão para exportar CSV
                            dbc.Button(
                                "Exportar CSV",
                                id="export-button",
                                color="info",
                                className="me-2"  # Atualizado para Bootstrap 5
                            ),

                            # Botão para importar CSV
                            dbc.Button(
                                "Importar CSV",
                                id="import-csv-button",
                                color="warning"
                            )
                        ], className="d-flex align-items-center h-100")
                    ], md=5)
                ], className="mb-3"),

                # Container para a tabela de EJAs - Modificado para expandir verticalmente
                html.Div(
                    id="eja-table-container",
                    className="eja-table-container",
                    style={
                        "height": "calc(100vh - 250px)",  # Altura dinâmica baseada na altura da janela
                        "overflow-y": "auto",             # Adiciona rolagem vertical quando necessário
                        "padding-right": "5px"            # Um pouco de padding para a barra de rolagem
                    }
                ),

                # Status de exportação
                dbc.Toast(
                    id="export-status",
                    header="Status da Exportação",
                    is_open=False,
                    dismissable=True,
                    duration=4000,  # 4 segundos
                    style={"position": "fixed", "top": 20, "right": 20, "width": 350}
                ),

                # Status de importação
                dbc.Toast(
                    id="import-status",
                    header="Status da Importação",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    style={"position": "fixed", "top": 80, "right": 20, "width": 350}
                ),

                # Status de exclusão
                dbc.Toast(
                    id="eja-delete-status",
                    header="Status da Exclusão",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    style={"position": "fixed", "top": 140, "right": 20, "width": 350}
                ),

                # Status do formulário
                dbc.Toast(
                    id="eja-form-status",
                    header="Status da Operação",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    style={"position": "fixed", "top": 200, "right": 20, "width": 350}
                ),

                # Adicione o modal de confirmação de exclusão
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Confirmar Exclusão")),
                    dbc.ModalBody([
                        html.P(id="delete-confirmation-message"),
                        dbc.Input(id="delete-eja-id", type="hidden")
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-delete-button", color="secondary", className="me-2"),
                        dbc.Button("Confirmar", id="confirm-delete-button", color="danger")
                    ])
                ], id="delete-eja-modal", is_open=False),

                # Modal de importação CSV
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Importar CSV")),
                    dbc.ModalBody([
                        # Componente de upload
                        dcc.Upload(
                            id="upload-csv",
                            children=html.Div([
                                'Arraste e solte ou ',
                                html.A('Selecione um Arquivo CSV')
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

                        # Checkbox para sobrescrever
                        dbc.Checkbox(
                            id="overwrite-checkbox",
                            label="Sobrescrever registros existentes",
                            value=["overwrite"]
                        )
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-import-button", color="secondary", className="me-2"),
                        dbc.Button("Importar", id="import-button", color="primary")
                    ])
                ], id="import-modal", is_open=False),

                # Modal de formulário para adicionar/editar EJA
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle(id="eja-form-title")),
                    dbc.ModalBody([
                        # Campo oculto para o modo do formulário
                        dbc.Input(id="form-mode", type="hidden", value="add"),
                        dbc.Input(id="edit-eja-id", type="hidden", value=""),

                        # Campos do formulário
                        dbc.Label("Código EJA:", html_for="eja-code-input"),
                        dbc.Input(
                            id="eja-code-input",
                            type="text",
                            placeholder="Digite o código do EJA",
                            className="mb-3"
                        ),

                        dbc.Label("Título:", html_for="eja-title-input"),
                        dbc.Input(
                            id="eja-title-input",
                            type="text",
                            placeholder="Digite o título do EJA",
                            className="mb-3"
                        ),

                        dbc.Label("Classificação:", html_for="eja-classification-input"),
                        dbc.Input(
                            id="eja-classification-input",
                            type="text",
                            placeholder="Digite a classificação do EJA",
                            className="mb-3"
                        )
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-eja-form-button", color="secondary", className="me-2"),
                        dbc.Button("Salvar", id="save-eja-form-button", color="primary")
                    ])
                ], id="eja-form-modal", is_open=False),
            ], style={"height": "calc(100vh - 150px)", "overflow": "hidden"})  # Dimensão fixa para o CardBody
        ], style={"height": "calc(100vh - 100px)"})  # Dimensão fixa para o Card
    ], fluid=True, style={"height": "100vh", "padding": "1rem"})  # Container com altura completa
