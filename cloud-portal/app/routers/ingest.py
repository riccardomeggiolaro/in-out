from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_site_from_api_key
from app.models import Site, Weighing
from app.schemas import IngestBatchRequest, IngestBatchResponse

router = APIRouter()


@router.get("/ping")
def ping(site: Site = Depends(get_site_from_api_key)):
    return {"site": site.name, "code": site.code}


@router.post("/weighings", response_model=IngestBatchResponse)
def ingest_weighings(
    body: IngestBatchRequest,
    site: Site = Depends(get_site_from_api_key),
    db: Session = Depends(get_db),
):
    created = 0
    updated = 0

    for item in body.weighings:
        existing = (
            db.query(Weighing)
            .filter(Weighing.site_id == site.id, Weighing.external_id == item.external_id)
            .first()
        )

        fields = item.model_dump(exclude={"external_id"})

        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            existing.raw_payload = item.model_dump_json()
            updated += 1
        else:
            db.add(
                Weighing(
                    site_id=site.id,
                    external_id=item.external_id,
                    raw_payload=item.model_dump_json(),
                    **fields,
                )
            )
            created += 1

    db.commit()

    return IngestBatchResponse(received=len(body.weighings), created=created, updated=updated)
