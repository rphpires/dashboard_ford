# layouts/header.py
from dash import html, dcc
from data.database import get_available_months


def create_header(available_months=None,
                  title="Dashboard Ford",
                  subtitle="TRACKS",
                  month_selector_id="month-selector",
                  show_logo=True,
                  custom_right_content=None):
    """
    Cria o layout do cabeçalho do dashboard com estilo moderno e seletor de mês

    Args:
        available_months: Lista de meses disponíveis
        title: Título do header
        subtitle: Subtítulo do header
        month_selector_id: ID do seletor de mês
        show_logo: Se deve mostrar o logo da Ford
        custom_right_content: Conteúdo customizado para o lado direito (substitui o seletor de mês se fornecido)
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
                    ) if show_logo else None,
                    html.Div(title, className='header-title'),
                    html.Div(subtitle, className='header-subtitle')
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
                children=custom_right_content if custom_right_content else [
                    # Dropdown com configurações específicas para funcionamento correto
                    dcc.Dropdown(
                        id=month_selector_id,
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
