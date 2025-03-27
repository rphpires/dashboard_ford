# app.py
# Aplicação principal do dashboard zeentech VEV (versão otimizada sem rolagem)
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import timedelta, datetime as dt
from utils.tracer import *
from layouts.header import create_header
from config.layout_config import layout_config, get_responsive_config
from components.sections import (
    create_section_container, create_section_header,
    create_metric_header, create_graph_section,
    create_bordered_container, create_side_by_side_container,
    create_flex_item, create_info_card,
    # create_compact_metric_box, create_summary_metrics
)
from components.graphs import (
    create_utilization_graph, create_availability_graph,
    create_programs_graph, create_other_skills_graph,
    create_internal_users_graph, create_external_sales_graph,
    create_tracks_graph, create_areas_graph,
    create_customers_stacked_graph  # Nova função para gráfico de clientes
)
from layouts.eja_manager import create_eja_manager_layout
# from layouts.left_column import create_left_column
# from layouts.right_column import create_right_column

from data.database import get_available_months, load_dashboard_data, get_current_period_info
from data.eja_manager import get_eja_manager
from data.tracks_manager import adjust_tracks_names
from layouts.eja_manager import create_eja_table
import os
import base64
import json
import tempfile
from dash.exceptions import PreventUpdate
from data.weekly_processor import setup_scheduler, check_and_process_if_needed
import threading
from dateutil.relativedelta import relativedelta


# Inicializar a aplicação Dash com Bootstrap para melhor estilo
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    title='Ford Dashboard',
    update_title='Carregando...',
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ],
)


def init_weekly_processor():
    # Verificar se é necessário processar dados
    needs_processing = check_and_process_if_needed()
    # Configurar agendamento semanal (executar imediatamente apenas se for necessário)
    setup_scheduler(run_immediately=needs_processing)
    trace("Inicialização do processador semanal concluída", color="green")


threading.Thread(target=init_weekly_processor, daemon=True).start()


available_months = get_available_months(20)


# Modificar a inicialização para não carregar dados imediatamente
dfs, tracks_data, areas_data_df, periodo_info = None, None, None, None

# Inicializar variáveis globais
current_month = ""
current_day = ""
ytd_utilization_percentage = ""
ytd_availability_percentage = ""
total_hours = ""
total_hours_ytd = ""


def create_utilization_availability_column(dfs, ytd_utilization_percentage, ytd_availability_percentage):
    """
    Cria a coluna de gráficos de utilização e disponibilidade
    """
    # from dash import html
    # from components.sections import create_section_container, create_section_header, create_graph_section, create_info_card
    # from components.graphs import create_utilization_graph, create_availability_graph

    # Importar a função de conversão segura
    # Se você adicionou a função a um módulo diferente, ajuste o import
    try:
        from utils.helpers import safe_convert_to_float, safe_calculate_percentage
    except ImportError:
        # Definir funções inline se não puder importar
        def safe_convert_to_float(value, default=0.0):
            try:
                if value is None:
                    return default
                if isinstance(value, str) and value.strip() == '':
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_calculate_percentage(part, total, format_str=True, default="0.0%"):
            try:
                part_float = safe_convert_to_float(part)
                total_float = safe_convert_to_float(total)
                if total_float <= 0:
                    return default if format_str else 0.0
                percentage = (part_float / total_float) * 100
                if format_str:
                    return f"{percentage:.1f}%"
                else:
                    return percentage
            except Exception as e:
                print(f"Erro ao calcular porcentagem: {e}")
                return default if format_str else 0.0

    # Calcular totais e percentuais para cada categoria
    try:
        # Extrair o valor numérico do total de horas
        if isinstance(total_hours, str) and ':' in total_hours:
            horas, minutos = map(int, total_hours.split(':'))
            total_horas_decimal = horas + (minutos / 60.0)
        else:
            total_horas_decimal = safe_convert_to_float(total_hours)

        # Calcular somas para cada categoria
        programas_horas = safe_convert_to_float(dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0)
        outras_equipes_horas = safe_convert_to_float(dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0)
        usuarios_internos_horas = safe_convert_to_float(dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0)
        vendas_externas_horas = safe_convert_to_float(dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0)

        # Calcular percentuais com função segura
        programas_perc_fmt = safe_calculate_percentage(programas_horas, total_horas_decimal)
        outras_equipes_perc_fmt = safe_calculate_percentage(outras_equipes_horas, total_horas_decimal)
        usuarios_internos_perc_fmt = safe_calculate_percentage(usuarios_internos_horas, total_horas_decimal)
        vendas_externas_perc_fmt = safe_calculate_percentage(vendas_externas_horas, total_horas_decimal)

    except Exception as e:
        print(f"Erro ao calcular percentuais: {e}")
        traceback.print_exc()
        # Valores padrão em caso de erro
        programas_horas = 89
        outras_equipes_horas = 130
        usuarios_internos_horas = 778
        vendas_externas_horas = 34
        programas_perc_fmt = "9%"
        outras_equipes_perc_fmt = "13%"
        usuarios_internos_perc_fmt = "75%"
        vendas_externas_perc_fmt = "3%"

    return [
        # Seção de Utilização (%)
        create_section_container([
            create_section_header('UTILIZAÇÃO (%)', ytd_utilization_percentage),
            html.Div(
                className='panel-content',
                children=[
                    # Cards de resumo agrupados
                    html.Div(
                        className='flex-container',
                        style={'marginBottom': '2px'},
                        children=[
                            create_info_card('Programas', f"{int(programas_horas)} hr",
                                             f"{programas_perc_fmt} do total", color='#1E88E5'),
                            create_info_card('Outras Equipes', f"{int(outras_equipes_horas)} hr",
                                             f"{outras_equipes_perc_fmt} do total", color='#673AB7'),
                            create_info_card('Uso Interno', f"{int(usuarios_internos_horas)} hr",
                                             f"{usuarios_internos_perc_fmt} do total", color='#2E7D32'),
                            create_info_card('Vendas Externas', f"{int(vendas_externas_horas)} hr",
                                             f"{vendas_externas_perc_fmt} do total", color='#F57C00')
                        ]
                    ),
                    # Gráfico - sem altura fixa para ajuste automático
                    create_graph_section(
                        'utilization-graph',
                        create_utilization_graph(dfs['utilization'], height=None)
                    )
                ]
            )
        ], margin_bottom='2px'),

        # Seção de Disponibilidade de Tracks (%)
        create_section_container([
            create_section_header('DISPONIBILIDADE DE TRACKS (%)', ytd_availability_percentage),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section(
                        'availability-graph',
                        create_availability_graph(dfs['availability'], height=None)
                    )
                ]
            )
        ], margin_bottom='2px')
    ]


# Função para criar o detalhamento de utilização mensal otimizado e expandido
def create_optimized_utilization_breakdown(dfs, total_hours):
    """
    Cria o layout otimizado para o detalhamento de utilização mensal,
    com gráficos maiores e melhor distribuídos.
    """
    # Calcular totais e percentuais para cada categoria
    try:
        # Extrair o valor numérico do total de horas
        if ':' in total_hours:
            horas, minutos = map(int, total_hours.split(':'))
            total_horas_decimal = horas + (minutos / 60.0)
        else:
            total_horas_decimal = float(total_hours)

        # Calcular somas para cada categoria
        programas_horas = dfs['programs']['hours'].sum() if 'hours' in dfs['programs'].columns else 0
        outras_equipes_horas = dfs['other_skills']['hours'].sum() if 'hours' in dfs['other_skills'].columns else 0
        usuarios_internos_horas = dfs['internal_users']['hours'].sum() if 'hours' in dfs['internal_users'].columns else 0
        vendas_externas_horas = dfs['external_sales']['hours'].sum() if 'hours' in dfs['external_sales'].columns else 0

        # Calcular percentuais
        if total_horas_decimal > 0:
            programas_perc = (programas_horas / total_horas_decimal) * 100
            outras_equipes_perc = (outras_equipes_horas / total_horas_decimal) * 100
            usuarios_internos_perc = (usuarios_internos_horas / total_horas_decimal) * 100
            vendas_externas_perc = (vendas_externas_horas / total_horas_decimal) * 100
        else:
            programas_perc = outras_equipes_perc = usuarios_internos_perc = vendas_externas_perc = 0

        # Formatação para exibição
        programas_perc_fmt = f"{programas_perc:.1f}%"
        outras_equipes_perc_fmt = f"{outras_equipes_perc:.1f}%"
        usuarios_internos_perc_fmt = f"{usuarios_internos_perc:.1f}%"
        vendas_externas_perc_fmt = f"{vendas_externas_perc:.1f}%"

    except Exception as e:
        print(f"Erro ao calcular percentuais: {e}")
        # Valores padrão em caso de erro
        programas_horas = 89
        outras_equipes_horas = 130
        usuarios_internos_horas = 778
        vendas_externas_horas = 34
        programas_perc_fmt = "9%"
        outras_equipes_perc_fmt = "13%"
        usuarios_internos_perc_fmt = "75%"
        vendas_externas_perc_fmt = "3%"

    return create_section_container([
        create_section_header('DETALHAMENTO DE UTILIZAÇÃO MENSAL', f"{total_hours} hr"),
        html.Div(
            className='panel-content',
            children=[
                # Indicadores de Resumo em linha compacta
                html.Div(
                    className='flex-container compact-info-cards',
                    style={'marginBottom': '2px'},
                    children=[
                        create_info_card('Programas', f"{int(programas_horas)} hr",
                                         f"{programas_perc_fmt} do total", color='#1E88E5'),
                        create_info_card('Outras Equipes', f"{int(outras_equipes_horas)} hr",
                                         f"{outras_equipes_perc_fmt} do total", color='#673AB7'),
                        create_info_card('Uso Interno', f"{int(usuarios_internos_horas)} hr",
                                         f"{usuarios_internos_perc_fmt} do total", color='#2E7D32'),
                        create_info_card('Vendas Externas', f"{int(vendas_externas_horas)} hr",
                                         f"{vendas_externas_perc_fmt} do total", color='#F57C00')
                    ]
                ),

                # Programas - altura flexível
                create_bordered_container([
                    create_metric_header('PROGRAMAS', f"{int(programas_horas)}", programas_perc_fmt),
                    create_graph_section(
                        'programs-graph',
                        create_programs_graph(dfs['programs'], height=None)
                    )
                ]),

                # Other Skill Teams - altura flexível
                create_bordered_container([
                    create_metric_header('OUTRAS EQUIPES DE HABILIDADES', f"{int(outras_equipes_horas)}", outras_equipes_perc_fmt),
                    create_graph_section(
                        'other-skills-graph',
                        create_other_skills_graph(dfs['other_skills'], height=None)
                    )
                ]),

                # Internal Users and External Sales (lado a lado)
                create_side_by_side_container([
                    # Internal Users
                    create_flex_item([
                        create_metric_header('USUÁRIOS INTERNOS', f"{int(usuarios_internos_horas)}", usuarios_internos_perc_fmt),
                        create_graph_section(
                            'internal-users-graph',
                            create_internal_users_graph(dfs['internal_users'], height=None)
                        )
                    ], margin_right='8px', min_width='38%'),

                    # External Sales
                    create_flex_item([
                        create_metric_header('VENDAS EXTERNAS', f"{int(vendas_externas_horas)}", vendas_externas_perc_fmt),
                        create_graph_section(
                            'external-sales-graph',
                            create_external_sales_graph(dfs['external_sales'], height=None)
                        )
                    ], min_width='38%')
                ])
            ]
        )
    ])


# Função para criar a coluna com tracks, áreas e clientes (modificada)
def create_tracks_areas_column(dfs, total_hours, total_hours_ytd):
    """
    Cria a coluna com utilização por tracks, áreas e clientes
    Modificada para exibir apenas 8 tracks e usar novo tipo de gráfico para clientes
    """
    # Log detalhado no início da função
    print("\n========== INÍCIO DE create_tracks_areas_column ==========")
    print(f"total_hours: {total_hours}")
    print(f"total_hours_ytd: {total_hours_ytd}")
    print(f"Keys em dfs: {list(dfs.keys())}")

    try:
        # Extrair tracks_data do dicionário dfs
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
                        # Se não tiver as colunas esperadas, usar dados simulados
                        print("DataFrame não tem as colunas esperadas. Criando dados simulados.")
                        tracks_dict = {
                            'Track 1': {'track_name': 'Track 1', 'track_time': '102:30'},
                            'Track 2': {'track_name': 'Track 2', 'track_time': '85:15'},
                            'Track 3': {'track_name': 'Track 3', 'track_time': '65:45'},
                        }
                except Exception as e:
                    print(f"Erro ao converter DataFrame para dicionário: {e}")
                    print(traceback.format_exc())
                    # Usar dados simulados em caso de erro
                    tracks_dict = {
                        'Track 1': {'track_name': 'Track 1', 'track_time': '102:30'},
                        'Track 2': {'track_name': 'Track 2', 'track_time': '85:15'},
                        'Track 3': {'track_name': 'Track 3', 'track_time': '65:45'},
                    }
            else:
                # Se já for um dicionário, usar diretamente
                tracks_dict = dfs['tracks_data']
                print("tracks_dict obtido de dfs['tracks_data']")
        else:
            print("Aviso: dfs['tracks_data'] não disponível, usando dicionário vazio")

        # Log do conteúdo de tracks_dict
        print(f"tracks_dict tipo: {type(tracks_dict)}")
        if isinstance(tracks_dict, dict):
            print(f"tracks_dict está vazio? {len(tracks_dict) == 0}")
            if len(tracks_dict) > 0:
                print(f"Número de itens em tracks_dict: {len(tracks_dict)}")
                # Mostrar os primeiros itens
                print("Amostra de tracks_dict (até 3 itens):")
                for i, (key, value) in enumerate(list(tracks_dict.items())[:3]):
                    print(f"  {key}: {value}")

        # Extrair areas_data_df do dicionário dfs
        areas_df = pd.DataFrame(columns=['area', 'hours'])
        if 'areas_data_df' in dfs and dfs['areas_data_df'] is not None:
            areas_df = dfs['areas_data_df']
            print("areas_df obtido de dfs['areas_data_df']")
            # Verificar se areas_df tem o formato correto
            if 'area' not in areas_df.columns or 'hours' not in areas_df.columns:
                print("areas_df não tem as colunas necessárias. Recriando DataFrame...")
                # Tentar reformatar o DataFrame se tiver outras colunas que possam ser usadas
                if isinstance(areas_df, pd.DataFrame) and not areas_df.empty:
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
                            # Criar dados simulados
                            print("Não foi possível identificar colunas adequadas. Criando dados simulados.")
                            areas_df = pd.DataFrame({
                                'area': ['Area 1', 'Area 2', 'Area 3', 'Area 4'],
                                'hours': [120, 85, 65, 30]
                            })
                    except Exception as e:
                        print(f"Erro ao tentar reformatar áreas: {e}")
                        # Criar dados simulados em caso de erro
                        areas_df = pd.DataFrame({
                            'area': ['Area 1', 'Area 2', 'Area 3', 'Area 4'],
                            'hours': [120, 85, 65, 30]
                        })
        else:
            print("Aviso: dfs['areas_data_df'] não disponível, usando DataFrame vazio")

        # Log do conteúdo de areas_df
        print(f"areas_df tipo: {type(areas_df)}")
        if hasattr(areas_df, 'empty'):
            print(f"areas_df está vazio? {areas_df.empty}")
            if not areas_df.empty:
                print(f"areas_df formato: {areas_df.shape}")
                print(f"areas_df colunas: {list(areas_df.columns)}")
                print("Primeiras 3 linhas de areas_df (se houver):")
                try:
                    print(areas_df.head(3).to_string())
                except Exception:
                    print("Não foi possível exibir as linhas de areas_df")

        # Log do customers_ytd DataFrame
        print("\nInformações sobre o DataFrame de clientes:")
        if 'customers_ytd' in dfs and dfs['customers_ytd'] is not None:
            customers_df = dfs['customers_ytd']
            print(f"customers_ytd tipo: {type(customers_df)}")
            if hasattr(customers_df, 'empty'):
                print(f"customers_ytd está vazio? {customers_df.empty}")
                if not customers_df.empty:
                    print(f"customers_ytd formato: {customers_df.shape}")
                    print(f"customers_ytd colunas: {list(customers_df.columns)}")
        else:
            print("Aviso: dfs['customers_ytd'] não está definido ou é None")
            dfs['customers_ytd'] = pd.DataFrame()

        # Tentar importar e usar a função adjust_tracks_names
        try:
            adjusted_tracks = adjust_tracks_names(tracks_dict)
            print("Tracks ajustados com adjust_tracks_names()")
            # Verificar se o ajuste afetou os dados
            if isinstance(adjusted_tracks, dict):
                print(f"adjusted_tracks tem {len(adjusted_tracks)} itens")
                if len(adjusted_tracks) > 0:
                    print("Amostra de adjusted_tracks (até 3 itens):")
                    for i, (key, value) in enumerate(list(adjusted_tracks.items())[:3]):
                        print(f"  {key}: {value}")
            else:
                print(f"adjusted_tracks não é um dicionário, é {type(adjusted_tracks)}")
                adjusted_tracks = tracks_dict  # fallback
        except Exception as e:
            print(f"Erro ao ajustar nomes de tracks: {e}")
            print(traceback.format_exc())
            adjusted_tracks = tracks_dict

        # Verificar que total_hours e total_hours_ytd são strings válidas
        if total_hours is None or not isinstance(total_hours, str):
            print("Aviso: total_hours não é uma string válida")
            total_hours = "0:00"

        if total_hours_ytd is None or not isinstance(total_hours_ytd, str):
            print("Aviso: total_hours_ytd não é uma string válida")
            total_hours_ytd = "0:00"

        # Log do momento antes de criar os gráficos
        print("\nPronto para criar os gráficos com os dados processados")
        print("========== FIM DOS LOGS DE DIAGNÓSTICO ==========\n")

        # Função modificada para criar gráfico de tracks
        def create_tracks_graph_safe(tracks_data, height=None, max_items=None):
            """Versão segura da função create_tracks_graph que lida com diferentes tipos de entrada"""
            # from components.graphs import create_tracks_graph

            try:
                # Se tracks_data não for um dicionário, converter para dados simulados
                if not isinstance(tracks_data, dict):
                    print("Aviso: tracks_data não é um dicionário. Usando dados simulados.")
                    tracks_data = {
                        'Track 1': {'track_name': 'Track 1', 'track_time': '102:30'},
                        'Track 2': {'track_name': 'Track 2', 'track_time': '85:15'},
                        'Track 3': {'track_name': 'Track 3', 'track_time': '65:45'},
                    }

                # Chamar a função original
                return create_tracks_graph(tracks_data, height=height, max_items=max_items)
            except Exception as e:
                print(f"Erro em create_tracks_graph_safe: {e}")
                import plotly.graph_objects as go
                # Criar um gráfico vazio com mensagem de erro
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Erro ao criar gráfico: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="red")
                )
                if height is None:
                    try:
                        height = layout_config.get('chart_md_height', 180)
                    except Exception:
                        height = 180

                fig.update_layout(
                    height=height,
                    autosize=True,
                    margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                return fig

        # Criar os gráficos com logs detalhados de cada etapa
        print("Criando gráfico de tracks...")
        tracks_graph = create_tracks_graph_safe(adjusted_tracks, height=None, max_items=8)
        print("Gráfico de tracks criado!")

        print("Criando gráfico de áreas...")
        areas_graph = create_areas_graph(areas_df, height=None)
        print("Gráfico de áreas criado!")

        print("Criando gráfico de clientes...")
        customers_graph = create_customers_stacked_graph(dfs['customers_ytd'], height=None)
        print("Gráfico de clientes criado!")

        # Retornar as seções com os gráficos
        return [
            # Seção de Utilização por Tracks
            create_section_container([
                create_section_header('UTILIZAÇÃO POR TRACKS', f"{total_hours} hr"),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section('monthly-tracks-graph', tracks_graph)
                    ]
                )
            ], margin_bottom='4px'),

            # Utilização por Áreas
            create_section_container([
                create_section_header('UTILIZAÇÃO POR ÁREAS', f"{total_hours} hr"),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section('monthly-areas-graph', areas_graph)
                    ]
                )
            ], margin_bottom='4px'),

            # Seção de Utilização por Clientes
            create_section_container([
                create_section_header('UTILIZAÇÃO POR CLIENTES', total_hours_ytd),
                html.Div(
                    className='panel-content',
                    children=[
                        create_graph_section('ytd-customers-graph', customers_graph)
                    ]
                )
            ], margin_bottom='0px')
        ]

    except Exception as e:
        print(f"ERRO em create_tracks_areas_column: {e}")
        print(traceback.format_exc())
        # Em caso de erro, retornar contêineres vazios
        return [
            create_section_container([
                create_section_header('UTILIZAÇÃO POR TRACKS', f"{total_hours} hr"),
                html.Div(className='panel-content', children=[
                    html.Div("Erro ao carregar dados", className="error-message")
                ])
            ], margin_bottom='4px'),
            create_section_container([
                create_section_header('UTILIZAÇÃO POR ÁREAS', f"{total_hours} hr"),
                html.Div(className='panel-content', children=[
                    html.Div("Erro ao carregar dados", className="error-message")
                ])
            ], margin_bottom='4px'),
            create_section_container([
                create_section_header('UTILIZAÇÃO POR CLIENTES', total_hours_ytd),
                html.Div(className='panel-content', children=[
                    html.Div("Erro ao carregar dados", className="error-message")
                ])
            ], margin_bottom='0px')
        ]


main_layout = html.Div(
    id='dashboard-container',
    className='dashboard-container full-screen',
    style={'height': '100vh', 'overflow': 'hidden'},
    children=[
        # Cabeçalho com seletor de mês
        create_header("", "", available_months),

        # # Container para o conteúdo que será atualizado
        html.Div(
            id='dashboard-content',
            className='dashboard-content three-column-layout',
            style={
                'marginTop': '5px',  # Adicione margem para separar do header
                'paddingBottom': '5px',  # Espaço para o footer
                'maxHeight': 'calc(100vh - 80px)'  # Altura restrita para não sobrepor o footer
            },
            children=[html.Div("Selecione um mês para carregar os dados...", className="loading-message")]
        ),

        html.Div(
            className='footer',
            style={
                'position': 'fixed',
                'bottom': '0',
                'left': '0',
                'width': '100%',
                'backgroundColor': '#f8f9fa',
                'borderTop': '1px solid #e9ecef',
                'textAlign': 'center',
                'padding': '3px 0',
                'zIndex': '1000',
                'height': '25px'
            },
            children=[
                f"zeentech VEV Dashboard • Atualizado em: {dt.now().strftime('%d/%m/%Y %H:%M')}"
            ]
        ),

        # Armazenamento de dados
        dcc.Store(id='dashboard-data-store')
    ]
)


# Definir o layout com navegação por abas
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='eja-store', data={}),
    dcc.Store(id='eja-data-store', data={}),
    html.Div(id='dummy-div-edit', style={'display': 'none'}),
    html.Div(id='dummy-div-delete', style={'display': 'none'}),
    html.Div(id='eja-delete-refresh', style={'display': 'none'}),
    html.Div(id='import-refresh', style={'display': 'none'}),
    html.Div(id='resize-trigger', style={'display': 'none'}),
    html.Div([
        dbc.Tabs(
            id='tabs',
            children=[
                dbc.Tab(label='Dashboard', tab_id='tab-dashboard'),
                dbc.Tab(label='Gerenciar EJAs', tab_id='tab-eja-manager'),
            ],
            active_tab='tab-dashboard',
        ),
    ]),
    html.Div(id='tab-content', className='tabs-content-container'),

    html.Div(
        className='footer',
        children=[
            f"zeentech VEV Dashboard • Atualizado em: {dt.now().strftime('%d/%m/%Y %H:%M')}"
        ]
    )
])


@app.callback(
    [
        Output('dashboard-data-store', 'data'),
        Output('header-date-display', 'children')
    ],
    [Input('month-selector', 'value')],
)
def load_month_data(selected_month_value):
    """Callback para carregar dados do mês selecionado"""
    # Para debugging
    print(f"Valor selecionado no dropdown: {selected_month_value}")

    if not selected_month_value:
        # Retornar dados vazios se nenhum valor for selecionado
        empty_data = {
            'status': 'no_selection',
            'message': 'Nenhum mês selecionado'
        }
        return empty_data, "Selecione um mês"

    try:
        # Extrair datas do valor selecionado (formato: "YYYY-MM-DD|YYYY-MM-DD")
        start_date_str, end_date_str = selected_month_value.split('|')

        # Formatar para exibição
        display_date = dt.strptime(start_date_str, '%Y-%m-%d')
        header_display = f"{display_date.strftime('%B').upper()} {display_date.day}"

        # Criar dados para o store com as datas de início e fim
        data = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'display_month': display_date.strftime('%B').upper(),
            'display_day': display_date.day
        }

        print(f"Período selecionado: {start_date_str} até {end_date_str}")
        return data, header_display

    except Exception as e:
        # Em caso de erro, retornar dados de erro
        error_message = str(e)
        print(f"Erro no callback do seletor de mês: {error_message}")
        error_data = {
            'status': 'error',
            'message': f'Erro: {error_message}'
        }
        return error_data, f"Erro: {error_message[:20]}..."


@app.callback(
    Output('dashboard-content', 'children'),
    [Input('dashboard-data-store', 'data')],
    prevent_initial_call=False
)
def update_dashboard_content(data):
    # from dash import html
    # import pandas as pd
    # import traceback
    # from data.database import load_dashboard_data

    if not data:
        # Caso não haja dados, exibir mensagem
        return html.Div("Selecione um mês para carregar os dados...", className="loading-message")

    # Verificar se há erro nos dados
    if 'status' in data and data['status'] == 'error':
        return html.Div(f"Erro ao carregar dados: {data.get('message', 'Erro desconhecido')}",
                        className="error-message")

    try:
        # Carregar os dados novamente com base nas datas armazenadas
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date or not end_date:
            return html.Div("Datas inválidas. Selecione um período válido.",
                            className="error-message")

        print(f"Carregando dados para o período: {start_date} até {end_date}")

        # Tentar carregar os dados, com tratamento para erro
        try:
            result = load_dashboard_data(start_date, end_date)

            # Verificar se o resultado é uma tupla com 4 elementos
            if not isinstance(result, tuple) or len(result) != 4:
                print(f"Erro: load_dashboard_data retornou {type(result)} em vez de uma tupla com 4 elementos")
                from data.mock_data import get_all_dataframes
                result = get_all_dataframes()

            # Desempacotar o resultado
            dfs, tracks_data, areas_data_df, periodo_info = result

            # Logs para depuração
            print(f"DFs carregados: {list(dfs.keys() if isinstance(dfs, dict) else [])}")
            print(f"Tracks data é None? {tracks_data is None}")
            print(f"Áreas data é None? {areas_data_df is None}")
            print(f"Periodo info é None? {periodo_info is None}")

        except Exception as e:
            # Capturar qualquer erro durante o carregamento de dados
            print(f"Erro ao carregar dados: {str(e)}")
            print(traceback.format_exc())

            # Usar dados simulados como fallback
            from data.mock_data import get_all_dataframes
            dfs, tracks_data, areas_data_df, periodo_info = get_all_dataframes()

        # Garantir que tracks_data não é None antes de passar para create_tracks_graph
        if tracks_data is None:
            tracks_data = {}  # Usar um dicionário vazio se tracks_data for None
            print("Aviso: tracks_data é None, usando dicionário vazio como fallback")

        # Garantir que areas_data_df não é None antes de passar para create_areas_graph
        if areas_data_df is None:
            from data.mock_data import get_all_dataframes
            _, _, areas_data_df, _ = get_all_dataframes()
            print("Aviso: areas_data_df é None, usando dados simulados como fallback")

        # Extrair informações do período com fallbacks seguros
        if periodo_info is None:
            periodo_info = {}
            print("Aviso: periodo_info é None, usando dicionário vazio como fallback")

        ytd_utilization_percentage = periodo_info.get('ytd_utilization_percentage', '0%')
        ytd_availability_percentage = periodo_info.get('ytd_availability_percentage', '0%')
        total_hours = periodo_info.get('total_hours', '0')
        total_hours_ytd = periodo_info.get('total_hours_ytd', '0')

        print(
            f"Valores extraídos: ytd_util={ytd_utilization_percentage}, ytd_avail={ytd_availability_percentage}, total_hours={total_hours}, total_hours_ytd={total_hours_ytd}")

        # Garantir que dfs tem todas as chaves necessárias
        required_keys = ['utilization', 'availability', 'programs', 'other_skills',
                         'internal_users', 'external_sales', 'customers_ytd']

        for key in required_keys:
            if key not in dfs:
                print(f"Aviso: chave '{key}' ausente em dfs, adicionando DataFrame vazio")
                dfs[key] = pd.DataFrame()

        print("\n-------- ANTES DE CRIAR A COLUNA DE TRACKS E ÁREAS --------")
        print(f"tracks_data (tipo): {type(tracks_data)}")
        print(f"tracks_data (tamanho): {len(tracks_data) if isinstance(tracks_data, dict) else 'não é um dicionário'}")
        print(f"areas_data_df (tipo): {type(areas_data_df)}")
        if hasattr(areas_data_df, 'shape'):
            print(f"areas_data_df (formato): {areas_data_df.shape}")
            print(f"areas_data_df (colunas): {list(areas_data_df.columns)}")
            print(f"areas_data_df (vazio?): {areas_data_df.empty}")
        print("--------------------------------------------------------\n")

        dfs['tracks_data'] = tracks_data
        dfs['areas_data_df'] = areas_data_df

        # Criar o layout de três colunas
        return html.Div(
            className='dashboard-content three-column-layout',
            children=[
                # Coluna 1: Utilização e Disponibilidade
                html.Div(
                    className='column column-small',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
                        'paddingBottom': '5px',
                    },
                    children=create_utilization_availability_column(
                        dfs,
                        ytd_utilization_percentage,
                        ytd_availability_percentage
                    )
                ),

                # Coluna 2: Utilização por Tracks, Áreas e Clientes
                # Passando tracks_data e areas_data_df diretamente como argumentos
                html.Div(
                    className='column column-medium',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
                        'paddingBottom': '5px',
                    },
                    children=create_tracks_areas_column(
                        dfs,  # dfs deve incluir tracks_data e areas_data_df
                        total_hours,
                        total_hours_ytd
                    )
                ),

                # Coluna 3: Detalhamento de Utilização
                html.Div(
                    className='column column-large',
                    style={
                        'width': '33.33%',
                        'minWidth': '200px',
                        'paddingBottom': '5px',
                    },
                    children=[
                        # Detalhamento da utilização mensal com layout otimizado e expandido
                        create_optimized_utilization_breakdown(
                            dfs,
                            total_hours
                        )
                    ]
                )
            ]
        )
    except Exception as e:
        print(f"Erro ao atualizar conteúdo do dashboard: {e}")
        print(traceback.format_exc())
        return html.Div([
            html.H4("Erro ao renderizar dashboard:"),
            html.Pre(str(e)),
            html.Hr(),
            html.P("Detalhes técnicos:"),
            html.Pre(traceback.format_exc())
        ], className="error-message")


@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab')
)
def render_tab_content(active_tab):
    if active_tab == 'tab-dashboard':
        return main_layout
    elif active_tab == 'tab-eja-manager':
        # Ao renderizar o layout do EJA Manager, também carregamos os dados iniciais
        layout = create_eja_manager_layout()

        # Pré-carregar a tabela com todos os EJAs
        eja_manager = get_eja_manager()
        all_ejas = eja_manager.get_all_ejas()

        # Encontrar o container da tabela no layout e atualizar seu conteúdo
        for child in layout.children:
            if isinstance(child, dbc.Card) and hasattr(child, 'children'):
                for card_child in child.children:
                    if isinstance(card_child, dbc.CardBody) and hasattr(card_child, 'children'):
                        for body_child in card_child.children:
                            if hasattr(body_child, 'id') and body_child.id == "eja-table-container":
                                body_child.children = create_eja_table(all_ejas)

        return layout
    return html.Div("Conteúdo não encontrado")


app.clientside_callback(
    """
    function() {
        // Calcula a altura disponível quando a aba é carregada
        var windowHeight = window.innerHeight;
        var tableContainer = document.querySelector('.eja-table-container');

        if (tableContainer) {
            var tableTop = tableContainer.offsetTop;
            var paginationHeight = 100; // Espaço para paginação e outras informações
            var availableHeight = windowHeight - tableTop - paginationHeight;

            // Certifique-se de que a altura não seja muito pequena
            availableHeight = Math.max(availableHeight, 300);

            // Define a variável CSS
            document.documentElement.style.setProperty('--table-height', availableHeight + 'px');
        }

        return '';
    }
    """,
    Output('resize-trigger', 'children'),
    Input('tabs', 'active_tab')
)


# Callback para abrir o modal de importação
@callback(
    Output("import-modal", "is_open"),
    Input("import-csv-button", "n_clicks"),
    Input("cancel-import-button", "n_clicks"),
    State("import-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_import_modal(import_click, cancel_click, is_open):
    if import_click or cancel_click:
        return not is_open
    return is_open


@callback(
    Output("delete-eja-modal", "is_open"),
    Output("delete-confirmation-message", "children"),
    Output("delete-eja-id", "value"),
    Input({"type": "delete-button", "index": dash.ALL, "action": "delete"}, "n_clicks"),
    Input("cancel-delete-button", "n_clicks"),
    prevent_initial_call=True
)
def show_delete_confirmation(delete_clicks, cancel_click):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Obter o ID completo do elemento que disparou o callback
    trigger_full = ctx.triggered[0]['prop_id']
    trigger_id = trigger_full.split('.')[0]

    trace(f"show_delete_confirmation: {trigger_full=}")

    # Para o botão cancelar
    if "cancel-delete-button" in trigger_full:
        return False, "", ""

    if delete_clicks and any(click for click in delete_clicks if click):
        # Identificar qual botão foi clicado
        triggered_id = json.loads(trigger_full.split(".")[0])
        row_id = triggered_id["index"]

        # Buscar informações do EJA
        eja_manager = get_eja_manager()
        eja = eja_manager.get_eja_by_id(row_id)

        if eja:
            # Obter código e título
            eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
            title = eja.get('TITLE', eja.get('title', ''))

            # Criar mensagem de confirmação
            message = f"Tem certeza que deseja excluir o EJA #{row_id} ({eja_code} - {title})?"
            return True, message, row_id

    # Log para depuração
    print(f"DEBUG - show_delete_confirmation triggered by: {trigger_full}")

    # Para o botão cancelar
    if trigger_id == "cancel-delete-button":
        return False, "", ""

    # Para botões de exclusão - verificação mais rigorosa
    try:
        # Verificar explicitamente se o ID corresponde ao padrão esperado
        if '{"type":"delete-button"' in trigger_id:
            try:
                trigger_dict = json.loads(trigger_id)
                if isinstance(trigger_dict, dict) and trigger_dict.get("type") == "delete-button":
                    row_id = trigger_dict.get("index")
                    if row_id:
                        # Buscar informações do EJA
                        eja_manager = get_eja_manager()
                        eja = eja_manager.get_eja_by_id(row_id)

                        if eja:
                            # Obter código e título
                            eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
                            title = eja.get('TITLE', eja.get('title', ''))
                            # Criar mensagem de confirmação
                            message = f"Tem certeza que deseja excluir o EJA #{row_id} ({eja_code} - {title})?"
                            return True, message, row_id
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSONDecodeError: {str(e)} for trigger_id: {trigger_id}")
                raise PreventUpdate

        # Se chegou aqui, o trigger não é um botão de exclusão válido
        print(f"DEBUG - Not a valid delete button: {trigger_id}")
        raise PreventUpdate
    except Exception as e:
        print(f"DEBUG - Erro ao processar clique: {type(e).__name__}: {str(e)}")
        raise PreventUpdate


# Callback para abrir o modal de adição de EJA
@app.callback(
    [
        Output("eja-form-modal", "is_open"),
        Output("eja-form-title", "children"),
        Output("form-mode", "value"),
        Output("eja-code-input", "value"),
        Output("eja-title-input", "value"),
        Output("eja-classification-input", "value"),
        Output("edit-eja-id", "value")
    ],
    [
        Input("add-eja-button", "n_clicks"),
        Input("cancel-eja-form-button", "n_clicks"),
        Input({"type": "edit-button", "index": dash.ALL}, "n_clicks"),
    ],
    [
        State("eja-form-modal", "is_open"),
    ],
    prevent_initial_call=True
)
def toggle_eja_form_modal(add_clicks, cancel_clicks, edit_clicks, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Adicionar novo EJA - abrir modal vazio
    if trigger_id == "add-eja-button":
        return True, "Adicionar Novo EJA", "add", "", "", "", ""

    # Cancelar - fechar modal
    if trigger_id == "cancel-eja-form-button":
        return False, "", "", "", "", "", ""

    # Editar EJA existente
    if isinstance(trigger_id, dict) and trigger_id.get("type") == "edit-button":
        eja_id = trigger_id.get("index")
        if eja_id:
            # Obter os dados do EJA para edição
            eja_manager = get_eja_manager()
            eja = eja_manager.get_eja_by_id(eja_id)

            if eja:
                # Obter os valores para os campos do formulário
                eja_code = eja.get('EJA CODE', eja.get('eja_code', ''))
                title = eja.get('TITLE', eja.get('title', ''))
                classification = eja.get('NEW CLASSIFICATION', eja.get('new_classification', ''))

                return True, f"Editar EJA #{eja_id}", "edit", eja_code, title, classification, eja_id

    # Caso padrão - não altera o estado atual
    return is_open, "", "", "", "", "", ""


# Callback unificado para gerenciar todas as atualizações da tabela EJA
@callback(
    Output("eja-table-container", "children"),
    Output("eja-data-store", "data"),
    [
        Input({"type": "search-button", "action": "search"}, "n_clicks"),
        Input("eja-delete-refresh", "children"),
        Input("import-refresh", "children"),
        Input("eja-pagination", "active_page")
    ],
    [
        State("search-term", "value"),
        State("search-eja-code", "value"),
        State("eja-data-store", "data")
    ],
    prevent_initial_call=True
)
def update_eja_table(
    search_clicks, delete_refresh, import_refresh, active_page,
    search_term, eja_code, data_store
):
    # Determinar qual input disparou o callback
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Identificar o acionador com informações completas
    trigger_full = ctx.triggered[0]['prop_id']
    trigger_id = trigger_full.split('.')[0]

    # Log para depuração
    print(f"DEBUG - update_eja_table triggered by: {trigger_full}")

    # Carregar o gerenciador de EJAs
    eja_manager = get_eja_manager()

    # Processar de acordo com o acionador
    if trigger_id == "search-button" and search_clicks:
        # Busca de EJAs
        print(f"DEBUG - Search triggered with: term={search_term}, code={eja_code}")
        filtered_ejas = eja_manager.search_ejas(search_term=search_term, eja_code=eja_code)
        print(f"DEBUG - Search returned {len(filtered_ejas)} items")

        # Atualizar o data_store com os resultados filtrados
        data_store['filtered_ejas'] = filtered_ejas
        data_store['page_current'] = 0

        return create_eja_table(filtered_ejas, page_current=0), data_store

    elif trigger_id in ["eja-delete-refresh", "import-refresh"]:
        # Atualização após exclusão ou importação
        all_ejas = eja_manager.get_all_ejas()

        # Resetar para mostrar todos os EJAs
        data_store['filtered_ejas'] = all_ejas
        data_store['page_current'] = 0

        return create_eja_table(all_ejas, page_current=0), data_store

    elif trigger_id == "eja-pagination":
        # Atualização de paginação
        if not active_page:
            raise PreventUpdate

        # Ajustar página (UI é base 1, código é base 0)
        page_current = active_page - 1
        data_store['page_current'] = page_current

        # Usar os dados filtrados atuais (não buscar todos novamente)
        filtered_ejas = data_store.get('filtered_ejas', [])
        if not filtered_ejas:
            filtered_ejas = eja_manager.get_all_ejas()
            data_store['filtered_ejas'] = filtered_ejas

        return create_eja_table(filtered_ejas, page_current=page_current), data_store

    # Caso padrão - não atualizar
    raise PreventUpdate


def create_search_button():
    """
    Cria um botão de busca com um ID exclusivo para evitar conflitos com outros callbacks
    """
    return dbc.Button(
        "Buscar",
        id={"type": "search-button", "action": "search"},
        color="primary",
        className="mr-2"
    )


@callback(
    Output("eja-table-container", "children", allow_duplicate=True),
    Output("eja-data-store", "data", allow_duplicate=True),
    [
        Input({"type": "search-button", "action": "search"}, "n_clicks"),
    ],
    [
        State("search-term", "value"),
        State("search-eja-code", "value"),
        State("eja-data-store", "data")
    ],
    prevent_initial_call=True
)
def handle_search_button(
    search_clicks, search_term, eja_code, data_store
):
    if not search_clicks:
        raise PreventUpdate

    # Log para depuração
    print(f"DEBUG - handle_search_button triggered with: term={search_term}, code={eja_code}")

    # Carregar o gerenciador de EJAs
    eja_manager = get_eja_manager()

    # Busca de EJAs
    filtered_ejas = eja_manager.search_ejas(search_term=search_term, eja_code=eja_code)
    print(f"DEBUG - Search returned {len(filtered_ejas)} items")

    # Atualizar o data_store com os resultados filtrados
    data_store['filtered_ejas'] = filtered_ejas
    data_store['page_current'] = 0

    return create_eja_table(filtered_ejas, page_current=0), data_store


@callback(
    [
        Output("eja-delete-status", "is_open", allow_duplicate=True),
        Output("eja-delete-status", "children", allow_duplicate=True),
        Output("eja-delete-status", "header", allow_duplicate=True),
        Output("eja-delete-status", "color", allow_duplicate=True),
        Output("eja-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("confirm-delete-button", "n_clicks"),
    State("delete-eja-id", "value"),
    prevent_initial_call=True
)
def delete_eja(confirm_click, eja_id):
    if not confirm_click or not eja_id:
        raise PreventUpdate

    # Realizar a exclusão
    eja_manager = get_eja_manager()
    success = eja_manager.delete_eja(eja_id)

    # Gerar timestamp único para atualização da tabela
    import time
    refresh_time = str(time.time())

    if success:
        return True, "EJA excluído com sucesso!", "Exclusão Concluída", "success", refresh_time
    else:
        return True, "Erro ao excluir o EJA.", "Erro", "danger", no_update


@callback(
    Output("delete-eja-modal", "is_open", allow_duplicate=True),
    Input("confirm-delete-button", "n_clicks"),
    prevent_initial_call=True
)
def close_delete_modal(n_clicks):
    if n_clicks:
        return False
    raise PreventUpdate


# Callback para salvar o EJA (novo ou editado)
@app.callback(
    [
        Output("eja-form-status", "is_open"),
        Output("eja-form-status", "children"),
        Output("eja-form-status", "header"),
        Output("eja-form-status", "color"),
        Output("eja-form-modal", "is_open", allow_duplicate=True),
        Output("eja-delete-refresh", "children", allow_duplicate=True)
    ],
    Input("save-eja-form-button", "n_clicks"),
    [
        State("form-mode", "value"),
        State("edit-eja-id", "value"),
        State("eja-code-input", "value"),
        State("eja-title-input", "value"),
        State("eja-classification-input", "value"),
    ],
    prevent_initial_call=True
)
def save_eja_form(n_clicks, form_mode, edit_eja_id, eja_code, title, classification):
    if not n_clicks:
        raise PreventUpdate

    # Validar campos obrigatórios
    if not eja_code or not title:
        return True, "Preencha todos os campos obrigatórios.", "Erro", "danger", True, no_update

    try:
        # Preparar os dados do EJA
        eja_data = {
            "eja_code": eja_code,
            "title": title,
            "new_classification": classification or ""  # Garantir que nunca seja None
        }

        # Obter gerenciador de EJAs
        eja_manager = get_eja_manager()

        # Adicionar ou atualizar o EJA dependendo do modo
        if form_mode == "add":
            result = eja_manager.add_eja(eja_data)
            success_message = "EJA adicionado com sucesso!"
            error_prefix = "Erro ao adicionar EJA:"
        else:  # mode == "edit"
            result = eja_manager.update_eja(edit_eja_id, eja_data)
            success_message = "EJA atualizado com sucesso!"
            error_prefix = "Erro ao atualizar EJA:"

        # Verificar resultado
        if isinstance(result, dict) and result.get('error'):
            return True, f"{error_prefix} {result['error']}", "Erro", "danger", True, no_update

        # Gerar timestamp para atualizar a tabela
        import time
        refresh_time = str(time.time())

        # Sucesso - fechar modal e mostrar mensagem
        return True, success_message, "Sucesso", "success", False, refresh_time

    except Exception as e:
        # Erro - mostrar mensagem mas manter modal aberto
        return True, f"Erro: {str(e)}", "Erro", "danger", True, no_update


# Callback for handling CSV export
@callback(
    Input("export-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_csv_export(n_clicks):
    if not n_clicks:
        raise PreventUpdate

    try:
        # Export the EJA data using the manager
        eja_manager = get_eja_manager()
        export_path = eja_manager.export_csv()

        if export_path and os.path.exists(export_path):
            return True, f"Dados exportados com sucesso para: {export_path}", "Exportação Concluída", "success"
        else:
            return True, f"Erro ao exportar: {export_path}", "Erro", "danger"
    except Exception as e:
        return True, f"Erro ao exportar: {str(e)}", "Erro", "danger"


# Callback para processar a importação de CSV
@callback(
    Input("import-csv-button", "n_clicks"),
    State("upload-csv", "contents"),
    State("upload-csv", "filename"),
    State("overwrite-checkbox", "value"),
    prevent_initial_call=True
)
def process_csv_import(n_clicks, contents, filename, overwrite):
    if not n_clicks or not contents:
        raise PreventUpdate

    try:
        # Decodificar o conteúdo do arquivo
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp:
            temp.write(decoded)
            temp_path = temp.name

        # Importar usando o gerenciador de EJAs
        eja_manager = get_eja_manager()
        overwrite_flag = overwrite and "overwrite" in overwrite
        result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

        # Remover o arquivo temporário
        os.unlink(temp_path)

        # Verificar resultado
        if 'error' in result:
            return True, result['error'], "Erro na Importação", "danger", no_update, False

        # Mensagem de sucesso
        if overwrite_flag:
            message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
        else:
            message = f"Importação concluída! Adicionados: {result.get('imported', 0)}, Atualizados: {result.get('updated', 0)}, Ignorados: {result.get('skipped', 0)}."

        # Gerar timestamp único para atualização da tabela
        import time
        refresh_time = str(time.time())

        return True, message, "Importação Concluída", "success", refresh_time, False

    except Exception as e:
        return True, f"Erro ao processar arquivo: {str(e)}", "Erro", "danger", no_update, False


# Callback for handling file upload and import
@callback(
    Input("upload-csv", "contents"),
    Input("import-csv-button", "n_clicks"),
    Input("cancel-import-button", "n_clicks"),
    State("upload-csv", "filename"),
    State("overwrite-checkbox", "value"),
    State("import-modal", "is_open"),
    prevent_initial_call=True
)
def handle_csv_import(contents, import_click, cancel_click, filename, overwrite, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Cancel button - close modal
    if trigger_id == "cancel-import-button":
        return False, "", "", "", False, no_update

    # Upload file - store content
    if trigger_id == "upload-csv" and contents is not None:
        # Store content in hidden div for later use
        return False, "", "", "", is_open, json.dumps({"filename": filename, "content": contents})

    # Import button - process file
    if trigger_id == "import-csv-button" and import_click:
        # Get stored content
        if not dash.callback_context.states['import-refresh.children']:
            return True, "Nenhum arquivo selecionado", "Erro", "danger", False, no_update

        try:
            # Parse stored content
            stored_data = json.loads(dash.callback_context.states['import-refresh.children'])
            content_string = stored_data['content'].split(',')[1]
            decoded = base64.b64decode(content_string)

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                tmp.write(decoded)
                temp_path = tmp.name

            # Import CSV using the EJA manager
            eja_manager = get_eja_manager()
            overwrite_flag = overwrite and "overwrite" in overwrite
            result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

            # Remove temp file
            os.unlink(temp_path)

            # Handle result
            if 'error' in result:
                return True, result['error'], "Erro na Importação", "danger", False, ""

            # Success message
            if overwrite_flag:
                message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
            else:
                message = f"Importação concluída! Adicionados: {result.get('imported', 0)}, Atualizados: {result.get('updated', 0)}, Ignorados: {result.get('skipped', 0)}."

            # Generate unique timestamp for refreshing the table
            import time
            refresh_time = str(time.time())

            return True, message, "Importação Concluída", "success", False, refresh_time

        except Exception as e:
            return True, f"Erro ao processar arquivo: {str(e)}", "Erro", "danger", False, ""

    # Open/close modal on button click
    if trigger_id == "import-csv-button":
        return False, "", "", "", not is_open, no_update

    # Default - no change
    return False, "", "", "", is_open, no_update


# Callback unificado para gerenciar todas as mensagens de status
@callback(
    [
        Output("export-status", "is_open"),
        Output("export-status", "children"),
        Output("export-status", "header"),
        Output("export-status", "color"),
        Output("import-status", "is_open"),
        Output("import-status", "children"),
        Output("import-status", "header"),
        Output("import-status", "color"),
        Output("import-refresh", "children"),
        Output("eja-delete-status", "is_open", allow_duplicate=True),
        Output("eja-delete-status", "children", allow_duplicate=True),
        Output("eja-delete-status", "header", allow_duplicate=True),
        Output("eja-delete-status", "color", allow_duplicate=True),
        Output("eja-delete-refresh", "children", allow_duplicate=True),
    ],
    [
        Input("export-button", "n_clicks"),
        Input("import-csv-button", "n_clicks"),
        Input("confirm-delete-button", "n_clicks")
    ],
    [
        State("upload-csv", "contents"),
        State("upload-csv", "filename"),
        State("overwrite-checkbox", "value"),
        State("delete-eja-id", "value")
    ],
    prevent_initial_call=True
)
def handle_all_status_messages(
    export_clicks, import_clicks, confirm_delete_clicks,
    csv_contents, csv_filename, overwrite, eja_id
):
    # Valores padrão para todos os outputs (para não alterar componentes não afetados)
    defaults = [
        False, "", "", "",  # export-status
        False, "", "", "", None,  # import-status e refresh
        False, "", "", "", None   # delete-status e refresh
    ]

    # Determinar qual input disparou o callback
    ctx = callback_context

    if not ctx.triggered:
        return defaults

    # Identificar o acionador
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Gerar timestamp para atualização quando necessário
    import time
    refresh_time = str(time.time())

    # Processar exportação CSV
    if trigger_id == "export-button" and export_clicks:
        try:
            # Exportar usando o gerenciador de EJAs
            eja_manager = get_eja_manager()
            export_path = eja_manager.export_csv()

            if export_path and os.path.exists(export_path):
                # Atualizar apenas os outputs do export-status
                results = defaults.copy()
                results[0] = True  # is_open
                results[1] = f"Dados exportados com sucesso para: {export_path}"  # children
                results[2] = "Exportação Concluída"  # header
                results[3] = "success"  # color
                return results
            else:
                results = defaults.copy()
                results[0] = True
                results[1] = f"Erro ao exportar: {export_path}"
                results[2] = "Erro"
                results[3] = "danger"
                return results
        except Exception as e:
            results = defaults.copy()
            results[0] = True
            results[1] = f"Erro ao exportar: {str(e)}"
            results[2] = "Erro"
            results[3] = "danger"
            return results

    # Processar importação CSV
    elif trigger_id == "import-csv-button" and import_clicks:
        if not csv_contents:
            results = defaults.copy()
            results[4] = True
            results[5] = "Nenhum arquivo selecionado"
            results[6] = "Erro"
            results[7] = "danger"
            return results

        try:
            # Decodificar o conteúdo do arquivo
            content_type, content_string = csv_contents.split(',')
            decoded = base64.b64decode(content_string)

            # Salvar em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp:
                temp.write(decoded)
                temp_path = temp.name

            # Importar usando o gerenciador de EJAs
            eja_manager = get_eja_manager()
            overwrite_flag = overwrite and "overwrite" in overwrite
            result = eja_manager.import_csv(temp_path, overwrite=overwrite_flag)

            # Remover o arquivo temporário
            os.unlink(temp_path)

            # Verificar resultado
            if 'error' in result:
                results = defaults.copy()
                results[4] = True
                results[5] = result['error']
                results[6] = "Erro na Importação"
                results[7] = "danger"
                return results

            # Mensagem de sucesso
            if overwrite_flag:
                message = f"Importação concluída com sucesso! {result.get('imported', 0)} registros importados."
            else:
                message = f"Importação concluída! Adicionados: {result.get('imported', 0)}, Atualizados: {result.get('updated', 0)}, Ignorados: {result.get('skipped', 0)}."

            results = defaults.copy()
            results[4] = True  # import-status.is_open
            results[5] = message  # import-status.children
            results[6] = "Importação Concluída"  # import-status.header
            results[7] = "success"  # import-status.color
            results[8] = refresh_time  # import-refresh.children
            return results

        except Exception as e:
            results = defaults.copy()
            results[4] = True
            results[5] = f"Erro ao processar arquivo: {str(e)}"
            results[6] = "Erro"
            results[7] = "danger"
            return results

    # Processar exclusão de EJA
    elif trigger_id == "confirm-delete-button" and confirm_delete_clicks and eja_id:
        # Realizar a exclusão
        eja_manager = get_eja_manager()
        success = eja_manager.delete_eja(eja_id)

        if success:
            results = defaults.copy()
            results[9] = True  # eja-delete-status.is_open
            results[10] = "EJA excluído com sucesso!"  # eja-delete-status.children
            results[11] = "Exclusão Concluída"  # eja-delete-status.header
            results[12] = "success"  # eja-delete-status.color
            results[13] = refresh_time  # eja-delete-refresh.children
            return results
        else:
            results = defaults.copy()
            results[9] = True
            results[10] = "Erro ao excluir o EJA."
            results[11] = "Erro"
            results[12] = "danger"
            return results

    # Caso padrão
    return defaults


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }

            /* Container principal com espaço reservado para o footer */
            .dashboard-container {
                height: calc(100vh - 35px) !important;
                max-height: calc(100vh - 35px) !important;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                padding-bottom: 35px;
            }

            /* Conteúdo principal com altura limitada */
            .dashboard-content {
                flex: 1;
                overflow: hidden;
                display: flex;
                /* Altura máxima para não sobrepor o footer */
                max-height: calc(100vh - 80px) !important;
                padding-bottom: 40px;
            }

            /* Estilo das colunas */
            .column {
                height: 100%;
                overflow-y: auto;
                padding: 0 8px;
                /* Importante: limitar a altura da coluna também */
                max-height: calc(100vh - 90px);
                padding-bottom: 40px;
            }

            /* Footer sempre na parte inferior */
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 30px; /* Altura fixa para o footer */
                background-color: #f8f9fa;
                text-align: center;
                padding: 5px 0;
                font-size: 12px;
                color: #666;
                border-top: 1px solid #e9ecef;
                z-index: 1000;
            }

            /* Garantir que o conteúdo das abas respeite o footer */
            #tab-content, .tabs-content-container {
                padding-bottom: 35px; /* Espaço para o footer */
                overflow: hidden;
                height: calc(100vh - 75px); /* header + tabs + footer */
            }

            /* Ajustes para a tabela EJA */
            .eja-table-container {
                height: calc(100vh - 270px) !important;
                overflow-y: auto !important;
                max-height: none !important;
                margin-bottom: 40px; /* Espaço extra no final */
            }

            /* Ajustes para gráficos */
            .chart-container {
                min-height: 0 !important;
                height: auto !important;
                margin-bottom: 10px !important;
            }

            /* Garantir que os conteúdos dos painéis sejam visíveis */
            .panel-content {
                height: auto !important;
                min-height: 0 !important;
                overflow: visible !important;
            }

            /* Responsividade */
            @media (max-height: 768px) {
                .dashboard-content, .column, #tab-content, .tabs-content-container {
                    max-height: calc(100vh - 75px);
                }

                .footer {
                    height: 25px;
                    padding: 3px 0;
                }

                .dashboard-container {
                    height: calc(100vh - 30px);
                    max-height: calc(100vh - 30px);
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
