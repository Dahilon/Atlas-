from pathlib import Path
from pydantic import BaseModel


class AppConfig(BaseModel):
    """
    Central configuration object for the backend application.

    For v1 we use SQLite and local disk paths; this can be
    extended later to support Postgres and cloud storage.
    """

    project_root: Path = Path(__file__).resolve().parents[3]
    backend_root: Path = Path(__file__).resolve().parents[2]
    data_root: Path = backend_root / "data"
    raw_data_dir: Path = data_root / "raw"
    processed_data_dir: Path = data_root / "processed"

    # SQLite database (upgradeable to Postgres later)
    sqlite_path: Path = backend_root / "events.db"

    # GDELT events export base URL
    gdelt_events_base_url: str = "https://data.gdeltproject.org/events"

    # Default number of days to ingest for Day 1
    default_ingest_days: int = 7

    # Live ingest (Step 1): days to pull on each run; re-download latest day to get updates
    live_ingest_days: int = 2
    live_redownload_latest: bool = True


config = AppConfig()

