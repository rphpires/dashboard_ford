# components/__init__.py
# Torna o diretório um pacote Python e facilita importações

from components.graphs import (
    create_utilization_graph, create_availability_graph, create_programs_graph,
    create_other_skills_graph, create_internal_users_graph, create_external_sales_graph,
    create_tracks_graph, create_areas_graph, create_customers_graph
)

from components.sections import (
    create_section_container, create_section_header, create_metric_header,
    create_graph_section, create_bordered_container, create_side_by_side_container,
    create_flex_item
)