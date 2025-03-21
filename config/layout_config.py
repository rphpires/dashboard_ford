# layout_config.py
# Configurações de layout para dashboard responsivo sem rolagem

# Configuração de proporções e alturas
layout_config = {
    # Proporções relativas das colunas (total deve ser 100)
    'column_proportions': {
        'small': 30,   # Primeira coluna - 30%
        'medium': 32,  # Segunda coluna - 32%
        'large': 38    # Terceira coluna - 38%
    },

    # Proporções internas das seções em cada coluna
    'section_proportions': {
        # Coluna 1 - Utilização e Disponibilidade
        'utilization': 50,      # 50% da altura da coluna
        'availability': 50,     # 50% da altura da coluna

        # Coluna 2 - Tracks, Áreas e Clientes
        'tracks': 30,           # 30% da altura da coluna
        'areas': 30,            # 30% da altura da coluna
        'customers': 40,        # 40% da altura da coluna

        # Coluna 3 - Detalhamento de Utilização
        'programs': 25,         # 25% da altura da coluna
        'other_skills': 25,     # 25% da altura da coluna
        'internal_external': 50  # 50% da altura da coluna (combinados)
    },

    # Alturas base para cálculos responsivos
    'base_heights': {
        'header': 40,           # Altura do cabeçalho
        'footer': 22,           # Altura do rodapé
        'section_header': 30,   # Altura do cabeçalho de seção
        'chart_padding': 16,    # Padding total ao redor dos gráficos
        'card_header': 24       # Altura do cabeçalho de card
    },

    # Espaçamentos
    'spacing': {
        'column_gap': 8,        # Espaçamento entre colunas
        'section_gap': 8,       # Espaçamento entre seções
        'card_margin': 8,       # Margem externa dos cards
        'card_padding': 6       # Padding interno dos cards
    },

    # Tamanhos de fonte
    'font_sizes': {
        'header_title': 16,     # Título principal
        'section_title': 11,    # Título de seção
        'card_title': 10,       # Título de card
        'axis_title': 9,        # Título de eixo
        'axis_tick': 8,         # Valores dos eixos
        'data_label': 9,        # Rótulos de dados
    },

    # Configurações de visualização
    'display': {
        'show_data_labels': True,      # Mostrar rótulos nos dados
        'show_axis_titles': True,      # Mostrar títulos dos eixos
        'show_legends': False,         # Mostrar legendas
        'use_compact_cards': True      # Usar versão compacta dos cards
    },

    # Alturas fixas de fallback para gráficos (usado apenas se necessário)
    'chart_sm_height': 160,      # Altura pequena de gráfico
    'chart_md_height': 180,      # Altura média de gráfico
    'chart_lg_height': 200       # Altura grande de gráfico
}

# Configurações específicas para diferentes tamanhos de tela
responsive_breakpoints = {
    'small': {
        'max_width': 1200,
        'chart_heights': {
            'chart_sm_height': 160,
            'chart_md_height': 180,
            'chart_lg_height': 200,
        },
        'font_sizes': {
            'header_title': 14,
            'section_title': 10,
            'card_title': 9,
            'axis_title': 8,
            'axis_tick': 7,
            'data_label': 8,
        }
    },
    'medium': {
        'max_width': 1600,
        'chart_heights': {
            'chart_sm_height': 180,
            'chart_md_height': 200,
            'chart_lg_height': 220,
        },
        'font_sizes': {
            'header_title': 16,
            'section_title': 11,
            'card_title': 10,
            'axis_title': 9,
            'axis_tick': 8,
            'data_label': 9,
        }
    },
    'large': {
        'max_width': 10000,  # Valor arbitrariamente grande
        'chart_heights': {
            'chart_sm_height': 200,
            'chart_md_height': 220,
            'chart_lg_height': 240,
        },
        'font_sizes': {
            'header_title': 18,
            'section_title': 12,
            'card_title': 11,
            'axis_title': 10,
            'axis_tick': 9,
            'data_label': 10,
        }
    }
}

# Calcular altura disponível para gráficos


def calculate_available_height(viewport_height):
    """
    Calcula a altura disponível para gráficos com base na altura da viewport
    """
    fixed_heights = (
        layout_config['base_heights']['header']
        + layout_config['base_heights']['footer']
        + layout_config['spacing']['section_gap'] * 4  # Espaçamento entre seções
    )

    # Altura disponível total após elementos fixos
    available_height = viewport_height - fixed_heights

    return available_height

# Função para determinar proporções de altura com base na coluna


def get_height_proportions(column_type):
    """
    Retorna as proporções de altura para os elementos em uma coluna específica

    Args:
        column_type: 'small', 'medium' ou 'large'

    Returns:
        Dicionário com as proporções para cada tipo de seção na coluna
    """
    if column_type == 'small':
        return {
            'utilization': layout_config['section_proportions']['utilization'],
            'availability': layout_config['section_proportions']['availability']
        }
    elif column_type == 'medium':
        return {
            'tracks': layout_config['section_proportions']['tracks'],
            'areas': layout_config['section_proportions']['areas'],
            'customers': layout_config['section_proportions']['customers']
        }
    elif column_type == 'large':
        return {
            'programs': layout_config['section_proportions']['programs'],
            'other_skills': layout_config['section_proportions']['other_skills'],
            'internal_external': layout_config['section_proportions']['internal_external']
        }

    return {}

# Função para pegar configurações responsivas com base na largura da tela


def get_responsive_config(screen_width):
    """
    Retorna configurações apropriadas para o tamanho de tela atual

    Args:
        screen_width: Largura da tela em pixels

    Returns:
        Dicionário com configurações responsivas
    """
    if screen_width <= responsive_breakpoints['small']['max_width']:
        return responsive_breakpoints['small']
    elif screen_width <= responsive_breakpoints['medium']['max_width']:
        return responsive_breakpoints['medium']
    else:
        return responsive_breakpoints['large']

# Função para calcular altura real de um gráfico


def calculate_chart_height(viewport_height, column_type, section_type):
    """
    Calcula a altura ideal para um gráfico com base na altura da viewport,
    tipo de coluna e tipo de seção

    Args:
        viewport_height: Altura total da viewport
        column_type: 'small', 'medium' ou 'large'
        section_type: 'utilization', 'availability', 'tracks', etc.

    Returns:
        Altura calculada em pixels
    """
    available_height = calculate_available_height(viewport_height)
    proportions = get_height_proportions(column_type)

    if section_type in proportions:
        # Calcular com base na proporção e altura disponível
        proportion = proportions[section_type] / 100
        # Subtrair alturas de cabeçalho e padding
        section_fixed_height = (
            layout_config['base_heights']['section_header']
            + layout_config['base_heights']['chart_padding']
        )
        return (available_height * proportion) - section_fixed_height

    # Fallback para valores fixos
    if section_type in ['utilization', 'availability', 'programs', 'other_skills']:
        return layout_config['chart_sm_height']
    elif section_type in ['tracks', 'areas', 'customers']:
        return layout_config['chart_md_height']
    else:
        return layout_config['chart_sm_height']
