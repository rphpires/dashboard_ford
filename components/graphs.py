# components/graphs.py
# Funções para criação de gráficos do dashboard com visual moderno
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from config.config import colors, layout_config, dashboard_constants


def create_utilization_graph(df):
    """Cria o gráfico de utilização mensal com design moderno e gradiente"""
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
    x_smooth = np.linspace(0, len(df['month'])-1, 100)
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
            hovertext=f"<b>{month}</b><br>Utilização: {util:.1f}%",
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
        text=f"Média: {avg_util:.1f}%",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=10, color="#FF5722"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#FF5722",
        borderwidth=1,
        borderpad=4,
    )
    
    # Atualizar o layout
    fig.update_layout(
        height=layout_config['chart_sm_height'],
        margin={'l': 40, 'r': 20, 't': 20, 'b': 40},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickangle=0,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            zerolinecolor='#E0E0E0',
            showline=True,
            linecolor='#E0E0E0',
            range=[0, max(df['utilization']) * 1.2],
            tickfont=dict(size=10),
            title=dict(text='Utilização (%)', standoff=5),
            title_font=dict(size=11, color="#666"),
        ),
        bargap=0.2,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_availability_graph(df):
    """Cria o gráfico de disponibilidade com design moderno usando áreas sombreadas"""
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
            hovertext=f"<b>{month}</b><br>Disponibilidade: {avail:.1f}%<br>{'Abaixo da meta' if avail < target else 'Acima da meta'}",
            showlegend=False
        ))
    
    # Adicionar linha de meta
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=[target] * len(df['month']),
        mode='lines',
        line=dict(color=colors['target_line'], width=2, dash='dash'),
        name=f'Meta ({target}%)',
        hoverinfo='skip'
    ))
    
    # Atualizar layout
    fig.update_layout(
        height=layout_config['chart_sm_height'],
        margin={'l': 40, 'r': 20, 't': 20, 'b': 40},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickangle=0,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            range=[0, 110],
            tickfont=dict(size=10),
            title=dict(text='Disponibilidade (%)', standoff=5),
            title_font=dict(size=11, color="#666"),
        ),
        annotations=[
            dict(
                x=df['month'].iloc[-1],
                y=target,
                xref="x",
                yref="y",
                text=f"META {target}%",
                showarrow=False,
                font=dict(size=10, color=colors['target_line'], family="Segoe UI, sans-serif"),
                xanchor="right",
                yanchor="bottom",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor=colors['target_line'],
                borderwidth=1,
                borderpad=4,
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_programs_graph(df):
    """Cria o gráfico de utilização por programas com barras horizontais e estilo moderno"""
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
    
    # Atualizar layout
    fig.update_layout(
        height=layout_config['chart_sm_height'],
        margin={'l': 100, 'r': 20, 't': 10, 'b': 40},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            title=dict(text='Horas', standoff=5),
            title_font=dict(size=11, color="#666"),
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=10),
        ),
        bargap=0.2,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_other_skills_graph(df):
    """Cria o gráfico de outras equipes de habilidades com barras horizontais e estilo moderno"""
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
            textfont=dict(color='white', size=10),
            name='Horas',
            hovertemplate='<b>%{y}</b><br>Horas: %{x}<br>Percentual: %{text}<extra></extra>',
        )
    )
    
    # Atualizar layout
    fig.update_layout(
        height=layout_config['chart_sm_height'],
        margin={'l': 100, 'r': 20, 't': 10, 'b': 30},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            title=dict(text='Horas', standoff=5),
            title_font=dict(size=11, color="#666"),
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=10),
        ),
        bargap=0.2,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
        showlegend=False,
    )
    
    return fig


def create_internal_users_graph(df):
    """Cria o gráfico de usuários internos com design moderno usando gráfico de pizza"""
    # Ordenar os dados por horas (decrescente)
    df_sorted = df.sort_values('hours', ascending=False)
    
    # Calcular percentuais
    total = df_sorted['hours'].sum()
    percentages = [f"{(val/total*100):.1f}%" for val in df_sorted['hours']]
    
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
    
    # Adicionar gráfico de pizza
    fig.add_trace(
        go.Pie(
            labels=df_sorted['department'],
            values=df_sorted['hours'],
            hole=0.6,
            textposition='inside',
            textinfo='percent',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{percent}<extra></extra>',
            marker=dict(colors=colors_list[:len(df_sorted)], line=dict(color='white', width=1)),
            showlegend=False,
        ),
        row=1, col=1
    )
    
    # Adicionar barras horizontais
    fig.add_trace(
        go.Bar(
            y=df_sorted['department'],
            x=df_sorted['hours'],
            orientation='h',
            marker_color=colors_list[:len(df_sorted)],
            text=[f"{h}" for h in df_sorted['hours']],
            textposition='auto',
            textfont=dict(size=10),
            hovertemplate='<b>%{y}</b><br>Horas: %{x}<extra></extra>',
            showlegend=False,
        ),
        row=1, col=2
    )
    
    # Adicionar anotação no centro do donut
    fig.add_annotation(
        text=f"{total}<br>Total",
        x=0.2, y=0.5,
        font=dict(size=14, color='#333', family="Segoe UI, sans-serif"),
        showarrow=False,
        xref="paper",
        yref="paper"
    )
    
    # Atualizar layout
    fig.update_layout(
        height=layout_config['chart_md_height'],
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickfont=dict(size=9),
            domain=[0.55, 1]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=9),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_external_sales_graph(df):
    """Cria o gráfico de vendas externas com design moderno usando gráfico de rosca"""
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
            textfont=dict(size=10, color="white"),
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{percent}<extra></extra>',
            marker=dict(colors=colors_list[:len(df_sorted)], line=dict(color='white', width=1)),
        )
    )
    
    # Adicionar anotação no centro
    fig.add_annotation(
        text=f"{total}<br>Total",
        x=0.5, y=0.5,
        font=dict(size=14, color='#333', family="Segoe UI, sans-serif"),
        showarrow=False
    )
    
    # Atualizar layout
    fig.update_layout(
        height=layout_config['chart_md_height'],
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_tracks_graph(df, height=None, bottom_margin=None):
    """Cria o gráfico de utilização por tracks com design moderno usando treemap"""
    if height is None:
        height = layout_config['chart_md_height']
    
    # Ordenar dados
    df_sorted = df.sort_values('hours', ascending=False)
    
    # Criar treemap usando plotly express
    fig = px.treemap(
        df_sorted,
        values='hours',
        path=[px.Constant('Tracks'), 'track_type'],
        color='hours',
        color_continuous_scale=['#E1F5FE', '#81D4FA', '#4FC3F7', '#29B6F6', '#03A9F4', '#0288D1', '#0277BD'],
        hover_data={'hours': True, 'percentage': True},
        custom_data=['percentage']
    )
    
    # Atualizar texto e layout do treemap
    fig.update_traces(
        textinfo='label+value',
        hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{customdata[0]}<extra></extra>'
    )
    
    # Atualizar layout
    fig.update_layout(
        height=height,
        margin={'l': 10, 'r': 10, 't': 10, 'b': bottom_margin or 10},
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_areas_graph(df, height=None):
    """Cria o gráfico de utilização por áreas com design moderno usando gráfico de pizza"""
    if height is None:
        height = layout_config['chart_md_height']
    
    # Ordenar dados
    df_sorted = df.sort_values('hours', ascending=False)
    
    # Criar figura com subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        column_widths=[0.4, 0.6],
        horizontal_spacing=0.01
    )
    
    # Definir cores mais atraentes
    colors_list = ['#388E3C', '#43A047', '#4CAF50', '#66BB6A', '#81C784', 
                  '#A5D6A7', '#C8E6C9', '#1B5E20', '#2E7D32', '#388E3C']
    
    # Adicionar gráfico de pizza
    fig.add_trace(
        go.Pie(
            labels=df_sorted['area'],
            values=df_sorted['hours'],
            hole=0.6,
            textposition='inside',
            textinfo='percent',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{percent}<extra></extra>',
            marker=dict(colors=colors_list[:len(df_sorted)], line=dict(color='white', width=1)),
            showlegend=False,
        ),
        row=1, col=1
    )
    
    # Adicionar barras horizontais
    fig.add_trace(
        go.Bar(
            y=df_sorted['area'],
            x=df_sorted['hours'],
            orientation='h',
            marker_color=colors_list[:len(df_sorted)],
            text=[f"{h}" for h in df_sorted['hours']],
            textposition='auto',
            textfont=dict(size=10),
            hovertemplate='<b>%{y}</b><br>Horas: %{x}<br>Percentual: %{text}<extra></extra>',
            showlegend=False,
        ),
        row=1, col=2
    )
    
    # Adicionar anotação no centro do donut
    total = df_sorted['hours'].sum()
    fig.add_annotation(
        text=f"{total}<br>Total",
        x=0.2, y=0.5,
        font=dict(size=14, color='#333', family="Segoe UI, sans-serif"),
        showarrow=False,
        xref="paper",
        yref="paper"
    )
    
    # Atualizar layout
    fig.update_layout(
        height=height,
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(224, 224, 224, 0.5)',
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            tickfont=dict(size=9),
            domain=[0.55, 1]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#E0E0E0',
            automargin=True,
            tickfont=dict(size=9),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig


def create_customers_graph(df):
    """Cria o gráfico de utilização por clientes com design moderno usando sunburst"""
    # Ordenar dados
    df_sorted = df.sort_values('hours', ascending=False)
    
    # Criar sunburst usando plotly express
    fig = px.sunburst(
        df_sorted,
        values='hours',
        path=[px.Constant('Clientes'), 'customer_type'],
        color='hours',
        color_continuous_scale=['#FFECB3', '#FFE082', '#FFD54F', '#FFCA28', '#FFC107', '#FFB300', '#FFA000'],
        hover_data={'hours': True, 'percentage': True},
        custom_data=['percentage']
    )
    
    # Atualizar texto e layout do sunburst
    fig.update_traces(
        textinfo='label+value',
        hovertemplate='<b>%{label}</b><br>Horas: %{value}<br>Percentual: %{customdata[0]}<extra></extra>'
    )
    
    # Atualizar layout
    fig.update_layout(
        height=layout_config['chart_md_height'],
        margin={'l': 10, 'r': 10, 't': 10, 'b': 10},
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI",
            bordercolor="#DDD"
        ),
    )
    
    return fig