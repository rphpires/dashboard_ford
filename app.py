# app.py
# Aplicação principal do dashboard zeentech VEV
import dash
from dash import html
import datetime
from layouts.header import create_header, create_summary_metrics
from layouts.left_column import create_left_column
from layouts.right_column import create_right_column
from data.mock_data import get_mock_data

# Inicializar a aplicação Dash
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    title='zeentech VEV Dashboard',
    update_title='Carregando...',
    suppress_callback_exceptions=True
)

# Obter dados mockados
dfs = get_mock_data()

# Obter data atual
current_date = datetime.datetime.now()
current_month = current_date.strftime("%B").upper()
current_day = current_date.strftime("%d")

# Definir métricas YTD
ytd_utilization_percentage = "82.5%"
ytd_availability_percentage = "88.2%"
total_hours = "1031"
total_hours_ytd = "8245"

# Layout da aplicação
app.layout = html.Div(
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
                f"zeentech VEV Dashboard • Atualizado em: {current_date.strftime('%d/%m/%Y %H:%M')}"
            ]
        )
    ]
)

# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)