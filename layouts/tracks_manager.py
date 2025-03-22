# layouts/tracks_manager.py
# Layout para gerenciamento de Tracks com suporte a SQLite
from dash import html, dcc
import dash_bootstrap_components as dbc
from data.tracks_manager import get_tracks_manager
from utils.tracer import *


def create_track_table(tracks, page_current=0, page_size=10):
    """
    Cria uma tabela de Tracks com botões de ação de edição e exclusão com IDs melhorados
    """
    # Calcular índices para paginação
    start_idx = page_current * page_size
    end_idx = start_idx + page_size

    paged_tracks = tracks[start_idx:end_idx] if tracks else []

    # Se não houver Tracks, mostrar mensagem
    if not paged_tracks:
        return html.Div("Nenhum Track encontrado.", className="text-center my-4")

    # Cabeçalhos da tabela
    headers = ["ID", "TRACK", "PISTA", "PONTO", "AÇÕES"]

    # Criar linha de cabeçalho
    header_row = html.Tr([html.Th(h) for h in headers])

    # Criar linhas de dados
    data_rows = []
    for i, track in enumerate(paged_tracks):
        # ID da linha - importante para garantir unicidade
        row_id = track.get('id', str(i))

        # Criar botões de ação com IDs que incluem prefixos para evitar conflitos
        actions = html.Td([
            # Botão de edição - com ID exclusivo
            dbc.Button(
                html.I(className="fas fa-edit"),
                id={"type": "track-edit-button", "index": row_id, "action": "edit"},
                color="primary",
                size="sm",
                className="me-1",  # Atualizado para Bootstrap 5
                title="Editar"
            ),
            # Botão de exclusão - com ID exclusivo
            dbc.Button(
                html.I(className="fas fa-trash-alt"),
                id={"type": "track-delete-button", "index": row_id, "action": "delete"},
                color="danger",
                size="sm",
                title="Excluir"
            )
        ])

        # Criar linha da tabela
        row = html.Tr([
            html.Td(row_id),
            html.Td(track.get('TRACK', track.get('track', ''))),
            html.Td(track.get('PISTA', track.get('pista', ''))),
            html.Td(track.get('PONTO', track.get('ponto', ''))),
            actions
        ])

        data_rows.append(row)

    # Criar tabela
    table = html.Table(
        [html.Thead(header_row), html.Tbody(data_rows)],
        className="table table-striped table-bordered table-hover eja-table"  # Reaproveitamos o estilo da tabela EJA
    )

    # Calcular o número total de páginas
    total_pages = (len(tracks) - 1) // page_size + 1 if tracks else 1

    # Criar paginação
    pagination = dbc.Pagination(
        id="track-pagination",
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
        html.Div(f"Mostrando {len(paged_tracks)} de {len(tracks)} registros",
                 className="text-muted text-center mt-2")
    ])


def create_tracks_manager_layout():
    """
    Cria o layout para o gerenciador de Tracks com identificadores de botões aprimorados
    e expansão vertical adequada
    """
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader("Gerenciador de Tracks"),
            dbc.CardBody([
                # Controles de busca e botões
                dbc.Row([
                    # Coluna para o termo de busca
                    dbc.Col([
                        dbc.Label("Termo de Busca:"),
                        dbc.Input(id="track-search-term", type="text", placeholder="Digite um termo para busca...", className="mb-2")
                    ], md=4),

                    dbc.Col([
                        dbc.Label("Pista:"),
                        dbc.Input(id="track-search-pista", type="text", placeholder="Digite uma pista...", className="mb-2")
                    ], md=3),

                    # Coluna para os botões
                    dbc.Col([
                        html.Div([
                            # Botão de busca - Modificado para usar um ID exclusivo
                            dbc.Button(
                                "Buscar",
                                id={"type": "track-search-button", "action": "search"},
                                color="primary",
                                className="me-2"  # Atualizado para Bootstrap 5
                            ),

                            # Botão para adicionar Track
                            dbc.Button(
                                "Adicionar Track",
                                id="add-track-button",
                                color="success",
                                className="me-2"  # Atualizado para Bootstrap 5
                            )

                            # # Botão para exportar CSV
                            # dbc.Button(
                            #     "Exportar CSV",
                            #     id="export-track-button",
                            #     color="info",
                            #     className="me-2"  # Atualizado para Bootstrap 5
                            # ),

                            # # Botão para importar CSV
                            # dbc.Button(
                            #     "Importar CSV",
                            #     id="import-track-csv-button",
                            #     color="warning"
                            # )
                        ], className="d-flex align-items-center h-100")
                    ], md=5)
                ], className="mb-3"),

                # Container para a tabela de Tracks - Modificado para expandir verticalmente
                html.Div(
                    id="track-table-container",
                    className="track-table-container",
                    style={
                        "height": "calc(100vh - 250px)",  # Altura dinâmica baseada na altura da janela
                        "overflow-y": "auto",             # Adiciona rolagem vertical quando necessário
                        "padding-right": "5px"            # Um pouco de padding para a barra de rolagem
                    }
                ),

                # Status de exportação
                dbc.Toast(
                    id="track-export-status",
                    header="Status da Exportação",
                    is_open=False,
                    dismissable=True,
                    duration=4000,  # 4 segundos
                    style={"position": "fixed", "top": 20, "right": 20, "width": 350}
                ),

                # Status de importação
                dbc.Toast(
                    id="track-import-status",
                    header="Status da Importação",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    style={"position": "fixed", "top": 80, "right": 20, "width": 350}
                ),

                # Status de exclusão
                dbc.Toast(
                    id="track-delete-status",
                    header="Status da Exclusão",
                    is_open=False,
                    dismissable=True,
                    duration=4000,
                    style={"position": "fixed", "top": 140, "right": 20, "width": 350}
                ),

                # Status do formulário
                dbc.Toast(
                    id="track-form-status",
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
                        html.P(id="track-delete-confirmation-message"),
                        dbc.Input(id="delete-track-id", type="hidden")
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-track-delete-button", color="secondary", className="me-2"),
                        dbc.Button("Confirmar", id="confirm-track-delete-button", color="danger")
                    ])
                ], id="delete-track-modal", is_open=False),

                # Modal de importação CSV
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Importar CSV")),
                    dbc.ModalBody([
                        # Componente de upload
                        dcc.Upload(
                            id="upload-track-csv",
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
                            id="track-overwrite-checkbox",
                            label="Sobrescrever registros existentes",
                            value=["overwrite"]
                        )
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-track-import-button", color="secondary", className="me-2"),
                        dbc.Button("Importar", id="import-track-button", color="primary")
                    ])
                ], id="import-track-modal", is_open=False),

                # Modal de formulário para adicionar/editar Track
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle(id="track-form-title")),
                    dbc.ModalBody([
                        # Campo oculto para o modo do formulário
                        dbc.Input(id="track-form-mode", type="hidden", value="add"),
                        dbc.Input(id="edit-track-id", type="hidden", value=""),

                        # Campos do formulário
                        dbc.Label("Track:", html_for="track-input"),
                        dbc.Input(
                            id="track-input",
                            type="text",
                            placeholder="Digite o nome do Track",
                            className="mb-3"
                        ),

                        dbc.Label("Pista:", html_for="pista-input"),
                        dbc.Input(
                            id="pista-input",
                            type="text",
                            placeholder="Digite o nome da Pista",
                            className="mb-3"
                        ),

                        dbc.Label("Ponto:", html_for="ponto-input"),
                        dbc.Input(
                            id="ponto-input",
                            type="text",
                            placeholder="Digite o Ponto (opcional)",
                            className="mb-3"
                        )
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Cancelar", id="cancel-track-form-button", color="secondary", className="me-2"),
                        dbc.Button("Salvar", id="save-track-form-button", color="primary")
                    ])
                ], id="track-form-modal", is_open=False),
            ], style={"height": "calc(100vh - 150px)", "overflow": "hidden"})  # Dimensão fixa para o CardBody
        ], style={"height": "calc(100vh - 100px)"})  # Dimensão fixa para o Card
    ], fluid=True, style={"height": "100vh", "padding": "1rem"})  # Container com altura completa


def create_track_search_button():
    """
    Cria um botão de busca com um ID exclusivo para evitar conflitos com outros callbacks
    """
    return dbc.Button(
        "Buscar",
        id={"type": "track-search-button", "action": "search"},
        color="primary",
        className="me-2"
    )
