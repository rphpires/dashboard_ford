import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Inicializa a aplicação Dash
app = dash.Dash(__name__)

# Layout da aplicação
app.layout = html.Div([
    html.H1("Dashboard com Plotly e Dash"),
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Opção 1', 'value': 'Valor 1'},
            {'label': 'Opção 2', 'value': 'Valor 2'},
            {'label': 'Opção 3', 'value': 'Valor 3'}
        ],
        placeholder="Selecione uma opção",
    ),
    html.Br(),
    html.Div(id='output-div', style={'fontSize': 20, 'color': 'blue'})
])

# Callback para atualizar o conteúdo com base na seleção do usuário
@app.callback(
    Output('output-div', 'children'),
    Input('dropdown', 'value')
)
def update_output(selected_value):
    if selected_value:
        return f"Você selecionou: {selected_value}"
    return "Nenhuma opção selecionada"

# Executa o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)
