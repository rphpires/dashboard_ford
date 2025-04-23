# layouts/center_column.py
from dash import html

from utils.tracer import *
from utils.helpers import *

from config.layout_config import layout_config

from data.tracks_manager import adjust_tracks_names

from components.sections import (
    create_section_container, create_section_header,
    create_graph_section
)
from components.graphs import (
    create_tracks_graph, create_areas_graph,
    create_customers_stacked_graph
)


def create_track_section(tracks_data, total_hours):
    try:
        print("Criando gráfico de tracks...")
        tracks_graph = create_tracks_graph_safe(tracks_data, height=None, max_items=8)
        print("Gráfico de tracks criado!")

        # Calcular o total real para tracks
        tracks_total = "0:00"
        if isinstance(tracks_data, dict) and tracks_data:
            total_minutes = 0
            for track_info in tracks_data.values():
                if isinstance(track_info, dict) and 'track_time' in track_info:
                    track_time = track_info['track_time']
                    if track_time and ':' in track_time:
                        hours, minutes = map(int, track_time.split(':'))
                        total_minutes += hours * 60 + minutes

            # Converter minutos totais para formato HH:MM
            tracks_hours = total_minutes // 60
            # tracks_minutes = total_minutes % 60
            tracks_total = f"{tracks_hours} hr"

        return create_section_container([
            create_section_header('Tracks Utilization (monthly)', tracks_total),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section('monthly-tracks-graph', tracks_graph)
                ]
            )
        ], margin_bottom='4px')
    except Exception as e:
        print(f"Erro ao criar seção de tracks: {e}")
        return create_section_container([
            create_section_header('Tracks Utilization', f"{tracks_total} hr"),
            html.Div(className='panel-content', children=[
                html.Div("Erro ao carregar dados", className="error-message")
            ])
        ], margin_bottom='4px')


def create_areas_section(areas_df, total_hours):
    try:
        print("Criando gráfico de áreas...")
        areas_graph = create_areas_graph(areas_df, height=None)
        print("Gráfico de áreas criado!")

        # Calcular o total real para áreas
        areas_total = "0:00"
        if isinstance(areas_df, pd.DataFrame) and not areas_df.empty and 'hours' in areas_df.columns:
            total_hours_decimal = areas_df['hours'].sum()
            areas_hours = int(total_hours_decimal)
            # areas_minutes = int((total_hours_decimal - areas_hours) * 60)
            areas_total = f"{areas_hours} hr"

        return create_section_container([
            create_section_header('Areas Utilization (monthly)', areas_total),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section('monthly-areas-graph', areas_graph)
                ]
            )
        ], margin_bottom='4px')
    except Exception as e:
        print(f"Erro ao criar seção de áreas: {e}")
        return create_section_container([
            create_section_header('Areas Utilization', f"{areas_total} hr"),
            html.Div(className='panel-content', children=[
                html.Div("Erro ao carregar dados", className="error-message")
            ])
        ], margin_bottom='4px')


def create_customers_section(customers_df, total_hours_ytd):
    try:
        print("Criando gráfico de clientes...")
        customers_graph, df_sorted = create_customers_stacked_graph(customers_df, height=None)
        print("Gráfico de clientes criado!")

        # Calcular o total real para clientes
        total_hours = str(df_sorted["hours_int"].sum())
        clients_total = f"{str(total_hours)} hr"

        return create_section_container([
            create_section_header('Clients Utilization (Last 12 Months)', clients_total),
            html.Div(
                className='panel-content',
                children=[
                    create_graph_section('ytd-customers-graph', customers_graph)
                ]
            )
        ], margin_bottom='0px')

    except Exception as e:
        print(f"Erro ao criar seção de clientes: {e}")
        return create_section_container([
            create_section_header('Clients Utilization', clients_total),
            html.Div(className='panel-content', children=[
                html.Div("Erro ao carregar dados", className="error-message")
            ])
        ], margin_bottom='0px')


def create_tracks_graph_safe(tracks_data, height=None, max_items=None):
    """Versão segura da função create_tracks_graph que lida com diferentes tipos de entrada"""
    try:
        # Verificação simplificada para determinar se há dados
        has_data = False

        if isinstance(tracks_data, dict) and len(tracks_data) > 0:
            has_data = True
        elif isinstance(tracks_data, pd.DataFrame) and not tracks_data.empty:
            has_data = True

        if not has_data:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(
                text="Nenhum valor neste mês",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="#666666")
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

        # Chamar a função original se houver dados
        return create_tracks_graph(tracks_data, height=height, max_items=max_items)
    except Exception as e:
        print(f"Erro em create_tracks_graph_safe: {e}")
        # Criar um gráfico vazio com mensagem de erro
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum valor neste mês",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#666666")
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


def create_tracks_areas_column(dfs, total_hours, total_hours_ytd):
    try:
        # Processar os diferentes tipos de dados
        tracks_dict = process_tracks_data(dfs)
        areas_df = process_areas_data(dfs)
        customers_df = process_customers_data(dfs)

        # Validar e ajustar as variáveis total_hours e total_hours_ytd
        if total_hours is None or not isinstance(total_hours, str):
            print("Aviso: total_hours não é uma string válida")
            total_hours = "0:00"

        if total_hours_ytd is None or not isinstance(total_hours_ytd, str):
            print("Aviso: total_hours_ytd não é uma string válida")
            total_hours_ytd = "0:00"

        # Tentar ajustar os nomes dos tracks, se aplicável
        adjusted_tracks = tracks_dict
        try:
            adjusted_tracks = adjust_tracks_names(tracks_dict)
            print("Tracks ajustados com adjust_tracks_names()")
            print_dict_info(adjusted_tracks, "adjusted_tracks")
        except Exception as e:
            print(f"Erro ao ajustar nomes de tracks: {e}")
            print(traceback.format_exc())

        # Criar seções para visualização
        tracks_section = create_track_section(adjusted_tracks, total_hours)
        areas_section = create_areas_section(areas_df, total_hours)
        customers_section = create_customers_section(customers_df, total_hours_ytd)

        return [tracks_section, areas_section, customers_section]

    except Exception as e:
        print(f"ERRO em create_tracks_areas_column: {e}")
        print(traceback.format_exc())

        # Em caso de erro, retornar contêineres vazios
        return [
            create_section_container([
                create_section_header('Tracks Utilization', f"{total_hours} hr"),
                html.Div(className='panel-content', children=[
                    html.Div("Erro ao carregar dados", className="error-message")
                ])
            ], margin_bottom='4px'),
            create_section_container([
                create_section_header('Areas Utilization', f"{total_hours} hr"),
                html.Div(className='panel-content', children=[
                    html.Div("Erro ao carregar dados", className="error-message")
                ])
            ], margin_bottom='4px'),
            create_section_container([
                create_section_header('Clients Utilization', total_hours_ytd),
                html.Div(className='panel-content', children=[
                    html.Div("Erro ao carregar dados", className="error-message")
                ])
            ], margin_bottom='0px')
        ]
