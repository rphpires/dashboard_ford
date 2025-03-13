# data/__init__.py
# Torna o diretório um pacote Python e facilita importações

from data.mock_data import (
    get_utilization_df, get_availability_df, get_tracks_df, get_tracks_ytd_df,
    get_areas_df, get_areas_ytd_df, get_programs_df, get_other_skills_df,
    get_internal_users_df, get_external_sales_df, get_customers_ytd_df,
    get_all_dataframes
)

from data.database import load_dashboard_data, get_current_period_info