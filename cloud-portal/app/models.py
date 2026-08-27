from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Site(Base):
    """Un impianto di pesatura (installazione BARON IN-OUT) che invia dati al portale."""

    __tablename__ = "site"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    api_key_hash = Column(String, unique=True, index=True, nullable=False)
    api_key_prefix = Column(String, nullable=False)  # solo per riconoscerla in UI, non segreta
    active = Column(Boolean, default=True, nullable=False)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.utcnow)

    users = relationship("PortalUser", back_populates="site", cascade="all, delete-orphan")
    weighings = relationship("Weighing", back_populates="site", cascade="all, delete-orphan")


class PortalUser(Base):
    __tablename__ = "portal_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.utcnow)

    site = relationship("Site", back_populates="users")


class Weighing(Base):
    """Pesata ricevuta da un impianto. Struttura appiattita, pensata per essere filtrabile/ricercabile."""

    __tablename__ = "weighing"
    __table_args__ = (UniqueConstraint("site_id", "external_id", name="uq_site_external_id"),)

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False, index=True)
    external_id = Column(Integer, nullable=False)  # id dell'InOut sull'impianto locale

    status = Column(String, nullable=True, index=True)  # WAITING / ENTERED / CLOSED
    type = Column(String, nullable=True)  # RESERVATION / MANUALLY / TEST
    type_subject = Column(String, nullable=True)  # CUSTOMER / SUPPLIER

    plate = Column(String, nullable=True, index=True)
    vehicle_description = Column(String, nullable=True)
    subject_name = Column(String, nullable=True, index=True)
    vector_name = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    material = Column(String, nullable=True, index=True)

    weight1 = Column(Float, nullable=True)
    weight1_date = Column(DateTime, nullable=True)
    weight1_pid = Column(String, nullable=True)

    weight2 = Column(Float, nullable=True)
    weight2_date = Column(DateTime, nullable=True)
    weight2_pid = Column(String, nullable=True)

    net_weight = Column(Float, nullable=True)

    document_reference = Column(String, nullable=True)
    note = Column(Text, nullable=True)

    date_created = Column(DateTime, nullable=True)  # data creazione accesso sull'impianto locale
    ingested_at = Column(DateTime, server_default=func.now(), default=datetime.utcnow)
    raw_payload = Column(Text, nullable=True)  # payload originale inviato dall'impianto, per riferimento

    site = relationship("Site", back_populates="weighings")
