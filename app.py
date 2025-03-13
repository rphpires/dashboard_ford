# app.py
# Aplicação principal do dashboard zeentech VEV
import dash
from dash import html
import datetime
from layouts.header import create_header, create_summary_metrics
from layouts.left_column import create_left_column
from layouts.right_column import create_right_column
from data.database import load_dashboard_data, get_current_period_info

# Inicializar a aplicação Dash
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    title='Ford Dashboard',
    update_title='Carregando...',
    suppress_callback_exceptions=True
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
                f"zeentech VEV Dashboard • Atualizado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ]
        )
    ]
)

# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
