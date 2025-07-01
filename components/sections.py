# components/sections.py
# Funções para criação de seções e componentes de UI do dashboard
from dash import html, dcc
from config.config import colors
from config.layout_config import layout_config


def create_section_container(children, margin_bottom='0px'):
    return html.Div(
        className='panel',
        style={'marginBottom': margin_bottom},
        children=children
    )


def create_section_header(title, value, font_size='12px'):
    return html.Div(
        className='section-title',
        children=[
            html.Div(title, className='card-title', style={'fontSize': font_size}),
            html.Div(value, className='card-total', style={'fontSize': font_size})
        ]
    )


def create_metric_header(title, value, percentage, font_size='11px'):
    return html.Div(
        className='metric-box',
        style={
            'display': 'flex',
            'width': '100%',
            'justifyContent': 'space-between'
        },
        children=[
            html.Div(
                title,
                className='metric-title',
                style={
                    'fontSize': font_size
                }
            ),
            html.Div(
                className='metric-value',
                style={
                    'fontSize': font_size
                },
                children=[
                    html.Span(f"{value} Hr"),
                    # html.Span(
                    #     f" ({percentage})",
                    #     style={
                    #         'marginLeft': '5px',
                    #         'color': '#546E7A'
                    #     }
                    # )
                ]
            )
        ]
    )


def create_graph_section(id, figure, height=None):
    return html.Div(
        className='chart-container',
        style={'height': height} if height else {},
        children=[
            dcc.Graph(
                id=id,
                figure=figure,
                config={
                    'displayModeBar': False,
                    'responsive': True
                },
                style={
                    'height': '100%'
                }
            )
        ]
    )


def create_bordered_container(children, margin_bottom='0'):
    return html.Div(
        className='chart-container',
        style={'marginBottom': margin_bottom},
        children=children
    )


def create_side_by_side_container(children):
    """
    Cria um container para elementos lado a lado

    Args:
        children (list): Lista de elementos filhos

    Returns:
        dash.html.Div: Container flexível
    """
    return html.Div(
        className='flex-container',
        children=children
    )


def create_flex_item(children, min_width='200px', margin_right='0px'):
    """Cria um item flexível para containers lado a lado em estilo moderno"""
    return html.Div(
        className='flex-item',
        style={
            'minWidth': min_width,
            'flex': '1',  # Adicionando flex: 1 para distribuir o espaço igualmente
            'marginRight': margin_right,
        },
        children=children
    )


def create_info_card(title, value, subtitle=None, icon=None, color='#1E88E5', width=None):
    """Cria um card informativo com título, valor e subtítulo opcional em estilo moderno"""
    if color is None:
        color = colors['primary']

    # Adicionar estilo específico para largura se fornecido
    style = {'padding': '15px', 'flexDirection': 'column', 'alignItems': 'flex-start'}
    if width:
        style['width'] = width

    card_content = []

    # Adiciona o título
    card_content.append(html.Div(title, className='metric-title', style={'marginBottom': '5px'}))

    # Adiciona o valor com ícone se existir
    value_container = []
    if icon:
        value_container.append(html.I(className=icon, style={'marginRight': '5px'}))
    value_container.append(html.Span(value, style={'fontSize': '24px', 'fontWeight': '600', 'color': color}))

    card_content.append(html.Div(value_container, style={'display': 'flex', 'alignItems': 'center'}))

    # Adiciona o subtítulo se existir
    if subtitle:
        card_content.append(
            html.Div(subtitle,
                     style={'fontSize': '12px', 'color': colors['light_text'], 'marginTop': '5px'})
        )

    return html.Div(
        className='metric-box',
        style=style,
        children=card_content
    )
