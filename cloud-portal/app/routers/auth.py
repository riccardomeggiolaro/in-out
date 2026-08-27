from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import PortalUser
from app.schemas import LoginRequest, MeResponse, TokenResponse
from app.security import create_access_token, verify_password

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(PortalUser).filter(PortalUser.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali non valide")

    token = create_access_token(
        {
            "user_id": user.id,
            "username": user.username,
            "is_super_admin": user.is_super_admin,
            "site_id": user.site_id,
        }
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(user: PortalUser = Depends(get_current_user)):
    return MeResponse(
        id=user.id,
        username=user.username,
        is_super_admin=user.is_super_admin,
        site_id=user.site_id,
        site_name=user.site.name if user.site else None,
    )
