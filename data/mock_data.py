# data/mock_data.py
# Dados simulados para o dashboard
import pandas as pd
from datetime import datetime as dt


# Dados de utilização mensal (%)
utilization_data = {
    'month': ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
    'utilization': [7, 7, 19, 31, 13, 12, 20, 8, 0, 0, 0, 0]
}

# Dados de disponibilidade de tracks (%)
availability_data = {
    'month': ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
    'availability': [99, 99, 98, 97, 99, 99, 79, 99, 0, 0, 0, 0]
}

# Dados de utilização por tracks (mensal)
tracks_utilization = {
    'track_type': ['UNPAVED TRACKS', 'PAVED TRACKS', 'HILL SECTION', 'SPECIAL TRACKS', 'INNER', 'NEW SPECIAL TRACKS', 'GRADED YARD'],
    'hours': [0, 0, 0, 0, 0, 0, 0],
    'percentage': ['0%', '0%', '0%', '0%', '0%', '0%', '0%']
}

# Dados de utilização por tracks (YTD)
tracks_utilization_ytd = {
    'track_type': ['UNPAVED TRACKS', 'PAVED TRACKS', 'SPECIAL TRACKS', 'HILL SECTION', 'INNER', 'NEW SPECIAL TRACKS', 'GRAVEL ROAD CIRCUIT', 'GRADED YARD', 'DIRTY ROAD'],
    'hours': [0, 0, 0, 0, 0, 0, 0, 0, 0],
    'percentage': ['0%', '0%', '0%', '0%', '0%', '0%', '0%', '0%', '0%']
}

# Dados de utilização por áreas (mensal)
areas_utilization = {
    'area': ['Ford Land', 'VEV', 'FCSD', 'PD', 'TPG Commercial', 'Marketing', 'Press'],
    'hours': [0, 0, 0, 0, 0, 0, 0],
    'percentage': ['0%', '0%', '0%', '0%', '0%', '0%', '0%']
}

# Dados de utilização por áreas (YTD)
areas_utilization_ytd = {
    'area': ['Ford Land', 'VEV', 'PD', 'Press', 'Marketing', 'TPG Commercial', 'Ford GO', 'FCSD', 'Commercial Vehicles'],
    'hours': [0, 0, 0, 0, 0, 0, 0, 0, 0],
    'percentage': ['0%', '0%', '0%', '0%', '0%', '0%', '0%', '0%', '0%']
}

# Dados de utilização por programas
programs_utilization = {
    'program': ['GATPD Rangely 2023 (CT New Tipton)', 'SEL Legacy Products', '23MY Brght/P702P (T6)', 'DEV_PoleStar Development', 'SUB/LR-Mule A37U/LR Homologation', '20MY/PMJV/VRM (CMX SUV2)', 'Chassis/Comp/Drivetrrain Workload'],
    'hours': [37, 18, 13, 10, 9, 2, 0]
}

# Dados de outras equipes de habilidades
other_skills_utilization = {
    'team': ['FCSD', 'Marketing', 'SVM Ranger', 'SVM Transit', 'Press'],
    'hours': [0, 0, 0, 0, 0]
}

# Dados de usuários internos e vendas externas
internal_users = {
    'department': ['TPG Support', 'Ford Land', 'TPG VEV Operation & Business'],
    'hours': [0, 0, 0]
}

external_sales = {
    'company': ['Ediag', 'Dana', 'TPG Sales Team', 'Zeentech'],
    'hours': [0, 0, 0, 0]
}

# Dados de utilização por clientes (YTD)
customers_utilization_ytd = {
    'customer_type': ['INTERNAL USERS', 'PROGRAMS', 'OTHER SKILL TEAMS', 'EXTERNAL SALES'],
    'hours': [0, 0, 0, 0],
    'percentage': ['0%', '15%', '13%', '3%']
}

# Funções para obter DataFrames


def get_utilization_df():
    return pd.DataFrame(utilization_data)


def get_availability_df():
    return pd.DataFrame(availability_data)


def get_tracks_df():
    return pd.DataFrame(tracks_utilization)


def get_tracks_ytd_df():
    return pd.DataFrame(tracks_utilization_ytd)


def get_areas_df():
    return pd.DataFrame(areas_utilization)


def get_areas_ytd_df():
    return pd.DataFrame(areas_utilization_ytd)


def get_programs_df():
    return pd.DataFrame(programs_utilization)


def get_other_skills_df():
    return pd.DataFrame(other_skills_utilization)


def get_internal_users_df():
    return pd.DataFrame(internal_users)


def get_external_sales_df():
    return pd.DataFrame(external_sales)


def get_customers_ytd_df():
    return pd.DataFrame(customers_utilization_ytd)

# Função para obter todos os DataFrames de uma vez


def get_all_dataframes():
    """
    Retorna dados simulados para o dashboard, formatados para os 4 valores esperados.

    Returns:
        tuple: (dfs, tracks_data, areas_data_df, periodo_info)
    """
    # Dicionário com todos os DataFrames para visualizações
    dfs = {
        'utilization': get_utilization_df(),
        'availability': get_availability_df(),
        'programs': get_programs_df(),
        'other_skills': get_other_skills_df(),
        'internal_users': get_internal_users_df(),
        'external_sales': get_external_sales_df(),
        'customers_ytd': get_customers_ytd_df()
    }

    # Dados de tracks específicos
    tracks_data = get_tracks_df()

    # DataFrame de áreas
    areas_data_df = get_areas_df()

    # Informações do período
    periodo_info = {
        'current_month': dt.now().strftime('%B').upper(),
        'current_day': str(dt.now().day),
        'ytd_utilization_percentage': '0%',
        'ytd_availability_percentage': '0%',
        'total_hours': '0',
        'total_hours_ytd': '0'
    }

    # Retornar os 4 valores esperados
    return dfs, tracks_data, areas_data_df, periodo_info
