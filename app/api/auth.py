from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.models import User
from app.api.deps import get_db
from app.core.security import verify_password, create_access_token, get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Utility route to create our ONE admin/dispatcher user manually
@router.post("/setup-dispatcher")
def setup_dispatcher(db: Session = Depends(get_db)):
    if db.query(User).first():
        return {"msg": "User already exists."}
    
    hashed_pw = get_password_hash("rescue1122") # Default password
    new_user = User(username="dispatcher", password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"msg": "Dispatcher user created. Username: dispatcher | Password: rescue1122"}