# layouts/header.py
# Layout do cabeçalho do dashboard com estilo moderno
from dash import html
from dash import dcc
from config.config import colors


def create_header(current_month, current_day):
    """
    Cria o layout do cabeçalho do dashboard com estilo moderno

    Args:
        current_month (str): Mês atual
        current_day (str): Dia atual

    Returns:
        dash.html.Div: Layout do cabeçalho
    """
    return html.Div(
        className='header',
        children=[
            html.Div([
                html.Img(
                    src='https://www.ford.com.br/content/dam/guxeu/rhd/central/brand/ford-logo-new.svg',
                    className='logo'
                ),
                html.Div('zeentech VEV', className='header-title'),
                html.Div('TRACKS', className='header-subtitle')
            ], className='header-left'),

            html.Div(
                f"{current_month} {current_day}",
                className='header-date'
            )
        ]
    )


def create_summary_metrics(utilization_rate, availability_rate, total_hours):
    """
    Cria métricas de resumo para exibir no topo do dashboard

    Args:
        utilization_rate (str): Taxa de utilização
        availability_rate (str): Taxa de disponibilidade
        total_hours (str): Total de horas

    Returns:
        dash.html.Div: Layout das métricas de resumo
    """
    # Criar uma barra de progresso personalizada em vez de usar dcc.Progress
    progress_bar = html.Div(
        style={
            'width': '100%',
            'backgroundColor': 'rgba(255, 255, 255, 0.3)',
            'marginTop': '10px',
            'borderRadius': '5px',
            'height': '8px',
            'position': 'relative'
        },
        children=[
            html.Div(
                style={
                    'width': '82%',  # Valor fixo para progresso
                    'backgroundColor': 'rgba(255, 255, 255, 0.9)',
                    'position': 'absolute',
                    'height': '8px',
                    'borderRadius': '5px',
                    'top': '0',
                    'left': '0'
                }
            )
        ]
    )

    return html.Div(
        className='flex-container',
        style={'marginBottom': '20px'},
        children=[
            # Métrica 1: Taxa de Utilização
            html.Div(
                className='summary-card',
                style={'background': 'linear-gradient(135deg, #1976D2, #42A5F5)'},
                children=[
                    html.Div('Utilização YTD', className='summary-title'),
                    html.Div(utilization_rate, className='summary-value'),
                    html.Div('Meta: 80%', className='summary-subtitle')
                ]
            ),

            # Métrica 2: Taxa de Disponibilidade
            html.Div(
                className='summary-card',
                style={'background': 'linear-gradient(135deg, #388E3C, #66BB6A)'},
                children=[
                    html.Div('Disponibilidade YTD', className='summary-title'),
                    html.Div(availability_rate, className='summary-value'),
                    html.Div('Meta: 80%', className='summary-subtitle')
                ]
            ),

            # Métrica 3: Total de Horas
            html.Div(
                className='summary-card',
                style={'background': 'linear-gradient(135deg, #0288D1, #29B6F6)'},
                children=[
                    html.Div('Total de Horas', className='summary-title'),
                    html.Div(total_hours, className='summary-value'),
                    html.Div('Mês atual', className='summary-subtitle')
                ]
            ),

            # Métrica 4: Progresso do Mês
            html.Div(
                className='summary-card',
                style={'background': 'linear-gradient(135deg, #F57C00, #FFB74D)'},
                children=[
                    html.Div('Progresso YTD', className='summary-title'),
                    html.Div('82%', className='summary-value'),
                    html.Div('Em relação ao planejado', className='summary-subtitle'),
                    # Substitui dcc.Progress por um div personalizado
                    progress_bar
                ]
            )
        ]
    )
