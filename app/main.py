from fastapi import FastAPI
from app.db.database import engine, Base
from app.api import auth, calls, voice

# Create all tables in Supabase (if they don't exist yet)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rescue AI Backend", version="1.0")

# Include our routers
app.include_router(auth.router)
app.include_router(calls.router)
app.include_router(voice.router)

@app.get("/")
def root():
    return {"message": "Rescue AI Backend is running."}