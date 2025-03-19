# app.py
# Aplicação principal do dashboard zeentech VEV
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc  # Adicionado para componentes mais avançados
import datetime
from layouts.header import create_header, create_summary_metrics
from layouts.left_column import create_left_column
from layouts.right_column import create_right_column
from layouts.eja_manager import create_eja_manager_layout  # Nova importação
from data.database import load_dashboard_data, get_current_period_info
from data.eja_manager import EJAManager  # Importação do gerenciador de EJAs
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
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"  # Adicionar FontAwesome
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

# Layout da aplicação principal
main_layout = html.Div(
    className='dashboard-container',
    children=[
        # Cabeçalho
        create_header(current_month, current_day),

        # Métricas de resumo
        create_summary_metrics(ytd_utilization_percentage, ytd_availability_percentage, total_hours),

        # Conteúdo principal
        html.Div(
            className='dashboard-content',
            children=[
                # Coluna Esquerda
                create_left_column(
                    dfs,
                    ytd_utilization_percentage,
                    ytd_availability_percentage,
                    total_hours
                ),

                # Coluna Direita
                create_right_column(
                    dfs,
                    total_hours,
                    total_hours_ytd
                )
            ]
        ),

        # Rodapé
        html.Div(
            className='footer',
            style={
                'textAlign': 'center',
                'padding': '10px',
                'marginTop': '20px',
                'fontSize': '12px',
                'color': '#546E7A'
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
    dcc.Store(id='eja-store', data={}),  # Armazenamento client-side para estado do EJA manager
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


# Callbacks para o gerenciador de EJAs

# 1. Callback para busca de EJAs

# Modificação no callback search_ejas no arquivo app.py


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


# Callback corrigido para abrir modal de adição/edição
@app.callback(
    Output('add-eja-modal', 'is_open'),
    Output('eja-form-title', 'children'),
    Output('eja-form-submit-button', 'children'),
    Output('eja-form-id', 'value'),
    Output('eja-form-code', 'value'),
    Output('eja-form-title-input', 'value'),
    Output('eja-form-classification', 'value'),
    Output('eja-form-subclassification', 'value'),
    Input('add-eja-button', 'n_clicks'),
    Input({'type': 'edit-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('eja-form-cancel-button', 'n_clicks'),
    Input('eja-form-submit-button', 'n_clicks'),
    State('add-eja-modal', 'is_open'),
    State('eja-form-id', 'value'),
    prevent_initial_call=True
)
def toggle_add_eja_modal(add_clicks, edit_clicks, cancel_clicks, submit_clicks, is_open, current_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, "Adicionar EJA", "Adicionar", "", "", "", "", ""

    # Pegar o ID do componente que triggou o callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Se não houve clique (callback chamado por outra razão), não mudar estado
    if ctx.triggered[0]['value'] is None:
        return is_open, "Adicionar EJA", "Adicionar", "", "", "", "", ""

    # Verificar se é botão de edição
    if '{' in triggered_id:
        button_data = json.loads(triggered_id)
        if button_data.get('type') == 'edit-button':
            row_id = button_data.get('index')
            if row_id:
                # Buscar dados do EJA para edição
                eja_manager = EJAManager()
                eja = eja_manager.get_eja_by_id(row_id)
                if eja:
                    return (True,
                            "Editar EJA",
                            "Atualizar",
                            eja.get('Nº', ''),
                            eja.get('EJA CODE', ''),
                            eja.get('TITLE', ''),
                            eja.get('NEW CLASSIFICATION', ''),
                            eja.get('CLASSIFICATION', ''))

    # Caso seja o botão de adicionar, abrir modal vazio
    if triggered_id == 'add-eja-button':
        return not is_open, "Adicionar EJA", "Adicionar", "", "", "", "", ""

    # Caso de fechar o modal
    if triggered_id == 'eja-form-cancel-button' or triggered_id == 'eja-form-submit-button':
        return False, "Adicionar EJA", "Adicionar", "", "", "", "", ""

    # Padrão: não alterar o estado
    return is_open, "Adicionar EJA", "Adicionar", "", "", "", "", ""


# Callback para mostrar/ocultar botões de ação
@app.callback(
    Output({"type": "action-container", "index": dash.dependencies.MATCH}, "style"),
    Input({"type": "action-button", "index": dash.dependencies.MATCH}, "n_clicks"),
    State({"type": "action-container", "index": dash.dependencies.MATCH}, "style"),
    prevent_initial_call=True
)
def toggle_action_buttons(n_clicks, current_style):
    if n_clicks is None:
        raise PreventUpdate

    # Se o container estiver oculto, mostrar; caso contrário, ocultar
    if current_style.get("display") == "none":
        return {"display": "inline-block", "margin-top": "5px"}
    else:
        return {"display": "none"}

# 3. Callback para salvar/atualizar EJA


@app.callback(
    Output('eja-form-status', 'children'),
    Output('eja-form-status', 'is_open'),
    Output('search-button', 'n_clicks'),
    Input('eja-form-submit-button', 'n_clicks'),
    State('eja-form-id', 'value'),
    State('eja-form-code', 'value'),
    State('eja-form-title-input', 'value'),
    State('eja-form-classification', 'value'),
    State('eja-form-subclassification', 'value'),
    prevent_initial_call=True
)
def save_eja_form(n_clicks, row_id, eja_code, title, classification, subclassification):
    if n_clicks is None:
        raise PreventUpdate

    eja_manager = EJAManager()

    if not eja_code or not title or not classification:
        return "Por favor, preencha todos os campos obrigatórios.", True, dash.no_update

    try:
        eja_data = {
            'EJA CODE': int(eja_code),
            'TITLE': title,
            'NEW CLASSIFICATION': classification,
            'CLASSIFICATION': subclassification
        }

        if row_id:  # Edição
            result = eja_manager.update_eja(row_id, eja_data)
            if 'error' in result:
                return f"Erro ao atualizar: {result['error']}", True, dash.no_update
            return "EJA atualizado com sucesso!", True, 1
        else:  # Adição
            result = eja_manager.add_eja(eja_data)
            if 'error' in result:
                return f"Erro ao adicionar: {result['error']}", True, dash.no_update
            return "EJA adicionado com sucesso!", True, 1
    except Exception as e:
        return f"Erro ao processar o formulário: {str(e)}", True, dash.no_update


# Callback unificado para gerenciar a tabela de EJAs
# Este callback substitui os callbacks anteriores que atualizavam eja-table-container.children
@app.callback(
    Output('eja-table-container', 'children'),
    Output('eja-data-store', 'data'),

    # Inputs para busca
    Input('search-button', 'n_clicks'),
    Input('eja-delete-refresh', 'n_clicks'),
    Input('import-refresh', 'n_clicks'),

    # Input para paginação
    Input('eja-pagination', 'active_page'),

    # States necessários
    State('search-term', 'value'),
    State('search-eja-code', 'value'),
    State('eja-data-store', 'data'),

    # Prevenir chamada inicial
    prevent_initial_call=True
)
def update_eja_table(search_clicks, delete_refresh, import_refresh,
                     active_page, search_term, eja_code, current_data):
    """
    Callback unificado para atualizar a tabela de EJAs.
    Gerencia busca, paginação e refreshes após operações.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    # Identificar qual input acionou o callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Inicializar variáveis
    eja_manager = EJAManager()

    # Inicializar current_data se for None
    if current_data is None:
        all_ejas = eja_manager.get_all_ejas()
        current_data = {
            'all_ejas': all_ejas,
            'filtered_ejas': all_ejas,
            'page_current': 0
        }

    # Ações baseadas no input que acionou o callback
    if triggered_id in ['search-button', 'eja-delete-refresh', 'import-refresh']:
        # Recarregar todos os EJAs para ter dados atualizados
        all_ejas = eja_manager.get_all_ejas()

        # Caso de refresh ou busca sem termos
        if triggered_id in ['eja-delete-refresh', 'import-refresh'] or (
                triggered_id == 'search-button' and not search_term and not eja_code):
            # Mostrar todos os EJAs
            filtered_ejas = all_ejas
            page_current = 0  # Voltar para a primeira página

        # Caso de busca com termos específicos
        elif triggered_id == 'search-button' and (search_term or eja_code):
            # Filtrar baseado nos termos de busca
            filtered_ejas = eja_manager.search_ejas(search_term, eja_code)
            page_current = 0  # Voltar para a primeira página após busca

        # Caso padrão (não deve ocorrer)
        else:
            filtered_ejas = current_data.get('filtered_ejas', all_ejas)
            page_current = current_data.get('page_current', 0)

        # Atualizar o data store com os novos dados
        updated_data = {
            'all_ejas': all_ejas,
            'filtered_ejas': filtered_ejas,
            'page_current': page_current
        }

        # Criar e retornar a tabela com a página atual
        return create_eja_table(filtered_ejas, page_current=page_current), updated_data

    # Caso de mudança na paginação
    elif triggered_id == 'eja-pagination':
        # Ajustar para índice base 0 (UI mostra páginas a partir de 1)
        page_current = (active_page or 1) - 1

        # Atualizar o page_current no data store
        updated_data = current_data.copy()
        updated_data['page_current'] = page_current

        # Usar os dados filtrados existentes
        filtered_ejas = current_data.get('filtered_ejas', [])

        # Criar e retornar a tabela com a nova página
        return create_eja_table(filtered_ejas, page_current=page_current), updated_data

    # Caso padrão - não fazer nada
    raise dash.exceptions.PreventUpdate


# Callback corrigido para modal de exclusão
@app.callback(
    Output('delete-eja-modal', 'is_open'),
    Output('delete-eja-id', 'value'),
    Output('delete-confirmation-message', 'children'),
    Input({'type': 'delete-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('confirm-delete-button', 'n_clicks'),
    Input('cancel-delete-button', 'n_clicks'),
    State('delete-eja-modal', 'is_open'),
    State('delete-eja-id', 'value'),
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, confirm_clicks, cancel_clicks, is_open, current_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, "", ""

    # Pegar o ID do componente que triggou o callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Se não houve clique (callback chamado por outra razão), não mudar estado
    if ctx.triggered[0]['value'] is None:
        return is_open, current_id, ""

    # Verificar se é botão de exclusão
    if '{' in triggered_id:
        button_data = json.loads(triggered_id)
        if button_data.get('type') == 'delete-button':
            row_id = button_data.get('index')
            if row_id:
                # Buscar nome do EJA para confirmação
                eja_manager = EJAManager()
                eja = eja_manager.get_eja_by_id(row_id)
                if eja:
                    eja_name = eja.get('TITLE', 'sem nome')
                    return True, row_id, f"Tem certeza que deseja excluir o EJA '{eja_name}' (CODE: {eja.get('EJA CODE', '')})"

    # Fechar modal
    if triggered_id == 'cancel-delete-button':
        return False, "", ""

    # Confirmar exclusão
    if triggered_id == 'confirm-delete-button' and current_id:
        return False, "", ""

    return is_open, current_id, ""
# 5. Callback para processar exclusão


@app.callback(
    Output('eja-delete-status', 'children'),
    Output('eja-delete-status', 'is_open'),
    Output('eja-delete-refresh', 'n_clicks'),
    Input('confirm-delete-button', 'n_clicks'),
    State('delete-eja-id', 'value'),
    prevent_initial_call=True
)
def process_delete(n_clicks, row_id):
    if n_clicks is None or not row_id:
        raise PreventUpdate

    eja_manager = EJAManager()
    success = eja_manager.delete_eja(row_id)

    if success:
        # Incrementar n_clicks para acionar o refresh da tabela
        return "EJA excluído com sucesso!", True, 1
    else:
        return "Erro ao excluir o EJA.", True, dash.no_update

# Callback para abrir o modal de importação


@app.callback(
    Output('import-modal', 'is_open'),
    Input('import-csv-button', 'n_clicks'),
    Input('cancel-import-button', 'n_clicks'),
    Input('import-button', 'n_clicks'),
    State('import-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_import_modal(import_clicks, cancel_clicks, submit_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'import-csv-button':
        return True
    elif button_id in ['cancel-import-button', 'import-button']:
        return False

    return is_open

# 6. Callback para importar CSV


@app.callback(
    Output('import-status', 'children'),
    Output('import-status', 'is_open'),
    Output('import-refresh', 'n_clicks'),
    Input('import-button', 'n_clicks'),
    State('upload-csv', 'contents'),
    State('upload-csv', 'filename'),
    State('overwrite-checkbox', 'value'),
    prevent_initial_call=True
)
def import_csv(n_clicks, contents, filename, overwrite):
    if n_clicks is None or contents is None:
        raise PreventUpdate

    # Verificar se é um arquivo CSV
    if not filename.lower().endswith('.csv'):
        return "Por favor, faça upload de um arquivo CSV.", True, dash.no_update

    # Decodificar e salvar o conteúdo
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_path = temp_file.name
            temp_file.write(decoded)

        # Importar o CSV
        eja_manager = EJAManager()
        overwrite_flag = True if overwrite and overwrite[0] == 'overwrite' else False
        result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

        # Remover o arquivo temporário
        os.unlink(temp_path)

        if 'error' in result:
            return f"Erro na importação: {result['error']}", True, dash.no_update

        # Formatar mensagem de sucesso
        if overwrite_flag:
            message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
        else:
            message = (f"Importação parcial concluída! "
                       f"{result.get('imported', 0)} adicionados, "
                       f"{result.get('updated', 0)} atualizados, "
                       f"{result.get('skipped', 0)} ignorados.")

        return message, True, 1

    except Exception as e:
        return f"Erro ao processar o arquivo: {str(e)}", True, dash.no_update

# 7. Callback para exportar CSV


@app.callback(
    Output('export-status', 'children'),
    Output('export-status', 'is_open'),
    Input('export-button', 'n_clicks'),
    prevent_initial_call=True
)
def export_csv(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    try:
        eja_manager = EJAManager()
        export_path = eja_manager.export_csv()

        if 'Erro' in export_path:
            return export_path, True

        return f"Arquivo exportado com sucesso: {export_path}", True
    except Exception as e:
        return f"Erro ao exportar: {str(e)}", True

# 8. Callback para obter todas as classificações disponíveis para o dropdown


@app.callback(
    Output('eja-form-classification', 'options'),
    Input('add-eja-button', 'n_clicks'),
    Input({'type': 'edit-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
)
def get_classification_options(add_clicks, edit_clicks):
    eja_manager = EJAManager()
    classifications = eja_manager.get_all_classifications()
    return [{'label': c, 'value': c} for c in classifications]


# Callbacks para lidar com cliques nos botões de edição e exclusão
# Esses callbacks apenas atualizam um store de cliques
# para garantir que o n_clicks só seja incrementado quando houver um clique real

@app.callback(
    Output('dummy-div-edit', 'children'),
    Input({'type': 'edit-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_edit_click(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Se o valor é None, o clique não foi de um usuário
    triggered_value = ctx.triggered[0]['value']
    if triggered_value is None:
        raise PreventUpdate

    # Retornar algo apenas para satisfazer o callback
    return ""


@app.callback(
    Output('dummy-div-delete', 'children'),
    Input({'type': 'delete-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_delete_click(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Se o valor é None, o clique não foi de um usuário
    triggered_value = ctx.triggered[0]['value']
    if triggered_value is None:
        raise PreventUpdate

    # Retornar algo apenas para satisfazer o callback
    return ""


# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
