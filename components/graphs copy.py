# components/graphs.py
# Funções para criação de gráficos do dashboard
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from config.config import colors  # Importar configurações de cores do projeto


def create_utilization_graph(df, height=180):
    """
    Criar gráfico de utilização com tamanho ajustável

    Args:
        df (pandas.DataFrame): DataFrame com dados de utilização
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de utilização
    """
    if height is None:
        height = layout_config['chart_sm_height']

    fig = go.Figure()

    # Adicionar barras para dados mensais
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['utilization'],
        name='Utilização Mensal',
        marker_color='#1976D2',
        hovertemplate='%{y:.1f}%<extra></extra>'
    ))

    # Adicionar linha para meta
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=[80] * len(df),  # Valor da meta
        mode='lines',
        name='Meta',
        line=dict(color='#F57C00', width=2, dash='dash'),
        hovertemplate='Meta: 80%<extra></extra>'
    ))

    # Configurar layout
    fig.update_layout(
        margin={'l': 40, 'r': 20, 't': 20, 'b': 40},  # Margens reduzidas
        height=height,  # Altura personalizada
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x",
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor='#ECEFF1',
            ticksuffix='%'
        )
    )

    return fig


def create_availability_graph(df, height=180):
    """
    Criar gráfico de disponibilidade com tamanho ajustável

    Args:
        df (pandas.DataFrame): DataFrame com dados de disponibilidade
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de disponibilidade
    """
    if height is None:
        height = layout_config['chart_sm_height']

    fig = go.Figure()

    # Adicionar barras para dados mensais
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['availability'],
        name='Disponibilidade Mensal',
        marker_color='#388E3C',
        hovertemplate='%{y:.1f}%<extra></extra>'
    ))

    # Adicionar linha para meta
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=[80] * len(df),  # Valor da meta
        mode='lines',
        name='Meta',
        line=dict(color='#F57C00', width=2, dash='dash'),
        hovertemplate='Meta: 80%<extra></extra>'
    ))

    # Configurar layout
    fig.update_layout(
        margin={'l': 40, 'r': 20, 't': 20, 'b': 40},  # Margens reduzidas
        height=height,  # Altura personalizada
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x",
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor='#ECEFF1',
            ticksuffix='%'
        )
    )

    return fig


def create_programs_graph(df, height=180):
    """
    Cria um gráfico de barras horizontais para visualização de horas por programa

    Args:
        df (pandas.DataFrame): DataFrame com dados de programas
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de programas
    """
    if height is None:
        height = layout_config['chart_sm_height']

    # Verificar as colunas necessárias
    required_cols = ['program', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        # Se faltarem colunas, criar dados de exemplo
        programs = ["Programa A", "Programa B", "Programa C", "Programa D"]
        hours = [40, 25, 15, 9]

        fig = go.Figure()

        # Adicionar barras horizontais
        fig.add_trace(go.Bar(
            y=programs,
            x=hours,
            orientation='h',
            marker_color='#1976D2',
            hovertemplate='<b>%{y}</b>: %{x} hr<extra></extra>'
        ))
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Selecionar top programas para melhor visualização
        top_programs = df_sorted.head(6)

        fig = go.Figure()

        # Adicionar barras horizontais
        fig.add_trace(go.Bar(
            y=top_programs['program'].tolist(),
            x=top_programs['hours'].tolist(),
            orientation='h',
            marker_color='#1976D2',
            hovertemplate='<b>%{y}</b>: %{x} hr<extra></extra>'
        ))

    # Configurar layout
    fig.update_layout(
        margin={'l': 100, 'r': 20, 't': 10, 'b': 40},
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='#ECEFF1',
            title=None
        ),
        yaxis=dict(
            showgrid=False,
            title=None
        )
    )

    return fig


def create_other_skills_graph(df, height=180):
    """
    Cria um gráfico de barras horizontais para visualização de horas por outras equipes

    Args:
        df (pandas.DataFrame): DataFrame com dados de outras equipes
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de outras equipes
    """
    if height is None:
        height = layout_config['chart_sm_height']

    # Verificar as colunas necessárias
    required_cols = ['team', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        # Se faltarem colunas, criar dados de exemplo
        teams = ["Equipe A", "Equipe B", "Equipe C", "Equipe D"]
        hours = [50, 40, 25, 15]

        fig = go.Figure()

        # Adicionar barras horizontais
        fig.add_trace(go.Bar(
            y=teams,
            x=hours,
            orientation='h',
            marker_color='#673AB7',  # Roxo para outras equipes
            hovertemplate='<b>%{y}</b>: %{x} hr<extra></extra>'
        ))
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Selecionar top equipes para melhor visualização
        top_teams = df_sorted.head(6)

        fig = go.Figure()

        # Adicionar barras horizontais
        fig.add_trace(go.Bar(
            y=top_teams['team'].tolist(),
            x=top_teams['hours'].tolist(),
            orientation='h',
            marker_color='#673AB7',  # Roxo para outras equipes
            hovertemplate='<b>%{y}</b>: %{x} hr<extra></extra>'
        ))

    # Configurar layout
    fig.update_layout(
        margin={'l': 100, 'r': 20, 't': 10, 'b': 30},
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='#ECEFF1',
            title=None
        ),
        yaxis=dict(
            showgrid=False,
            title=None
        )
    )

    return fig


def create_internal_users_graph(df, height=180):
    """
    Cria um gráfico de pizza para visualização de utilização por usuários internos

    Args:
        df (pandas.DataFrame): DataFrame com dados de usuários internos
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de usuários internos
    """
    if height is None:
        height = layout_config['chart_md_height']

    # Verificar as colunas necessárias
    required_cols = ['user', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        # Se faltarem colunas, criar dados de exemplo
        labels = ["Usuário A", "Usuário B", "Usuário C", "Usuário D", "Outros"]
        values = [350, 220, 100, 80, 28]

        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker=dict(
                colors=['#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9']
            ),
            textinfo='label+percent',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>%{value} hr<br>%{percent}<extra></extra>'
        )])
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Selecionar top usuários e agrupar o resto como "Outros"
        top_users = df_sorted.head(4)
        others_sum = df_sorted.iloc[4:]['hours'].sum() if len(df_sorted) > 4 else 0

        # Preparar dados para o gráfico
        labels = top_users['user'].tolist()
        values = top_users['hours'].tolist()

        # Adicionar "Outros" se houver
        if others_sum > 0:
            labels.append("Outros")
            values.append(others_sum)

        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker=dict(
                colors=['#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9']
            ),
            textinfo='label+percent',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>%{value} hr<br>%{percent}<extra></extra>'
        )])

    # Configurar layout
    fig.update_layout(
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    return fig


def create_external_sales_graph(df, height=180):
    """
    Cria um gráfico de pizza para visualização de vendas externas

    Args:
        df (pandas.DataFrame): DataFrame com dados de vendas externas
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de vendas externas
    """
    if height is None:
        height = layout_config['chart_md_height']

    # Verificar as colunas necessárias
    required_cols = ['client', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        # Se faltarem colunas, criar dados de exemplo
        labels = ["Cliente A", "Cliente B", "Cliente C", "Outros"]
        values = [15, 10, 6, 3]

        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker=dict(
                colors=['#FF9800', '#FFB74D', '#FFCC80', '#FFE0B2']
            ),
            textinfo='label+percent',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>%{value} hr<br>%{percent}<extra></extra>'
        )])
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Selecionar top clientes e agrupar o resto como "Outros"
        top_clients = df_sorted.head(3)
        others_sum = df_sorted.iloc[3:]['hours'].sum() if len(df_sorted) > 3 else 0

        # Preparar dados para o gráfico
        labels = top_clients['client'].tolist()
        values = top_clients['hours'].tolist()

        # Adicionar "Outros" se houver
        if others_sum > 0:
            labels.append("Outros")
            values.append(others_sum)

        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker=dict(
                colors=['#FF9800', '#FFB74D', '#FFCC80', '#FFE0B2']
            ),
            textinfo='label+percent',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>%{value} hr<br>%{percent}<extra></extra>'
        )])

    # Configurar layout
    fig.update_layout(
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    return fig


def create_tracks_graph(df, height=200, bottom_margin=30, max_items=None):
    """
    Cria um gráfico de árvore (treemap) para visualização de utilização por tracks
    """
    if height is None:
        height = layout_config['chart_md_height']

    # Verificar as colunas necessárias
    required_cols = ['track', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    # Limitar para os top N itens, se solicitado
    if max_items is not None:
        df_sorted = df.sort_values('hours', ascending=False).head(max_items)
    else:
        # Ordenar dados
        df_sorted = df.sort_values('hours', ascending=False)

    if missing_cols:
        # Se faltarem colunas, criar dados de exemplo
        fig = go.Figure(go.Treemap(
            labels=["Track A", "Track B", "Track C", "Track D"],
            values=[350, 280, 190, 120],
            parents=["", "", "", ""],
            marker=dict(
                colors=['#1976D2', '#42A5F5', '#64B5F6', '#90CAF9'],
                line=dict(width=1, color='white')
            ),
            textinfo="label+value+percent root",  # Corrigido aqui
            hovertemplate="<b>%{label}</b><br>%{value} hr<br>%{percentRoot} do total<extra></extra>",
            texttemplate="%{label}<br>%{value} hr",
        ))
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Criar o treemap
        fig = go.Figure(go.Treemap(
            labels=df_sorted['track'].tolist(),
            values=df_sorted['hours'].tolist(),
            parents=[""] * len(df_sorted),
            marker=dict(
                colors=['#1976D2', '#42A5F5', '#64B5F6', '#90CAF9'],
                line=dict(width=1, color='white')
            ),
            textinfo="label+value+percent root",  # Corrigido aqui
            hovertemplate="<b>%{label}</b><br>%{value} hr<br>%{percentRoot} do total<extra></extra>",
            texttemplate="%{label}<br>%{value} hr",
        ))

    # Configurar layout
    fig.update_layout(
        margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def create_areas_graph(df, height=180):
    """
    Cria um gráfico de barras horizontais para visualização de utilização por áreas

    Args:
        df (pandas.DataFrame): DataFrame com dados de áreas
        height (int, optional): Altura do gráfico. Padrão é 180.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de áreas
    """
    if height is None:
        height = layout_config['chart_md_height']

    # Verificar as colunas necessárias
    required_cols = ['area', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        # Se faltarem colunas, criar dados de exemplo
        areas = ["Área 1", "Área 2", "Área 3", "Área 4"]
        hours = [420, 320, 190, 101]

        # Calcular porcentagens
        total = sum(hours)
        percentages = [f"{round((h/total)*100, 1)}%" for h in hours]

        fig = go.Figure()

        # Adicionar barras horizontais
        fig.add_trace(go.Bar(
            x=hours,
            y=areas,
            orientation='h',
            marker=dict(
                color=['#4CAF50', '#66BB6A', '#81C784', '#A5D6A7'],
            ),
            text=percentages,
            textposition='auto',
            hovertemplate='<b>%{y}</b>: %{x} hr<extra></extra>'
        ))
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Calcular porcentagens
        total = df_sorted['hours'].sum()
        df_sorted['percentage'] = df_sorted['hours'].apply(lambda x: f"{round((x/total)*100, 1)}%")

        # Selecionar top áreas
        top_areas = df_sorted.head(8)  # Limitar a 8 para melhor visualização

        # Cores baseadas na posição
        colors_list = ['#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9']

        # Estender a lista de cores se necessário
        while len(colors_list) < len(top_areas):
            colors_list.append('#C8E6C9')

        fig = go.Figure()

        # Adicionar barras horizontais
        fig.add_trace(go.Bar(
            x=top_areas['hours'].tolist(),
            y=top_areas['area'].tolist(),
            orientation='h',
            marker=dict(
                color=colors_list[:len(top_areas)],
            ),
            text=top_areas['percentage'].tolist(),
            textposition='auto',
            hovertemplate='<b>%{y}</b>: %{x} hr<extra></extra>'
        ))

    # Configurar layout
    fig.update_layout(
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='#ECEFF1',
            title=None
        ),
        yaxis=dict(
            showgrid=False,
            title=None
        )
    )

    return fig


def create_customers_graph(df, height=200):
    """
    Cria um gráfico de sunburst para visualização de utilização por clientes

    Args:
        df (pandas.DataFrame): DataFrame com dados de clientes
        height (int, optional): Altura do gráfico. Padrão é 200.

    Returns:
        plotly.graph_objects.Figure: Figura do gráfico de clientes
    """
    # Verificar as colunas necessárias
    required_cols = ['customer', 'hours']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        # Dados de exemplo
        labels = ["Total", "Cliente A", "Cliente B", "Cliente C", "Cliente D", "Outros"]
        parents = ["", "Total", "Total", "Total", "Total", "Total"]
        values = [1000, 400, 300, 150, 100, 50]

        # Montar figura
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(
                colors=['#FFF3E0', '#FFCC80', '#FFA726', '#FB8C00', '#F57C00', '#EF6C00'],
                line=dict(width=1, color='white')
            ),
            textinfo="label+percent parent",
            hovertemplate='<b>%{label}</b><br>%{value} hr<br>%{percentParent} do total<extra></extra>'
        ))
    else:
        # Ordenar por horas em ordem decrescente
        df_sorted = df.sort_values('hours', ascending=False)

        # Selecionar top clientes e agrupar o resto como "Outros"
        top_customers = df_sorted.head(5)

        # Verificar se há mais de 5 clientes
        others_sum = 0
        if len(df_sorted) > 5:
            others_sum = df_sorted.iloc[5:]['hours'].sum()

        # Preparar dados para o sunburst
        labels = ["Total"] + top_customers['customer'].tolist()
        values = [df_sorted['hours'].sum()] + top_customers['hours'].tolist()
        parents = [""] + ["Total"] * len(top_customers)

        # Adicionar "Outros" se houver
        if others_sum > 0:
            labels.append("Outros")
            values.append(others_sum)
            parents.append("Total")

        # Montar figura
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(
                colors=['#FFF3E0', '#FFCC80', '#FFA726', '#FB8C00', '#F57C00', '#EF6C00'],
                line=dict(width=1, color='white')
            ),
            textinfo="label+percent parent",
            hovertemplate='<b>%{label}</b><br>%{value} hr<br>%{percentParent} do total<extra></extra>'
        ))

    # Configurar layout
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig

# Nova função para criar um gráfico diferente para clientes


def create_customers_stacked_graph(df, height=None):
    """Cria um gráfico de barras empilhadas para visualização de clientes"""
    if height is None:
        height = layout_config['chart_md_height']

    # Ordenar dados
    df_sorted = df.sort_values('hours', ascending=False)

    # Preparar dados para barras empilhadas - simulando subclassificações
    # Em um caso real, você usaria subclassificações reais dos dados

    # Criar figura
    fig = go.Figure()

    # Paleta de cores
    colors_list = ['#FF6D00', '#FF9100', '#FFAB00', '#FFD600', '#AEEA00', '#64DD17', '#00C853', '#00BFA5']

    # Adicionar primeira categoria como barra principal
    fig.add_trace(go.Bar(
        y=df_sorted['customer_type'],
        x=df_sorted['hours'],
        text=df_sorted['hours'],
        textposition='auto',
        orientation='h',
        marker=dict(color=colors_list[:len(df_sorted)]),
        name='Total',
        hovertemplate='<b>%{y}</b><br>Horas: %{x}<br>Percentual: %{text}<extra></extra>',
    ))

    # Adicionar um indicador visual na forma de marcadores
    fig.add_trace(go.Scatter(
        y=df_sorted['customer_type'],
        x=[max(df_sorted['hours']) * 1.05] * len(df_sorted),
        mode='markers+text',
        text=df_sorted['percentage'],
        textposition='middle right',
        marker=dict(
            symbol='circle',
            size=16,
            color=colors_list[:len(df_sorted)],
            line=dict(color='white', width=2)
        ),
        hoverinfo='none',
        showlegend=False
    ))

    # Atualizar layout para ser mais moderno
    fig.update_layout(
        height=height,
        margin={'l': 10, 'r': 70, 't': 10, 'b': 10},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        bargap=0.3,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        annotations=[
            dict(
                x=max(df_sorted['hours']) * 1.15,
                y=df_sorted['customer_type'].iloc[i],
                text=f"{int(df_sorted['hours'].iloc[i])} hr",
                showarrow=False,
                font=dict(size=11, color="#333"),
                xanchor="left",
                yanchor="middle",
            ) for i in range(len(df_sorted))
        ]
    )

    # Adicionar gráfico de pizza pequeno para resumo visual
    fig.add_trace(go.Pie(
        labels=df_sorted['customer_type'],
        values=df_sorted['hours'],
        domain=dict(x=[0.85, 1], y=[0.1, 0.5]),
        textinfo='none',
        hole=0.7,
        marker=dict(colors=colors_list[:len(df_sorted)]),
        showlegend=False,
        hoverinfo='none'
    ))

    # Adicionar título para o gráfico de pizza
    fig.add_annotation(
        x=0.925,
        y=0.3,
        xref="paper",
        yref="paper",
        text="Visão<br>Geral",
        showarrow=False,
        font=dict(size=10, color="#333"),
    )

    return fig
