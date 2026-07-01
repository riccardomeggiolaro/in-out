from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PortalUser, Site
from app.security import decode_access_token, hash_api_key

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PortalUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non autenticato")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload["user_id"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido o scaduto")

    user = db.get(PortalUser, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utente non trovato")
    return user


def require_super_admin(user: PortalUser = Depends(get_current_user)) -> PortalUser:
    if not user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Richiesti permessi di amministratore")
    return user


def get_site_from_api_key(
    x_api_key: str = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Site:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key mancante")

    site = db.query(Site).filter(Site.api_key_hash == hash_api_key(x_api_key)).first()
    if site is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key non valida")
    if not site.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sito disattivato")
    return site
