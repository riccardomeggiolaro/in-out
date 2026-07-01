from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import PortalUser, Weighing
from app.schemas import WeighingListResponse

router = APIRouter()


@router.get("", response_model=WeighingListResponse)
def list_weighings(
    user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    site_id: Optional[int] = None,
    plate: Optional[str] = None,
    material: Optional[str] = None,
    subject_name: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
):
    query = db.query(Weighing)

    if user.is_super_admin:
        if site_id is not None:
            query = query.filter(Weighing.site_id == site_id)
    else:
        if user.site_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utente non associato ad alcun sito")
        query = query.filter(Weighing.site_id == user.site_id)

    if plate:
        query = query.filter(Weighing.plate.ilike(f"%{plate}%"))
    if material:
        query = query.filter(Weighing.material.ilike(f"%{material}%"))
    if subject_name:
        query = query.filter(Weighing.subject_name.ilike(f"%{subject_name}%"))
    if status_filter:
        query = query.filter(Weighing.status == status_filter)
    if from_date:
        query = query.filter(Weighing.date_created >= from_date)
    if to_date:
        query = query.filter(Weighing.date_created <= to_date)

    total = query.count()
    rows = (
        query.order_by(Weighing.date_created.desc(), Weighing.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return WeighingListResponse(data=rows, total=total)
