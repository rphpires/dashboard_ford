
from data.db_connection import *
from utils.tracer import *

sql = DatabaseReader()

start_date = '2024-01-01 00:00:33.220'
end_date = '2024-01-31 23:59:59.220'

results_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport", [start_date, end_date])
results_df.to_csv('dashboard_ford.csv', index=False, encoding='utf-8-sig')

print("Dashboard data saved to dashboard_ford.csv")
