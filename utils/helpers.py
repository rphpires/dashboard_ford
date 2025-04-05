import pandas as pd
import traceback


# def safe_time_conversion(time_str):
#     try:
#         if time_str is None or time_str == "":
#             return 0.0

#         # Se já for um número, retornar diretamente
#         if isinstance(time_str, (int, float)):
#             return float(time_str)

#         # Verificar se é uma string no formato HH:MM
#         if isinstance(time_str, str) and ':' in time_str:
#             parts = time_str.split(':')
#             if len(parts) == 2:
#                 hours = int(parts[0])
#                 minutes = int(parts[1])
#                 return hours + (minutes / 60.0)

#         # Tentar converter diretamente para float
#         return float(time_str)

#     except (ValueError, TypeError, AttributeError) as e:
#         print(f"Erro ao converter tempo '{time_str}': {e}")
#         return 0.0


def safe_convert_to_float(value, default=0.0):
    if value is None:
        return default

    try:
        if isinstance(value, str) and value.strip() == '':
            return default

        return float(value)
    except (ValueError, TypeError):
        return default


def safe_calculate_percentage(part, total, format_str=True, default="0.0%"):
    try:
        # Converter valores para float de forma segura
        part_float = safe_convert_to_float(part)
        total_float = safe_convert_to_float(total)

        # Evitar divisão por zero
        if total_float <= 0:
            return default if format_str else 0.0

        # Calcular a porcentagem
        percentage = (part_float / total_float) * 100

        # Retornar o resultado formatado ou como número
        if format_str:
            return f"{percentage:.1f}%"
        else:
            return percentage

    except Exception as e:
        print(f"Erro ao calcular porcentagem: {e}")
        return default if format_str else 0.0


def process_tracks_data(dfs):
    """
    Processa os dados de tracks do dicionário dfs.

    Args:
        dfs (dict): Dicionário com os dados do dashboard

    Returns:
        dict: Dicionário de tracks processado
    """
    tracks_dict = {}

    if 'tracks_data' in dfs and dfs['tracks_data'] is not None:
        # Verificar o tipo de tracks_data
        if isinstance(dfs['tracks_data'], pd.DataFrame):
            print(f"tracks_data é um DataFrame com formato {dfs['tracks_data'].shape}")
            print(f"Colunas disponíveis: {list(dfs['tracks_data'].columns)}")

            # Converter o DataFrame para o formato de dicionário esperado
            try:
                # Verificar se o DataFrame tem as colunas necessárias
                if 'LocalityName' in dfs['tracks_data'].columns and 'StayTime' in dfs['tracks_data'].columns:
                    # Converter para o formato esperado
                    print("Convertendo DataFrame tracks_data para dicionário...")
                    tracks_dict = {}
                    for _, row in dfs['tracks_data'].iterrows():
                        track_name = row['LocalityName']
                        track_time = row['StayTime']
                        # Usar índice como chave única
                        tracks_dict[str(track_name)] = {
                            'track_name': str(track_name),
                            'track_time': str(track_time)
                        }
                    print(f"Conversão concluída. Dicionário tem {len(tracks_dict)} itens.")
                else:
                    print("DataFrame não tem as colunas esperadas.")
            except Exception as e:
                print(f"Erro ao converter DataFrame para dicionário: {e}")
                print(traceback.format_exc())
        else:
            # Se já for um dicionário, usar diretamente
            tracks_dict = dfs['tracks_data']
            print("tracks_dict obtido de dfs['tracks_data']")
    else:
        print("Aviso: dfs['tracks_data'] não disponível, usando dicionário vazio")

    # Log do conteúdo de tracks_dict
    print_dict_info(tracks_dict, "tracks_dict")

    return tracks_dict


def process_areas_data(dfs):
    areas_df = pd.DataFrame(columns=['area', 'hours'])

    if 'areas_data_df' in dfs and dfs['areas_data_df'] is not None:
        # Verificar se é um DataFrame ou um dicionário
        if isinstance(dfs['areas_data_df'], pd.DataFrame):
            areas_df = dfs['areas_data_df']
            print("areas_df obtido de dfs['areas_data_df'] como DataFrame")
        elif isinstance(dfs['areas_data_df'], dict):
            # Converter o dicionário para um DataFrame
            try:
                # Verificar se o dicionário tem o formato esperado
                if isinstance(dfs['areas_data_df'], dict) and len(dfs['areas_data_df']) > 0:
                    # Verificar formato do dicionário
                    if 'area' in dfs['areas_data_df'] and 'hours' in dfs['areas_data_df']:
                        # Formato esperado {area: [...], hours: [...]}
                        areas_df = pd.DataFrame(dfs['areas_data_df'])
                    else:
                        # Formato {area_name: hours, ...}
                        areas = []
                        hours = []
                        for area, hour in dfs['areas_data_df'].items():
                            areas.append(str(area))
                            hours.append(hour)
                        areas_df = pd.DataFrame({'area': areas, 'hours': hours})
                else:
                    print("Dicionário de áreas vazio ou em formato inválido")
            except Exception as e:
                print(f"Erro ao converter dicionário para DataFrame: {e}")
                areas_df = pd.DataFrame(columns=['area', 'hours'])
        else:
            print(f"Formato não suportado para areas_data_df: {type(dfs['areas_data_df'])}")
    else:
        print("Aviso: dfs['areas_data_df'] não disponível, usando DataFrame vazio")

    # Verificar se o DataFrame tem o formato correto
    if not areas_df.empty and ('area' not in areas_df.columns or 'hours' not in areas_df.columns):
        print("areas_df não tem as colunas necessárias. Recriando DataFrame...")
        try:
            # Verificar se há colunas que possam ser usadas
            possible_area_cols = [col for col in areas_df.columns if 'area' in col.lower() or 'depart' in col.lower() or 'local' in col.lower()]
            possible_hours_cols = [col for col in areas_df.columns if 'hour' in col.lower() or 'time' in col.lower() or 'stay' in col.lower()]

            if possible_area_cols and possible_hours_cols:
                print(f"Tentando usar colunas alternativas: {possible_area_cols[0]} e {possible_hours_cols[0]}")
                areas_df = areas_df.rename(columns={
                    possible_area_cols[0]: 'area',
                    possible_hours_cols[0]: 'hours'
                })
            else:
                print("Não foi possível identificar colunas adequadas.")
                areas_df = pd.DataFrame(columns=['area', 'hours'])
        except Exception as e:
            print(f"Erro ao tentar reformatar áreas: {e}")
            areas_df = pd.DataFrame(columns=['area', 'hours'])

    # Log do conteúdo de areas_df
    print_dataframe_info(areas_df, "areas_df")

    return areas_df


def process_customers_data(dfs):
    """
    Processa os dados de clientes do dicionário dfs.

    Args:
        dfs (dict): Dicionário com os dados do dashboard

    Returns:
        DataFrame: DataFrame de clientes processado
    """
    customers_df = pd.DataFrame()

    if 'customers_ytd' in dfs and dfs['customers_ytd'] is not None:
        customers_df = dfs['customers_ytd']
        print_dataframe_info(customers_df, "customers_ytd")
    else:
        print("Aviso: dfs['customers_ytd'] não está definido ou é None")

    return customers_df


def print_dict_info(data_dict, name):
    """
    Imprime informações sobre um dicionário para debugging.

    Args:
        data_dict (dict): Dicionário a ser analisado
        name (str): Nome do dicionário para referência
    """
    print(f"{name} tipo: {type(data_dict)}")
    if isinstance(data_dict, dict):
        print(f"{name} está vazio? {len(data_dict) == 0}")
        if len(data_dict) > 0:
            print(f"Número de itens em {name}: {len(data_dict)}")
            # Mostrar os primeiros itens
            print(f"Amostra de {name} (até 3 itens):")
            for i, (key, value) in enumerate(list(data_dict.items())[:3]):
                print(f"  {key}: {value}")


def print_dataframe_info(df, name):
    """
    Imprime informações sobre um DataFrame para debugging.

    Args:
        df (DataFrame): DataFrame a ser analisado
        name (str): Nome do DataFrame para referência
    """
    print(f"{name} tipo: {type(df)}")
    if hasattr(df, 'empty'):
        print(f"{name} está vazio? {df.empty}")
        if not df.empty:
            print(f"{name} formato: {df.shape}")
            print(f"{name} colunas: {list(df.columns)}")
            print(f"Primeiras 3 linhas de {name} (se houver):")
            try:
                print(df.head(3).to_string())
            except Exception:
                print(f"Não foi possível exibir as linhas de {name}")
