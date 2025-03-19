# config.py - Versão Moderna
# Configurações globais para o dashboard

# Cores para os gráficos e componentes
colors = {
    # Cores primárias
    'primary': '#2196F3',
    'primary_dark': '#1976D2',
    'primary_light': '#BBDEFB',
    'secondary': '#4CAF50',
    'secondary_dark': '#388E3C',
    'accent': '#FF5722',
    'warning': '#FFC107',

    # Texto e fundos
    'text': '#263238',
    'text_light': '#546E7A',
    'light_text': '#546E7A',
    'text_lighter': '#78909C',
    'background': '#F5F7FA',
    'card_bg': '#FFFFFF',
    'grid_bg': '#FFFFFF',
    'card_border': 'rgba(0, 0, 0, 0.05)',
    'grid_line': '#ECEFF1',

    # Componentes específicos
    'header_bg': '#1976D2',
    'header_text': '#FFFFFF',
    'section_bg': '#2196F3',
    'bar_color': '#2196F3',
    'bar_hover': '#1976D2',
    'target_line': '#FF5722',

    # Paletas para gráficos
    'blue_palette': ['#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5', '#1565C0'],
    'green_palette': ['#E8F5E9', '#A5D6A7', '#66BB6A', '#43A047', '#2E7D32'],
    'orange_palette': ['#FFF3E0', '#FFCC80', '#FFA726', '#FB8C00', '#EF6C00'],
    'red_palette': ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350'],
    'purple_palette': ['#F3E5F5', '#CE93D8', '#AB47BC', '#8E24AA', '#6A1B9A'],
}

# Configurações dos gráficos
chart_config = {
    'displayModeBar': False,
    'responsive': True,
    'staticPlot': False,
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
        'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian',
        'toggleSpikelines'
    ],
}

# Configurações de layout para gráficos
layout_config = {
    # Margens para gráficos
    'margin_default': {'l': 40, 'r': 20, 't': 20, 'b': 40},
    'margin_with_labels': {'l': 40, 'r': 20, 't': 20, 'b': 80},
    'margin_minimal': {'l': 10, 'r': 10, 't': 10, 'b': 10},

    # Alturas padrão para gráficos
    'chart_sm_height': 150,
    'chart_md_height': 200,
    'chart_lg_height': 250,

    # Espaçamento e larguras
    'bar_gap': 0.2,
    'group_gap': 0.1,
    'line_width': 2,
    'marker_size': 8,
}

# Estilo comum para gráficos
chart_style = {
    # Estilo para o grid
    'grid': {
        'xaxis': {
            'showgrid': False,
            'zeroline': False,
            'showline': True,
            'linecolor': colors['grid_line'],
            'tickfont': {'size': 10, 'color': colors['text_light']},
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': 'rgba(236, 239, 241, 0.5)',
            'zeroline': False,
            'showline': True,
            'linecolor': colors['grid_line'],
            'tickfont': {'size': 10, 'color': colors['text_light']},
        },
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': colors['text'], 'family': 'Inter, sans-serif'},
    },

    # Estilo para barras
    'bar': {
        'marker': {
            'color': colors['bar_color'],
            'line': {'width': 0},
        },
        'hoverinfo': 'text',
    },

    # Estilo para linhas de meta
    'target_line': {
        'line': {'color': colors['target_line'], 'width': 2, 'dash': 'dash'},
        'mode': 'lines',
        'hoverinfo': 'none',
    },

    # Estilo para rótulos dos gráficos
    'annotation': {
        'font': {'size': 10, 'color': colors['text_light']},
        'showarrow': False,
        'bgcolor': 'rgba(255, 255, 255, 0.8)',
        'bordercolor': colors['grid_line'],
        'borderwidth': 1,
        'borderpad': 4,
    },

    # Estilo para hover labels
    'hoverlabel': {
        'bgcolor': 'white',
        'font_size': 12,
        'font_family': 'Inter, sans-serif',
        'bordercolor': colors['card_border'],
    },
}

# Constantes do dashboard
dashboard_constants = {
    'target_availability': 80,  # Meta de disponibilidade em percentual
    'target_utilization': 80,   # Meta de utilização em percentual
    'decimal_places': 1,        # Casas decimais para percentuais
    'animation_duration': 800,  # Duração das animações em ms
}

# Temas para gráficos específicos
chart_themes = {
    'utilization': {
        'colors': colors['blue_palette'],
        'bgcolor': 'rgba(225, 245, 254, 0.5)',
    },
    'availability': {
        'colors': colors['green_palette'],
        'bgcolor': 'rgba(232, 245, 233, 0.5)',
    },
    'programs': {
        'colors': colors['blue_palette'],
        'bgcolor': 'rgba(227, 242, 253, 0.3)',
    },
    'other_skills': {
        'colors': colors['purple_palette'],
        'bgcolor': 'rgba(243, 229, 245, 0.3)',
    },
    'internal_users': {
        'colors': colors['blue_palette'],
        'bgcolor': 'rgba(227, 242, 253, 0.3)',
    },
    'external_sales': {
        'colors': colors['green_palette'],
        'bgcolor': 'rgba(232, 245, 233, 0.3)',
    },
    'tracks': {
        'colors': colors['blue_palette'],
        'bgcolor': 'rgba(227, 242, 253, 0.3)',
    },
    'areas': {
        'colors': colors['green_palette'],
        'bgcolor': 'rgba(232, 245, 233, 0.3)',
    },
    'customers': {
        'colors': colors['orange_palette'],
        'bgcolor': 'rgba(255, 243, 224, 0.3)',
    },
}
