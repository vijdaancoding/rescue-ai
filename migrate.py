from sqlalchemy import text
from app.db.database import engine

with engine.begin() as conn:
    for col in ["caller_phone", "caller_city", "caller_state", "caller_country", "caller_zip"]:
        conn.execute(text(f'ALTER TABLE call_sessions ADD COLUMN IF NOT EXISTS {col} VARCHAR'))
    print("Migration done.")
