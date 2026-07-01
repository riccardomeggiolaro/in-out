from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import PortalUser
from app.security import hash_password


def init_db_and_admin() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        has_users = db.query(PortalUser).first() is not None
        if not has_users:
            admin = PortalUser(
                username=settings.bootstrap_admin_username,
                password_hash=hash_password(settings.bootstrap_admin_password),
                is_super_admin=True,
                site_id=None,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
