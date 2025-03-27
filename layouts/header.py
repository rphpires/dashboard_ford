# layouts/header.py
from dash import html, dcc
from config.config import colors
from data.database import get_available_months


# Corrija a definição do dropdown no header
# def create_header(current_month, current_day, available_months=None):
#     """
#     Cria o layout do cabeçalho do dashboard com estilo moderno e seletor de mês
#     """
#     if available_months is None:
#         available_months = get_available_months(20)

#     # Converter para o formato esperado pelo dropdown
#     dropdown_options = [{'label': month['display'], 'value': month['value']}
#                         for month in available_months]

#     # Valor padrão para o dropdown (mês atual)
#     default_value = dropdown_options[0]['value'] if dropdown_options else None

#     return html.Div(
#         className='header',
#         style={
#             'position': 'relative',
#             'zIndex': 100,
#             'overflow': 'visible',
#             'padding': '6px 15px',  # Padding uniforme
#             'display': 'flex',      # Flexbox para alinhamento
#             'alignItems': 'center'  # Centraliza verticalmente todos os itens
#         },
#         children=[
#             html.Div([
#                 html.Img(
#                     src='https://www.ford.com.br/content/dam/guxeu/rhd/central/brand/ford-logo-new.svg',
#                     className='logo'
#                 ),
#                 html.Div('zeentech VEV', className='header-title'),
#                 html.Div('TRACKS', className='header-subtitle')
#             ],
#                 className='header-left',
#                 style={
#                 'display': 'flex',
#                 'alignItems': 'center'
#             }),
#             html.Div([
#                 # Simplifique o dropdown para eliminar problemas
#                 dcc.Dropdown(
#                     id='month-selector',
#                     options=dropdown_options,
#                     value=default_value,
#                     clearable=False,
#                     style={
#                         'width': '200px',
#                         'color': '#333',
#                         'backgroundColor': 'white',
#                         'fontFamily': 'Arial, sans-serif',
#                         'fontSize': '14px',
#                         'zIndex': '1000',  # Importante para garantir que o dropdown apareça na frente
#                         'height': '10px',  # Altura fixa para melhor controle
#                         'margin': '0'      # Remove margens
#                     }
#                 ),

#                 html.Div(
#                     id='header-date-display',
#                     style={'display': 'none'}
#                 )
#             ],
#                 className='header-right',
#                 style={
#                 'display': 'flex',
#                 'alignItems': 'row',  # Centralização vertical
#                 'height': '100%'         # Garante altura total
#             })
#         ]
#     )


def create_header(current_month, current_day, available_months=None):
    """
    Cria o layout do cabeçalho do dashboard com estilo moderno e seletor de mês
    """
    if available_months is None:
        available_months = get_available_months(20)

    # Converter para o formato esperado pelo dropdown
    dropdown_options = [{'label': month['display'], 'value': month['value']}
                        for month in available_months]

    # Valor padrão para o dropdown (mês atual)
    default_value = dropdown_options[0]['value'] if dropdown_options else None

    return html.Div(
        className='header',
        style={
            'position': 'relative',
            'zIndex': 100,
            'overflow': 'visible'
        },
        children=[
            # Lado esquerdo do header
            html.Div(
                className='header-left',
                children=[
                    html.Img(
                        src='https://www.ford.com.br/content/dam/guxeu/rhd/central/brand/ford-logo-new.svg',
                        className='logo'
                    ),
                    html.Div('zeentech VEV', className='header-title'),
                    html.Div('TRACKS', className='header-subtitle')
                ]
            ),
            
            # Lado direito do header
            html.Div(
                className='header-right',
                style={
                    'position': 'relative',
                    'overflow': 'visible',
                    'display': 'flex',
                    'alignItems': 'center',
                    'height': '100%'
                },
                children=[
                    # Dropdown com configurações específicas para funcionamento correto
                    dcc.Dropdown(
                        id='month-selector',
                        options=dropdown_options,
                        value=default_value,
                        clearable=False,
                        className='standard-dropdown',
                        style={
                            'width': '180px', 
                            'zIndex': 101,
                            'position': 'relative'
                        }
                    ),
                    
                    # Display de data (invisível)
                    html.Div(
                        id='header-date-display',
                        style={'display': 'none'}
                    )
                ]
            )
        ]
    )