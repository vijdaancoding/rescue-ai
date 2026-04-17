from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_user_repo
from app.repositories.users import UserRepository
from app.schemas.auth import TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    users: UserRepository = Depends(get_user_repo),
) -> TokenResponse:
    return auth_service.authenticate(
        username=form_data.username, password=form_data.password, users=users
    )


@router.post("/setup-dispatcher")
def setup_dispatcher(users: UserRepository = Depends(get_user_repo)) -> dict[str, str]:
    return auth_service.ensure_default_dispatcher(
        users=users, username="dispatcher", default_password="rescue1122"
    )
