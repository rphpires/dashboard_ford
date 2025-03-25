import pandas as pd


def convert_list_to_dataframe(data):
    """
    Converte uma lista de dicionários para um DataFrame do pandas.

    Args:
        data (list or None): Lista de dicionários ou None

    Returns:
        pandas.DataFrame: DataFrame convertido ou DataFrame vazio
    """
    if data is None or not isinstance(data, list) or len(data) == 0:
        return pd.DataFrame()

    # Converter lista de dicionários para DataFrame
    df = pd.DataFrame(data)

    return df


def convert_dataframe_to_dict(df):
    """
    Converte um DataFrame para uma lista de dicionários serializável.

    Args:
        df (pandas.DataFrame): DataFrame a ser convertido

    Returns:
        list: Lista de dicionários com os dados do DataFrame
    """
    if df is None or len(df) == 0:
        return []

    # Converter cada linha para um dicionário
    return df.to_dict(orient='records')


def normalize_dashboard_data(dfs):
    """
    Normaliza os dados do dashboard, convertendo listas de dicionários para DataFrames.

    Args:
        dfs (dict): Dicionário de dados do dashboard

    Returns:
        dict: Dicionário com DataFrames normalizados
    """
    normalized_dfs = {}

    # Lista de chaves que devem ser convertidas para DataFrame
    dataframe_keys = [
        'utilization', 'availability',
        'tracks', 'tracks_ytd',
        'areas', 'areas_ytd',
        'programs', 'other_skills',
        'internal_users', 'external_sales',
        'customers_ytd'
    ]

    for key in dataframe_keys:
        normalized_dfs[key] = convert_list_to_dataframe(dfs.get(key, []))

    # Copiar valores que não precisam de conversão
    normalized_dfs.update({
        'total_hours': dfs.get('total_hours', '00:00'),
        'total_hours_ytd': dfs.get('total_hours_ytd', '00:00'),
        'ytd_utilization_percentage': dfs.get('ytd_utilization_percentage', '0%'),
        'ytd_availability_percentage': dfs.get('ytd_availability_percentage', '0%')
    })

    return normalized_dfs


def safe_json_serializer(obj):
    """
    Função auxiliar para serialização segura de objetos.

    Args:
        obj: Objeto a ser serializado

    Returns:
        Versão serializável do objeto
    """
    if isinstance(obj, pd.DataFrame):
        return convert_dataframe_to_dict(obj)
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, 'tolist'):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
