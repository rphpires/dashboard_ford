# config.py - Versão Moderna
# Configurações globais para o dashboard
import json

from utils.tracer import *


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


def dashboard_constants():
    try:
        with open("config/dashboard_constants.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    except Exception as e:
        error(f"Erro inesperado ao ler o arquivo JSON: {str(e)}")
        # Constantes do dashboard
        return {
            'target_availability': 80,  # Meta de disponibilidade em percentual
            'target_utilization': 80,   # Meta de utilização em percentual
            'decimal_places': 1        # Casas decimais para percentuais
        }
