# components/sections.py
# Funções para criação de seções e componentes de UI do dashboard
from dash import html, dcc
from config.config import colors


def adjust_color_brightness(hex_color, brightness_offset=0):
    """
    Ajusta o brilho de uma cor hexadecimal

    Args:
        hex_color (str): Cor em formato hexadecimal (#RRGGBB)
        brightness_offset (int): Valor para ajustar o brilho (-255 a 255)

    Returns:
        str: Cor com brilho ajustado em formato hexadecimal
    """
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]

    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    rgb_adjusted = tuple(max(0, min(255, val + brightness_offset)) for val in rgb)

    return f'#{rgb_adjusted[0]:02x}{rgb_adjusted[1]:02x}{rgb_adjusted[2]:02x}'


def create_section_container(children, margin_bottom='10px'):
    """
    Cria um container de seção com margens personalizáveis

    Args:
        children (list): Lista de elementos filhos
        margin_bottom (str, optional): Margem inferior. Padrão é '10px'.

    Returns:
        dash.html.Div: Container de seção
    """
    return html.Div(
        className='panel',
        style={'marginBottom': margin_bottom},
        children=children
    )


def create_section_header(title, value, font_size='12px'):
    """
    Cria o cabeçalho de uma seção

    Args:
        title (str): Título da seção
        value (str): Valor/métrica da seção
        font_size (str, optional): Tamanho da fonte. Padrão é '12px'.

    Returns:
        dash.html.Div: Cabeçalho da seção
    """
    return html.Div(
        className='section-title',
        children=[
            html.Div(title, className='card-title', style={'fontSize': font_size}),
            html.Div(value, className='card-total', style={'fontSize': font_size})
        ]
    )


def create_metric_header(title, value, percentage, font_size='11px'):
    """
    Cria um cabeçalho para métricas

    Args:
        title (str): Título da métrica
        value (str): Valor da métrica
        percentage (str): Percentual da métrica
        font_size (str, optional): Tamanho da fonte. Padrão é '11px'.

    Returns:
        dash.html.Div: Cabeçalho da métrica
    """
    return html.Div(
        className='metric-box',
        style={'marginBottom': '8px'},
        children=[
            html.Div(title, className='metric-title', style={'fontSize': font_size}),
            html.Div(
                className='metric-value',
                style={'fontSize': font_size},
                children=[
                    html.Span(value),
                    html.Span(f" ({percentage})", style={'marginLeft': '5px', 'color': '#546E7A'})
                ]
            )
        ]
    )


def create_graph_section(id, figure, height=None):
    """
    Cria uma seção de gráfico

    Args:
        id (str): ID do gráfico
        figure (plotly.graph_objects.Figure): Figura do gráfico
        height (str, optional): Altura do container. Padrão é None.

    Returns:
        dash.html.Div: Seção de gráfico
    """
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


def create_bordered_container(children, margin_bottom='10px'):
    """
    Cria um container com borda

    Args:
        children (list): Lista de elementos filhos
        margin_bottom (str, optional): Margem inferior. Padrão é '10px'.

    Returns:
        dash.html.Div: Container com borda
    """
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


# Função para criar a caixa métrica compacta


def create_compact_metric_box(title, style=None):
    """
    Cria uma caixa métrica compacta

    Args:
        title (str): Título da métrica
        style (dict, optional): Estilos adicionais. Padrão é None.

    Returns:
        dash.html.Div: Caixa métrica compacta
    """
    default_style = {
        'justifyContent': 'center',
        'marginBottom': '5px'
    }

    if style:
        default_style.update(style)

    return html.Div(
        className='compact-metric-box',
        style=default_style,
        children=[
            html.Div(title, className='metric-title')
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
    # Criar uma barra de progresso personalizada
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
        style={'marginBottom': '10px'},
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
                    progress_bar
                ]
            )
        ]
    )
