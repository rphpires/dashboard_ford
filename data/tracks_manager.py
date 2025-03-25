
from .local_db_handler import LocalDatabaseHandler


def adjust_tracks_names(tracks_data: dict):
    local_db = LocalDatabaseHandler()

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
