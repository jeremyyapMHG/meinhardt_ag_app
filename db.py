# from sqlalchemy import create_engine
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, Float, UniqueConstraint, Index, text

# Change this to your actual DB path or connection string
# engine = create_engine("sqlite:///meinhardt.db", echo=False)
engine = create_engine("sqlite:///meinhardt.db", echo=False, future=True)

metadata = MetaData()

Table(
    "ag_versions",
    metadata,
    Column("version_name", Text, primary_key=True),
    Column("timestamp", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Table(
    "ag_audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", Text),
    Column("action", Text),
    Column("version_name", Text),
    Column("timestamp", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Table(
    "devco_submissions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("version_name", Text),
    Column("devco_id", Text),
    Column("data_point_id", Text),
    Column("field_name", Text),
    Column("value", Text),
    Column("submitted_at", Text),
    UniqueConstraint("devco_id", "data_point_id", "field_name", name="uq_devco_sub"),
)

Index("idx_unique_submission", "devco_id", "data_point_id", "field_name", unique=True)

Table(
    "assessment_matrix",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("assessment_criteria", Text, nullable=False),
    Column("weightage", Float),
    Column("formula", Text),
    Column("data_points_used", Text),
    Column("calculation_type", Text),
    Column("rating_good", Text),
    Column("rating_satisfactory", Text),
    Column("rating_needs_improvement", Text),
    Column("pillar", Text),
    Column("description", Text),
    Column("formula_type", Text),
)


def init_db():
    """Idempotently create all tables."""
    metadata.create_all(engine)