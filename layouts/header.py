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
