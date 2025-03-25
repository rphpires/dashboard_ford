# app_minimal.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from components.sections import (
    create_section_container, create_section_header,
    create_metric_header, create_graph_section,
    create_bordered_container, create_side_by_side_container,
    create_flex_item, create_info_card, create_compact_metric_box, create_summary_metrics
)
from components.graphs import (
    create_utilization_graph, create_availability_graph,
    create_programs_graph, create_other_skills_graph,
    create_internal_users_graph, create_external_sales_graph,
    create_tracks_graph, create_areas_graph,
    create_customers_stacked_graph  # Nova função para gráfico de clientes
)
from data.database import load_dashboard_data
from data.local_db_handler import LocalDatabaseHandler


dfs, tracks_data = load_dashboard_data()

local_db = LocalDatabaseHandler()


def adjust_tracks_name(local_db, tracks_data: dict):
    try:
        for key, item in tracks_data.items():
            track_name = local_db.select(f"select track from tracks where ponto = '{key}';")
            tracks_data[key] = {
                "track_name": track_name[0],
                "track_time": item
            }

        return tracks_data
    except Exception:
        print('errrorr')


_tracks_data = adjust_tracks_name(local_db, tracks_data)


# Inicializar a aplicação Dash com Bootstrap
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    title='Dashboard Teste',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

# Layout simples para testar o funcionamento básico
app.layout = html.Div(
    className='panel-content',
    children=[
        create_graph_section(
            'monthly-tracks-graph',
            create_tracks_graph(_tracks_data, height=None, max_items=8)
        )
    ]
)


@app.callback(
    dash.dependencies.Output("test-output", "children"),
    dash.dependencies.Input("test-button", "n_clicks"),
)
def update_output(n_clicks):
    if n_clicks:
        return f"Botão foi clicado {n_clicks} vezes."
    return "Clique no botão para testar."


if __name__ == '__main__':
    app.run_server(debug=True)
