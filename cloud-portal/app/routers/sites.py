from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_super_admin
from app.models import PortalUser, Site
from app.schemas import (
    SiteCreate,
    SiteCreatedOut,
    SiteOut,
    SiteUserCreate,
    SiteUserOut,
)
from app.security import generate_api_key, hash_api_key, hash_password

router = APIRouter(dependencies=[Depends(require_super_admin)])


@router.get("", response_model=list[SiteOut])
def list_sites(db: Session = Depends(get_db)):
    return db.query(Site).order_by(Site.name.asc()).all()


@router.post("", response_model=SiteCreatedOut, status_code=status.HTTP_201_CREATED)
def create_site(body: SiteCreate, db: Session = Depends(get_db)):
    api_key = generate_api_key()
    site = Site(
        name=body.name,
        code=body.code,
        api_key_hash=hash_api_key(api_key),
        api_key_prefix=api_key[:8],
    )
    db.add(site)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Codice sito già esistente")
    db.refresh(site)

    return SiteCreatedOut(
        id=site.id,
        name=site.name,
        code=site.code,
        api_key_prefix=site.api_key_prefix,
        active=site.active,
        date_created=site.date_created,
        api_key=api_key,
    )


def _get_site_or_404(site_id: int, db: Session) -> Site:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sito non trovato")
    return site


@router.post("/{site_id}/rotate-key", response_model=SiteCreatedOut)
def rotate_key(site_id: int, db: Session = Depends(get_db)):
    site = _get_site_or_404(site_id, db)
    api_key = generate_api_key()
    site.api_key_hash = hash_api_key(api_key)
    site.api_key_prefix = api_key[:8]
    db.commit()
    db.refresh(site)

    return SiteCreatedOut(
        id=site.id,
        name=site.name,
        code=site.code,
        api_key_prefix=site.api_key_prefix,
        active=site.active,
        date_created=site.date_created,
        api_key=api_key,
    )


@router.patch("/{site_id}/active", response_model=SiteOut)
def set_active(site_id: int, active: bool, db: Session = Depends(get_db)):
    site = _get_site_or_404(site_id, db)
    site.active = active
    db.commit()
    db.refresh(site)
    return site


@router.get("/{site_id}/users", response_model=list[SiteUserOut])
def list_site_users(site_id: int, db: Session = Depends(get_db)):
    _get_site_or_404(site_id, db)
    return db.query(PortalUser).filter(PortalUser.site_id == site_id).all()


@router.post("/{site_id}/users", response_model=SiteUserOut, status_code=status.HTTP_201_CREATED)
def create_site_user(site_id: int, body: SiteUserCreate, db: Session = Depends(get_db)):
    _get_site_or_404(site_id, db)
    user = PortalUser(
        username=body.username,
        password_hash=hash_password(body.password),
        is_super_admin=False,
        site_id=site_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username già esistente")
    db.refresh(user)
    return user


@router.delete("/{site_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site_user(site_id: int, user_id: int, db: Session = Depends(get_db)):
    user = db.query(PortalUser).filter(PortalUser.id == user_id, PortalUser.site_id == site_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")
    db.delete(user)
    db.commit()
