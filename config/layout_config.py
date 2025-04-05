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
