# components/sections.py
# Componentes reutilizáveis para seções do dashboard
from dash import html, dcc
from config.config import colors, chart_config


def create_section_container(children, margin_bottom='15px'):
    """Cria um container para uma seção do dashboard em estilo moderno"""
    return html.Div(
        style={
            'marginBottom': margin_bottom,
        },
        className='panel',
        children=children
    )


def create_section_header(title, total_value=None):
    """Cria o cabeçalho de uma seção com título e valor total opcional em estilo moderno"""
    header_content = [html.Div(title, className='card-title')]

    if total_value:
        header_content.append(
            html.Div(total_value, className='card-total')
        )

    return html.Div(
        className='section-title',
        children=header_content
    )


def create_metric_header(title, hours, percentage=None):
    """Cria um cabeçalho de métrica com título, horas e porcentagem opcional em estilo moderno"""
    value_parts = []

    # Adiciona as horas
    value_parts.append(f"{hours} hr")

    # Adiciona o percentual, se existir
    if percentage:
        value_parts.append(f" ({percentage})")

    value_text = "".join(value_parts)

    return html.Div(
        className='metric-box',
        children=[
            html.Div(title, className='metric-title'),
            html.Div(value_text, className='metric-value')
        ]
    )


def create_graph_section(id, figure, config=None):
    """Cria uma seção de gráfico com ID e figura em estilo moderno"""
    if config is None:
        config = chart_config

    return html.Div(
        className='chart-container',
        children=[
            dcc.Graph(
                id=id,
                figure=figure,
                config=config
            )
        ]
    )


def create_bordered_container(children, margin_right='0px', margin_bottom='15px'):
    """Cria um container com borda para subseções em estilo moderno"""
    return html.Div(
        style={
            'marginBottom': margin_bottom,
            'marginRight': margin_right,
            'padding': '15px',
            'backgroundColor': colors['card_bg'],
            'borderRadius': '6px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        },
        children=children
    )


def create_side_by_side_container(children):
    """Cria um container para elementos lado a lado em estilo moderno"""
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
            'marginRight': margin_right,
        },
        children=children
    )


def create_info_card(title, value, subtitle=None, icon=None, color=None):
    """Cria um card informativo com título, valor e subtítulo opcional em estilo moderno"""
    if color is None:
        color = colors['primary']

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
        style={'padding': '15px', 'flexDirection': 'column', 'alignItems': 'flex-start'},
        children=card_content
    )


def create_summary_row(items):
    """Cria uma linha com cartões informativos resumidos em estilo moderno"""
    return html.Div(
        className='flex-container',
        style={'marginBottom': '15px'},
        children=[
            html.Div(
                className='flex-item',
                children=[item],
                style={'minWidth': f"{100/len(items)}%"}
            ) for item in items
        ]
    )
