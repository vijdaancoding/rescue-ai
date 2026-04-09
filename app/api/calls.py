from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import CallSession, User

router = APIRouter(prefix="/calls", tags=["Calls"])

@router.get("/")
def get_active_calls(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only authenticated users (the dispatcher) can see calls
    calls = db.query(CallSession).filter(CallSession.status != "Archived").all()
    return calls

@router.post("/dummy-call")
def create_dummy_call(db: Session = Depends(get_db)):
    # This simulates a call hitting the backend from telephony
    new_call = CallSession(caller_hash="anon_caller_xyz", status="Incoming")
    db.add(new_call)
    db.commit()
    db.refresh(new_call)
    return {"msg": "Dummy call created", "call_id": new_call.id}