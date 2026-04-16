from sqlalchemy import text
from app.db.database import engine

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT id, caller_hash, caller_phone, caller_city, caller_state,
               caller_country, caller_zip, status, start_time, end_time
        FROM call_sessions
        ORDER BY start_time DESC
        LIMIT 10
    """)).mappings().all()

for r in rows:
    print("-" * 70)
    for k, v in r.items():
        print(f"  {k}: {v}")
