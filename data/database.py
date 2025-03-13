# data/database.py
# Funções para conexão com banco de dados SQL Server (implementação futura)
import os
import pandas as pd
from datetime import datetime

# Por enquanto, importar dados simulados
from .mock_data import get_all_dataframes


def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados SQL Server.
    Esta função será implementada no futuro quando a integração com SQL Server estiver ativa.
    """
    # Configurações para conexão com SQL Server
    server = os.environ.get('DB_SERVER', 'seu_servidor')
    database = os.environ.get('DB_NAME', 'seu_banco_de_dados')
    # username = os.environ.get('DB_USER', 'seu_usuario')
    # password = os.environ.get('DB_PASSWORD', 'sua_senha')

    try:
        # Este é apenas um placeholder - será implementado quando conectar ao SQL Server
        print(f"Conectando ao servidor {server}, banco de dados {database}")
        # Em uma implementação real, você usaria pyodbc ou outro driver
        return None
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def load_dashboard_data():
    """
    Função principal para carregar todos os dados do dashboard.
    No futuro, carregará dados do SQL Server. Por enquanto, usa os dados simulados.
    """
    # Tentar conectar ao banco de dados
    conn = get_db_connection()

    if conn:
        # Futuro: implementar consultas SQL para obter dados reais
        # Por enquanto, retorna os dados simulados mesmo quando houver conexão
        print("Banco de dados conectado, mas usando dados simulados por enquanto")

    # Retornar todos os DataFrames
    return get_all_dataframes()


def get_current_period_info():
    """
    Obtém informações do período atual (mês, dia, totais).
    No futuro, isso poderá vir do banco de dados.
    """
    # Por enquanto, usando valores fixos definidos no mock_data
    return {
        'current_month': 'JANUARY',
        'current_day': '24',
        'total_hours': '1032',
        'total_hours_ytd': '10386',
        'ytd_utilization_percentage': '16%',
        'ytd_availability_percentage': '96%'
    }
