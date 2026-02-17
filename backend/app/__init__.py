"""
FastAPI application package for the Global Events Risk Intelligence Dashboard.

The app is organized as:
- main.py: FastAPI entrypoint
- db.py: database engine and session helpers
- models.py: SQLAlchemy ORM models
- schemas.py: Pydantic models
- config.py: runtime configuration
- logging_config.py: logging setup
- routes/: API routers
- pipeline/: ingestion, normalization, aggregation logic
"""

