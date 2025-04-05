# components/graphs.py
# Funções para criação de gráficos do dashboard
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from config.config import colors, dashboard_constants  # Importar configurações de cores do projeto
from config.layout_config import layout_config
import pandas as pd
import traceback


def create_utilization_graph(df, height=None):
    """Cria o gráfico de utilização mensal com design moderno e gradiente"""
    if df is None or df.empty:
        # Criar um gráfico vazio com a mensagem
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

    # Usar altura padrão se não for fornecida
    if height is None:
        height = layout_config.get('chart_sm_height', 180)

    # Definir paleta de cores para gradiente baseado nos valores
    max_value = max(df['utilization'])
    min_value = min(df['utilization'])

    # Criar gradiente de cores
    color_scale = [[0, '#64B5F6'], [0.5, '#1E88E5'], [1, '#0D47A1']]

    # Normalizar valores para coloração
    norm_values = [(val - min_value) / (max_value - min_value) if max_value != min_value else 0.5
                   for val in df['utilization']]

    # Calcular cores com base na escala
    bar_colors = [px.colors.sample_colorscale(color_scale, v)[0] for v in norm_values]

    # Adicionar brilho e profundidade
    fig = go.Figure()

    # Adicionar linha de tendência suave
    x_smooth = np.linspace(0, len(df['month']) - 1, 100)
    y_smooth = np.interp(x_smooth, np.arange(len(df['utilization'])), df['utilization'])

    fig.add_trace(go.Scatter(
        x=[df['month'][int(i)] if i.is_integer() and int(i) < len(df['month']) else df['month'][int(i)] for i in x_smooth],
        y=y_smooth,
        mode='lines',
        line=dict(color='rgba(30, 136, 229, 0.3)', width=3, shape='spline'),
        hoverinfo='skip',
        showlegend=False
    ))

    # Adicionar barras com gradiente
    for i, (month, util, color) in enumerate(zip(df['month'], df['utilization'], bar_colors)):
        fig.add_trace(go.Bar(
            x=[month],
            y=[util],
            marker_color=color,
            marker_line_width=0,
            width=0.7,
            text=[f"{util:.1f}%"],
            textposition='auto',
            hoverinfo='text',
            hovertext=f"<b>{month}</b><br>Utilization: {util:.1f}%",
            showlegend=False
        ))

    # Adicionar média como linha horizontal
    avg_util = df['utilization'].mean()
    fig.add_shape(
        type="line",
        x0=0,
        y0=avg_util,
        x1=1,
        y1=avg_util,
        xref="paper",
        line=dict(
            color="#FF5722",
            width=1.5,
            dash="dot",
        ),
    )

    # Adicionar anotação para a média
    fig.add_annotation(
        x=1,
        y=avg_util,
        xref="paper",
        text=f"Target: {avg_util:.1f}%",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=10, color="#FF5722"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#FF5722",
        borderwidth=1,
        borderpad=4,
    )

    # Atualizar o layout com a altura personalizada
    fig.update_layout(
        autosize=True,
        margin={'l': 30, 'r': 20, 't': 15, 'b': 30},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickangle=0,
            tickfont=dict(size=9),
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            zerolinecolor='#E0E0E0',
            showline=True,
            linecolor='#E0E0E0',
            range=[0, max(df['utilization']) * 1.1],
            tickfont=dict(size=9),
            title=dict(text='Utilization (%)', standoff=5),
            title_font=dict(size=10, color="#666"),
            fixedrange=True
        ),
        bargap=0.15,  # Reduzir espaçamento entre barras
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )

    fig.update_traces(hoverinfo='text')

    return fig


def create_availability_graph(df, height=None):
    """Cria o gráfico de disponibilidade com design moderno usando áreas sombreadas"""

    has_data = (df is not None
                and not df.empty
                and 'availability' in df.columns
                and df['availability'].sum() > 0)

    # Se não houver dados, mostrar mensagem
    if not has_data:
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum valor neste mês",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#666666")
        )

        # Definir altura padrão se não especificada
        if height is None:
            from config.layout_config import layout_config
            height = layout_config.get('chart_sm_height', 180)

        fig.update_layout(
            height=height,
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    target = dashboard_constants['target_availability']

    # Criar figura
    fig = go.Figure()

    # Adicionar área sombreada para a meta
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=[target] * len(df['month']),
        fill='tozeroy',
        fillcolor='rgba(241, 248, 255, 0.6)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Adicionar barras para disponibilidade, com cores condicionais
    for i, (month, avail) in enumerate(zip(df['month'], df['availability'])):
        color = colors['accent'] if avail < target else '#2E7D32'  # Vermelho se abaixo da meta, verde se acima

        fig.add_trace(go.Bar(
            x=[month],
            y=[avail],
            marker_color=color,
            marker_line_width=0,
            width=0.7,
            text=[f"{avail:.1f}%"],
            textposition='auto',
            hoverinfo='text',
            hovertext=f"<b>{month}</b><br>Availability: {avail:.1f}%<br>{'Below target' if avail < target else 'Above target'}",
            showlegend=False
        ))

    # Adicionar linha de meta
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=[target] * len(df['month']),
        mode='lines',
        line=dict(color=colors['target_line'], width=2, dash='dash'),
        name=f'Target ({target}%)',
        hoverinfo='skip'
    ))

    # Atualizar layout com a altura personalizada
    fig.update_layout(
        autosize=True,
        margin={'l': 30, 'r': 20, 't': 15, 'b': 30},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickangle=0,
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            range=[0, 110],
            tickfont=dict(size=9),
            title=dict(text='Availability (%)', standoff=5),
            title_font=dict(size=10, color="#666"),
        ),
        annotations=[
            dict(
                x=df['month'].iloc[-1],
                y=target,
                xref="x",
                yref="y",
                text=f"Target {target}%",
                showarrow=False,
                font=dict(size=9, color=colors['target_line'], family="Segoe UI, sans-serif"),
                xanchor="right",
                yanchor="bottom",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor=colors['target_line'],
                borderwidth=1,
                borderpad=3,
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=9)
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )

    return fig


def create_programs_graph(df, height=None):
    """Cria o gráfico de utilização por programas com barras horizontais e estilo moderno"""
    # Usar altura padrão se não for fornecida
    if df is None or df.empty:
        # Criar um gráfico vazio com a mensagem
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

    if height is None:
        height = layout_config.get('chart_sm_height', 180)

    # Ordenar os dados por horas (decrescente)
    df_sorted = df.sort_values('hours', ascending=False)

    # Criar figura
    fig = go.Figure()

    # Definir paleta de cores para gradiente baseado nos valores
    max_value = max(df_sorted['hours'])
    min_value = min(df_sorted['hours'])

    # Criar gradiente de cores
    color_scale = [[0, '#64B5F6'], [0.5, '#1E88E5'], [1, '#0D47A1']]

    # Normalizar valores para coloração
    norm_values = [(val - min_value) / (max_value - min_value) if max_value != min_value else 0.5
                   for val in df_sorted['hours']]

    # Calcular cores com base na escala
    bar_colors = [px.colors.sample_colorscale(color_scale, v)[0] for v in norm_values]

    # Adicionar barras horizontais
    fig.add_trace(go.Bar(
        y=df_sorted['program'],
        x=df_sorted['hours'],
        orientation='h',
        marker_color=bar_colors,
        marker_line_width=0,
        text=df_sorted['hours'],
        textposition='auto',
        textfont=dict(size=10),
        hovertemplate='<b>%{y}</b><br>Horas: %{x}<extra></extra>',
    ))

    # Atualizar layout com a altura personalizada
    fig.update_layout(
        autosize=True,
        margin={'l': 90, 'r': 20, 't': 10, 'b': 30},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            title=dict(text='Horas', standoff=5),
            title_font=dict(size=10, color="#666"),
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=9),
        ),
        bargap=0.15,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )

    return fig


def create_other_skills_graph(df, height=None):
    """Cria o gráfico de outras equipes de habilidades com barras horizontais e estilo moderno"""
    # Usar altura padrão se não for fornecida
    if df is None or df.empty:
        # Criar um gráfico vazio com a mensagem
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

    if height is None:
        height = layout_config.get('chart_sm_height', 180)

    # Ordenar os dados por horas (decrescente)
    df_sorted = df.sort_values('hours', ascending=False)

    # Criar figura com subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Definir paleta de cores
    colors_list = ['#1E88E5', '#42A5F5', '#64B5F6', '#90CAF9']

    # Calcular percentual
    total = df_sorted['hours'].sum()
    percentages = df_sorted['hours'] / total * 100

    # Adicionar barras
    fig.add_trace(
        go.Bar(
            y=df_sorted['team'],
            x=df_sorted['hours'],
            orientation='h',
            marker_color=colors_list[:len(df_sorted)],
            text=[f"{h} ({p:.1f}%)" for h, p in zip(df_sorted['hours'], percentages)],
            textposition='auto',
            textfont=dict(color='white', size=9),  # Reduzido de 10px
            name='Horas',
            hovertemplate='<b>%{y}</b><br>Horas: %{x}<br>Percentual: %{text}<extra></extra>',
        )
    )

    # Atualizar layout com a altura personalizada
    fig.update_layout(
        height=height,
        autosize=True,
        margin={'l': 90, 'r': 15, 't': 5, 'b': 20},  # Margens reduzidas
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            title=dict(text='Horas', standoff=5),
            title_font=dict(size=10, color="#666"),
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=9),
        ),
        bargap=0.15,  # Reduzido de 0.2
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
        showlegend=False,
    )

    return fig


def create_internal_users_graph(df, height=None):
    """Cria o gráfico de usuários internos com design moderno usando gráfico de pizza"""
    if df is None or df.empty:
        # Criar um gráfico vazio com a mensagem
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

    # Usar altura padrão se não for fornecida
    if height is None:
        height = layout_config.get('chart_md_height', 180)

    # Ordenar os dados por horas (decrescente)
    df_sorted = df.sort_values('hours', ascending=False)

    # Calcular percentuais
    # total = df_sorted['hours'].sum()
    # percentages = [f"{(val/total*100):.1f}%" for val in df_sorted['hours']]

    # Definir cores mais atraentes
    colors_list = ['#1E88E5', '#42A5F5', '#64B5F6', '#90CAF9', '#BBDEFB',
                   '#0D47A1', '#1565C0', '#1976D2', '#1E88E5', '#2196F3']

    # Criar figura com subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        column_widths=[0.4, 0.6],
        horizontal_spacing=0.01
    )

    # # Adicionar gráfico de pizza
    # fig.add_trace(
    #     go.Pie(
    #         labels=df_sorted['department'],
    #         values=df_sorted['hours'],
    #         hole=0.6,
    #         textposition='inside',
    #         textinfo='percent',
    #         textfont=dict(size=9),  # Tamanho reduzido
    #         hoverinfo='label+value+percent',
    #         hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{percent}<extra></extra>',
    #         marker=dict(colors=colors_list[:len(df_sorted)], line=dict(color='white', width=1)),
    #         showlegend=False,
    #         text=percentages,
    #     ),
    #     row=1, col=1
    # )

    # Adicionar barras horizontais
    fig.add_trace(
        go.Bar(
            y=df_sorted['department'],
            x=df_sorted['hours'],
            orientation='h',
            marker_color=colors_list[:len(df_sorted)],
            text=[f"{h}" for h in df_sorted['hours']],
            textposition='auto',
            textfont=dict(size=9),  # Tamanho reduzido
            hovertemplate='<b>%{y}</b><br>Horas: %{x}<extra></extra>',
            showlegend=False,
        ),
        row=1, col=2
    )

    # Atualizar layout com a altura personalizada
    fig.update_layout(
        height=height,
        autosize=True,
        margin={'l': 5, 'r': 5, 't': 5, 'b': 5},  # Margens reduzidas
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickfont=dict(size=8),  # Tamanho reduzido
            domain=[0.55, 1]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=8),  # Tamanho reduzido
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )

    return fig


# def create_external_sales_graph(df, height=None):
#     """Cria o gráfico de vendas externas com design moderno usando gráfico de rosca"""
#     # Usar altura padrão se não for fornecida
#     if height is None:
#         height = layout_config.get('chart_md_height', 180)

#     # Ordenar dados
#     df_sorted = df.sort_values('hours', ascending=False)

#     # Calcular percentuais
#     total = df_sorted['hours'].sum()
#     percentages = [f"{(val/total*100):.1f}%" for val in df_sorted['hours']]

#     # Definir cores
#     colors_list = ['#00897B', '#26A69A', '#4DB6AC', '#80CBC4', '#B2DFDB']

#     # Criar figura
#     fig = go.Figure()

#     # Adicionar gráfico de rosca
#     fig.add_trace(
#         go.Pie(
#             labels=df_sorted['company'],
#             values=df_sorted['hours'],
#             hole=0.7,
#             textposition='inside',
#             textinfo='percent',
#             textfont=dict(size=9, color="white"),  # Tamanho reduzido
#             hoverinfo='label+value+percent',
#             hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{percent}<extra></extra>',
#             marker=dict(colors=colors_list[:len(df_sorted)], line=dict(color='white', width=1)),
#             text=percentages,
#         )
#     )

#     # Adicionar anotação no centro
#     fig.add_annotation(
#         text=f"{total}<br>Total",
#         x=0.5, y=0.5,
#         font=dict(size=12, color='#333', family="Segoe UI, sans-serif"),  # Tamanho reduzido
#         showarrow=False
#     )

#     # Atualizar layout com a altura personalizada
#     fig.update_layout(
#         height=height,
#         autosize=True,
#         margin={'l': 5, 'r': 5, 't': 5, 'b': 5},  # Margens reduzidas
#         plot_bgcolor='rgba(0,0,0,0)',
#         paper_bgcolor='rgba(0,0,0,0)',
#         showlegend=True,
#         legend=dict(
#             orientation="h",
#             yanchor="bottom",
#             y=-0.1,
#             xanchor="center",
#             x=0.5,
#             font=dict(size=8)  # Tamanho reduzido
#         ),
#         hoverlabel=dict(
#             bgcolor="white",
#             font_size=10,
#             font_family="Segoe UI",
#             bordercolor="#DDD"
#         ),
#     )

#     return fig

def create_external_sales_graph(df, height=None):
    """Cria o gráfico de vendas externas com design moderno usando gráfico de rosca"""
    if df is None or df.empty:
        # Criar um gráfico vazio com a mensagem
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
    # Usar altura padrão se não for fornecida
    if height is None:
        height = layout_config.get('chart_md_height', 180)

    # Ordenar dados
    df_sorted = df.sort_values('hours', ascending=False)

    # Calcular percentuais
    total = df_sorted['hours'].sum()
    percentages = [f"{(val/total*100):.1f}%" for val in df_sorted['hours']]

    # Definir cores
    colors_list = ['#00897B', '#26A69A', '#4DB6AC', '#80CBC4', '#B2DFDB']

    # Criar figura
    fig = go.Figure()

    # Adicionar gráfico de rosca
    fig.add_trace(
        go.Pie(
            labels=df_sorted['company'],
            values=df_sorted['hours'],
            hole=0.7,
            textposition='inside',
            textinfo='percent',
            textfont=dict(size=9, color="white"),
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{percent}<extra></extra>',
            marker=dict(colors=colors_list[:len(df_sorted)], line=dict(color='white', width=1)),
            text=percentages,
        )
    )

    # Adicionar anotação no centro
    fig.add_annotation(
        text=f"{total}<br>Total",
        x=0.5, y=0.5,
        font=dict(size=12, color='#333', family="Segoe UI, sans-serif"),
        showarrow=False
    )

    # Atualizar layout com a altura personalizada e mais espaço para a legenda
    fig.update_layout(
        height=height,
        autosize=True,
        margin={'l': 5, 'r': 5, 't': 5, 'b': 30},  # Aumentei a margem inferior para dar mais espaço
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,  # Posição mais baixa para a legenda
            xanchor="center",
            x=0.5,
            font=dict(size=8)
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )

    # Reduzir o gráfico de rosca para deixar espaço para a legenda
    fig.update_traces(
        domain=dict(x=[0, 1], y=[0.1, 1])  # Reduz a área vertical do gráfico
    )

    return fig


def create_tracks_graph(tracks_dict, height=None, bottom_margin=None, max_items=None):
    print("\n-------- DIAGNÓSTICO DO GRÁFICO DE TRACKS --------")
    print(f"tracks_dict tipo: {type(tracks_dict)}")

    has_data = False

    if isinstance(tracks_dict, dict) and len(tracks_dict) > 0:
        has_data = True
    elif isinstance(tracks_dict, pd.DataFrame) and not tracks_dict.empty:
        has_data = True

    if height is None:
        from config.layout_config import layout_config
        height = layout_config.get('chart_md_height', 180)
        print(f"Usando altura padrão: {height}")

    try:
        # Verificar se tracks_dict é None ou vazio
        if not has_data:
            fig = go.Figure()

            fig.add_annotation(
                text="Nenhum valor neste mês",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14)
            )

            fig.update_layout(
                height=height,
                autosize=True,
                margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            return fig

        # Transformar o dicionário em DataFrame
        tracks_data = []
        for ponto, track_info in tracks_dict.items():
            try:
                # Verificar se track_info é um dicionário
                if not isinstance(track_info, dict):
                    print(f"Aviso: track_info para '{ponto}' não é um dicionário, é {type(track_info)}")
                    continue

                # Verificar se as chaves necessárias existem
                if 'track_time' not in track_info or 'track_name' not in track_info:
                    print(f"Aviso: track_info para '{ponto}' não tem as chaves necessárias. Chaves disponíveis: {list(track_info.keys())}")
                    continue

                # Converter tempo no formato HH:MM para horas decimais
                track_time = track_info['track_time']
                if track_time and ':' in track_time:
                    hours, minutes = map(int, track_time.split(':'))
                    total_hours = hours + (minutes / 60)
                else:
                    # Tentar converter diretamente para float
                    try:
                        total_hours = float(track_time) if track_time else 0.0
                    except (ValueError, TypeError):
                        total_hours = 0.0

                # Adicionar ao DataFrame
                tracks_data.append({
                    'ponto': ponto,
                    'track_type': track_info['track_name'],
                    'hours': total_hours,  # Valor numérico para cálculos
                    'track_time': track_info['track_time']  # Tempo original para exibição
                })
            except Exception as e:
                print(f"Erro ao processar track {ponto}: {e}")
                print(traceback.format_exc())
                continue

        # Verificar se conseguimos extrair algum dado
        if not tracks_data:
            print("Nenhum dado válido extraído de tracks_dict")
            # Se não conseguimos extrair nenhum dado, criar gráfico vazio
            fig = go.Figure()
            fig.add_annotation(
                text="Dados de tracks inválidos para exibição",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14)
            )
            fig.update_layout(
                height=height,
                autosize=True,
                margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            return fig

        # Criar DataFrame
        df = pd.DataFrame(tracks_data)
        print(f"DataFrame criado com {len(df)} linhas")
        print(f"Colunas: {list(df.columns)}")
        print("Primeiras 3 linhas:")
        print(df.head(3).to_string())

        # Limitar para os top N itens, se solicitado
        if max_items is not None and max_items > 0:
            df_sorted = df.sort_values('hours', ascending=False).head(max_items)
            print(f"Limitado para os top {max_items} itens")
        else:
            # Ordenar dados
            df_sorted = df.sort_values('hours', ascending=False)
            print("Ordenado por horas (decrescente)")

        # Calcular percentuais
        total_hours_sum = df_sorted['hours'].sum()
        if total_hours_sum > 0:
            df_sorted['percentage'] = df_sorted['hours'].apply(lambda x: f"{(x/total_hours_sum*100):.1f}%")
            print(f"Percentuais calculados (total de horas: {total_hours_sum:.1f})")
        else:
            df_sorted['percentage'] = "0.0%"
            print("Total de horas é zero, todos os percentuais serão 0.0%")

        # Criar treemap usando plotly express
        print("Criando treemap para os tracks...")
        fig = px.treemap(
            df_sorted,
            values='hours',  # Voltar a usar valores numéricos
            names='track_type',
            path=[px.Constant('Tracks'), 'track_type'],
            color='hours',
            color_continuous_scale=['#E1F5FE', '#81D4FA', '#4FC3F7', '#29B6F6', '#03A9F4', '#0288D1', '#0277BD'],
            custom_data=['track_time', 'percentage']  # Adicionar dados personalizados
        )

        # Atualizar texto e layout do treemap
        fig.update_traces(
            texttemplate='%{label}<br>%{customdata[0]} hr<br>%{customdata[1]}',  # Adicionar porcentagem
            hoverinfo='none',  # Desabilitar tooltip
            hovertemplate=None  # Remover template de hover
        )

        # Atualizar layout com a altura personalizada
        fig.update_layout(
            height=height,  # Usar a altura passada como parâmetro
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        print("Treemap criado com sucesso")
        print("----------------------------------------------------\n")
        return fig

    except Exception as e:
        print(f"ERRO ao criar gráfico de tracks: {e}")
        print(traceback.format_exc())

        # Em caso de erro, retornar um gráfico vazio com mensagem de erro
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao criar gráfico: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            height=height,
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig


def create_areas_graph(areas_df, height=None, bottom_margin=None):
    """Cria o gráfico de utilização por áreas usando barras horizontais"""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import traceback

    print("\n-------- DIAGNÓSTICO DO GRÁFICO DE ÁREAS --------")
    print(f"areas_df tipo: {type(areas_df)}")

    # Verificar se é um DataFrame válido
    is_valid_df = isinstance(areas_df, pd.DataFrame)
    print(f"É um DataFrame válido? {is_valid_df}")

    if is_valid_df:
        print(f"areas_df está vazio? {areas_df.empty}")
        print(f"Formato (linhas, colunas): {areas_df.shape}")
        print(f"Colunas disponíveis: {list(areas_df.columns)}")

        # Verificar se tem as colunas necessárias
        has_required_columns = 'area' in areas_df.columns and 'hours' in areas_df.columns
        print(f"Tem as colunas necessárias (area, hours)? {has_required_columns}")

        if not areas_df.empty:
            try:
                print("Primeiras 3 linhas:")
                print(areas_df.head(3).to_string())

                # Verificar tipos de dados
                print("\nTipos de dados das colunas:")
                print(areas_df.dtypes)

                # Estatísticas básicas da coluna hours
                if 'hours' in areas_df.columns:
                    try:
                        numeric_hours = pd.to_numeric(areas_df['hours'], errors='coerce')
                        print("\nEstatísticas da coluna 'hours':")
                        print(f"  Min: {numeric_hours.min()}")
                        print(f"  Max: {numeric_hours.max()}")
                        print(f"  Mean: {numeric_hours.mean()}")
                        print(f"  Sum: {numeric_hours.sum()}")
                        print(f"  NaN count: {numeric_hours.isna().sum()}")
                    except Exception as e:
                        print(f"Erro ao calcular estatísticas: {e}")
            except Exception as e:
                print(f"Erro ao exibir informações do DataFrame: {e}")

    if height is None:
        try:
            from config.layout_config import layout_config
            height = layout_config.get('chart_md_height', 180)
        except Exception:
            height = 180
        print(f"Usando altura: {height}")

    try:
        # Verificar se o DataFrame é válido para criar o gráfico
        is_invalid = (
            not is_valid_df
            or areas_df.empty
            or 'area' not in areas_df.columns
            or 'hours' not in areas_df.columns
        )

        if is_invalid:
            print("DataFrame inválido para criar gráfico. Criando gráfico vazio com mensagem.")
            # Criar um gráfico vazio COM MENSAGEM
            fig = go.Figure()

            # Adicionar texto explicativo
            fig.add_annotation(
                text="Nenhum valor neste mês",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14)
            )

            fig.update_layout(
                height=height,
                autosize=True,
                margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            return fig

        # Garantir que a coluna hours seja numérica
        try:
            print("Convertendo coluna 'hours' para numérico...")
            areas_df['hours'] = pd.to_numeric(areas_df['hours'], errors='coerce').fillna(0)
            print(f"Conversão concluída. Valores NaN: {areas_df['hours'].isna().sum()}")
        except Exception as e:
            print(f"Erro ao converter horas para numérico: {e}")
            print(traceback.format_exc())

        # Ordenar por horas (decrescente)
        df_sorted = areas_df.sort_values('hours', ascending=False)
        print(f"DataFrame ordenado por horas (decrescente). Linhas: {len(df_sorted)}")

        if len(df_sorted) == 0:
            print("DataFrame ordenado está vazio. Criando gráfico vazio.")
            fig = go.Figure()
            fig.add_annotation(
                text="Dados insuficientes para exibir o gráfico de áreas",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14)
            )
            fig.update_layout(
                height=height,
                autosize=True,
                margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            return fig

        # Criar gráfico com Plotly
        print("Criando gráfico de barras horizontais...")
        fig = px.bar(
            df_sorted,
            y='area',
            x='hours',
            orientation='h',
            text='hours',
            color='hours',
            color_continuous_scale=['#E1F5FE', '#81D4FA', '#4FC3F7', '#29B6F6', '#03A9F4', '#0288D1', '#0277BD'],
        )

        # Atualizar layout
        fig.update_traces(
            texttemplate='%{x} hr',
            textposition='outside',
        )

        fig.update_layout(
            height=height,
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_title=None,
            xaxis_title=None,
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            yaxis=dict(showgrid=False)
        )

        print("Gráfico de áreas criado com sucesso")
        print("----------------------------------------------------\n")
        return fig

    except Exception as e:
        print(f"ERRO ao criar gráfico de áreas: {e}")
        print(traceback.format_exc())

        # Em caso de erro, retornar um gráfico vazio com mensagem de erro
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao criar gráfico: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            height=height,
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig


def create_customers_stacked_graph(df, height=None, use_cached_data=True):
    has_data = False

    if isinstance(df, dict) and len(df) > 0:
        has_data = True
    elif isinstance(df, pd.DataFrame) and not df.empty:
        has_data = True

    if not has_data:
        print("Criando gráfico vazio pois tracks_dict é inválido ou vazio")
        fig = go.Figure()

        fig.add_annotation(
            text="Nenhum valor neste mês",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )

        fig.update_layout(
            height=height,
            autosize=True,
            margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    if height is None:
        height = layout_config.get('chart_md_height', 180)

    try:
        # Tentar carregar dados da tabela auxiliar se solicitado
        if use_cached_data:
            from data.local_db_handler import get_db_handler
            db_handler = get_db_handler()

            # Recuperar dados de utilização de clientes das últimas 12 semanas
            cached_df = db_handler.get_client_usage_data(weeks=52)

            # Se tiver dados no cache, usar eles
            if not cached_df.empty:
                # Agrupar por cliente e calcular total
                grouped_df = cached_df.groupby('classification').agg({
                    'total_hours': 'sum'
                }).reset_index()

                # Renomear colunas para compatibilidade
                grouped_df.rename(columns={
                    'classification': 'customer_type',
                    'total_hours': 'hours'
                }, inplace=True)

                # Calcular porcentagem
                total = grouped_df['hours'].sum()
                grouped_df['percentage'] = grouped_df['hours'].apply(
                    lambda x: f"{(x/total*100):.1f}%" if total > 0 else "0.0%"
                )

                # Ordenar por horas (decrescente)
                df_sorted = grouped_df.sort_values('hours', ascending=False)

                # Log para depuração
                print(f"Usando dados em cache para o gráfico de clientes ({len(df_sorted)} registros)")
            else:
                # Fallback para o DataFrame original
                df_sorted = df.sort_values('hours', ascending=False)
                print("Usando dados originais para o gráfico de clientes (cache vazio)")
        else:
            # Usar o DataFrame original
            df_sorted = df.sort_values('hours', ascending=False)
    except Exception as e:
        # Em caso de erro, fallback para o DataFrame original
        print(f"Erro ao usar dados em cache: {str(e)}")
        df_sorted = df.sort_values('hours', ascending=False)

    # Função para converter horas decimais para formato HH:MM para tooltips
    def format_hours(hours):
        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        return f"{hours_int:02d}:{minutes:02d}"

    # Criar coluna com horas formatadas para tooltips
    df_sorted['hours_formatted'] = df_sorted['hours'].apply(format_hours)

    # Criar coluna com valores inteiros para exibir no gráfico
    df_sorted['hours_int'] = df_sorted['hours'].apply(lambda x: int(x))

    # Criar figura
    fig = go.Figure()

    # Paleta de cores
    colors_list = ['#FF6D00', '#FF9100', '#FFAB00', '#FFD600', '#AEEA00', '#64DD17', '#00C853', '#00BFA5']

    # Adicionar primeira categoria como barra principal
    fig.add_trace(go.Bar(
        y=df_sorted['customer_type'],
        x=df_sorted['hours'],
        text=[f"{h} hr" for h in df_sorted['hours_int']],  # Texto exibido nas barras como valores inteiros
        textposition='auto',
        textfont=dict(size=9),  # Tamanho reduzido
        orientation='h',
        marker=dict(color=colors_list[:len(df_sorted)]),
        name='Total',
        hovertemplate='<b>%{y}</b><br>Horas: %{customdata[0]}<br>Percentual: %{customdata[1]}<extra></extra>',
        customdata=df_sorted[['hours_formatted', 'percentage']].values,  # Dados personalizados para tooltip
    ))

    # Vamos colocar os percentuais como anotações em vez de um trace de scatter
    for i, (customer_type, percentage) in enumerate(zip(df_sorted['customer_type'], df_sorted['percentage'])):
        fig.add_annotation(
            x=max(df_sorted['hours']) * 1.05,
            y=customer_type,
            text=percentage,
            showarrow=False,
            font=dict(size=11, color="#333"),  # Tamanho reduzido
            xanchor="left",
            yanchor="middle",
            bgcolor="#fff",
            bordercolor=colors_list[i % len(colors_list)],
            borderwidth=2,
            borderpad=3,  # Reduzido de 4
            xshift=20  # Reduzido de 25
        )

        # Adicionar círculos coloridos como marcadores (tamanho reduzido)
        fig.add_annotation(
            x=max(df_sorted['hours']) * 1.03,
            y=customer_type,
            text="●",
            showarrow=False,
            font=dict(size=20, color=colors_list[i % len(colors_list)]),  # Tamanho reduzido
            xanchor="left",
            yanchor="middle",
            xshift=4  # Reduzido de 5
        )

    # Atualizar layout para ser mais moderno
    fig.update_layout(
        height=height,
        autosize=True,
        margin={'l': 5, 'r': 35, 't': 5, 'b': 5},  # Margens reduzidas
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        bargap=0.25,  # Reduzido de 0.3
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            domain=[0, 1],
            tickfont=dict(size=8),  # Tamanho reduzido
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=8),  # Tamanho reduzido
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=8)  # Tamanho reduzido
        )
    )

    return fig
