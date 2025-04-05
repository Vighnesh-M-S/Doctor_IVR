from databases import Database
from sqlalchemy import create_engine, MetaData

database = Database(DATABASE_URL)
metadata = MetaData()

from sqlalchemy import Table, Column, Integer, String, Text

appointments = Table(
    "appointments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("patient_name", String(100)),
    Column("doctor_name", String(100)),
    Column("timestamp", String(100)),
    Column("query_text", Text),
    Column("gemini_reply", Text),
)