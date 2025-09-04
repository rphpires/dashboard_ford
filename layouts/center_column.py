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
    """
    Cria a seção de clientes com tratamento robusto de erros
    """
    # Inicializar valores padrão
    clients_total = "0 hr"
    customers_graph = None

    try:
        print("Criando gráfico de clientes...")

        # Tentar criar o gráfico de clientes
        try:
            # Verificar se a função retorna 1 ou 2 valores
            result = create_customers_stacked_graph(customers_df, height=None)

            # Se retornar apenas o gráfico
            if not isinstance(result, tuple):
                customers_graph = result
                df_sorted = customers_df  # Usar o DataFrame original
            else:
                # Se retornar tupla, desempacotar
                if len(result) == 2:
                    customers_graph, df_sorted = result
                else:
                    customers_graph = result[0]
                    df_sorted = customers_df

        except Exception as graph_error:
            print(f"Erro específico ao criar gráfico de clientes: {graph_error}")
            # Criar um gráfico vazio em caso de erro
            import plotly.graph_objects as go
            customers_graph = go.Figure()
            customers_graph.add_annotation(
                text="Erro ao carregar dados de clientes",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="#666666")
            )
            customers_graph.update_layout(
                height=180,
                autosize=True,
                margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            df_sorted = pd.DataFrame()

        print("Gráfico de clientes criado!")

        try:
            # Calcular total correto dos dados processados
            if isinstance(customers_df, pd.DataFrame) and not customers_df.empty and 'hours' in customers_df.columns:
                correct_total = int(customers_df['hours'].sum())
                clients_total = f"{correct_total} HR"
                print(f"CORRECAO: Total correto calculado: {correct_total}")
            else:
                clients_total = "0 HR"
        except Exception as e:
            print(f"Erro ao calcular total correto: {e}")
            clients_total = "0 HR"

    except Exception as e:
        trace(f"Erro geral ao criar seção de clientes: {e}")
        import traceback
        print(traceback.format_exc())

        # Criar gráfico vazio em caso de erro geral
        import plotly.graph_objects as go
        customers_graph = go.Figure()
        customers_graph.add_annotation(
            text="Erro ao carregar dados",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#666666")
        )
        customers_graph.update_layout(
            height=180,
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        clients_total = "0 hr"

    return create_section_container([
        create_section_header('Clients Utilization (Last 12 Months)', clients_total),
        html.Div(
            className='panel-content',
            children=[
                create_graph_section('ytd-customers-graph', customers_graph)
            ]
        )
    ], margin_bottom='0px')


def safe_process_customers_data(dfs):
    """
    Processa dados de clientes históricos - retorna DataFrame
    """
    print("=== DEBUG: safe_process_customers_data iniciada ===")

    try:
        from data.local_db_handler import get_db_handler
        db_handler = get_db_handler()

        # Query EXATA que funciona no banco
        query = """
            SELECT 
                e.new_classification as classification,
                COUNT(*) as registros,
                SUM(c.hours) as total_minutos,
                ROUND(SUM(c.hours) / 60.0, 2) as total_horas
            FROM clients_usage c
            INNER JOIN eja e ON c.classification = e.eja_code
            WHERE e.new_classification IS NOT NULL
              AND e.new_classification != ''
            GROUP BY e.new_classification
            ORDER BY total_minutos DESC
        """

        print("Executando query exata do banco...")
        cursor = db_handler.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"Query retornou {len(rows)} resultados:")

        if not rows:
            print("Nenhum resultado retornado")
            import pandas as pd
            return pd.DataFrame(columns=['classification', 'hours'])

        # Criar dados exatamente como na query
        result_data = []
        for row in rows:
            classification = row[0]
            registros = row[1]
            total_minutos = row[2]
            total_horas = row[3]

            print(f"  {classification}: {registros} registros, {total_minutos} min, {total_horas} horas")

            result_data.append({
                'classification': classification,
                'hours': int(total_horas),  # Usar as horas já convertidas da query
                'hours_int': int(total_horas)  # Para compatibilidade
            })

        import pandas as pd
        df_result = pd.DataFrame(result_data)

        print(f"DataFrame criado com {len(df_result)} registros")
        print(f"Colunas: {list(df_result.columns)}")
        print("Dados finais:")
        for _, row in df_result.iterrows():
            print(f"  {row['classification']}: {row['hours']} horas")

        print("=" * 40)
        return df_result

    except Exception as e:
        print(f"Erro ao processar dados de clientes: {str(e)}")
        import pandas as pd
        return pd.DataFrame(columns=['classification', 'hours'])


def create_empty_customers_data():
    """Cria dados vazios para clientes quando não há dados disponíveis"""
    print("🔧 Criando dados vazios para clientes...")
    return [
        {'classification': 'Programs', 'hours': 0},
        {'classification': 'Other Skills', 'hours': 0},
        {'classification': 'Internal Users', 'hours': 0},
        {'classification': 'External Sales', 'hours': 0}
    ]


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

        # Usar a nova função segura para processar clientes
        customers_df = safe_process_customers_data(dfs)

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
