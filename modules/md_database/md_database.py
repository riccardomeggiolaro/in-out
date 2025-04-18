from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, BLOB, Float, ForeignKey, Enum, func, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, List, Union
from pydantic import BaseModel, validator
from datetime import datetime
import os
from enum import Enum as PyEnum
import libs.lb_config as lb_config

# Database connection
Base = declarative_base()
path_database = lb_config.g_config['app_api']['path_database']
engine = create_engine(f"sqlite:///{path_database}")
SessionLocal = sessionmaker(bind=engine)

# Model for User table
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
    level = Column(Integer)
    description = Column(String)
    printer_name = Column(String, nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)

# Model for Subject table
class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String)
    telephone = Column(String)
    cfpiva = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="subject", cascade="all, delete")

# Model for Vector table
class Vector(Base):
    __tablename__ = 'vector'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String)
    telephone = Column(String)
    cfpiva = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="vector", cascade="all, delete")

# Model for Driver table
class Driver(Base):
    __tablename__ = 'driver'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String)
    telephone = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="driver", cascade="all, delete")  # Fixed typo: resservations -> reservations

# Model for Vehicle table
class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String)
    description = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete")

# Model for Material table
class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, index=True) 
    description = Column(String, index=True)
    date_created = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="material", cascade="all, delete")

class WeighingPicture(Base):
    __tablename__ = 'weighing_picture'
    id = Column(Integer, primary_key=True, index=True)
    path_name = Column(String, nullable=False)
    idWeighing = Column(Integer, ForeignKey('weighing.id'))

    weighing = relationship("Weighing", back_populates="weighing_pictures")

# Model for Weighing table
class Weighing(Base):
    __tablename__ = 'weighing'
    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=True)
    pid = Column(String, nullable=True)
    weigher = Column(String, nullable=True)
    idReservation = Column(Integer, ForeignKey('reservation.id'))

    reservation = relationship("Reservation", back_populates="weighings")
    weighing_pictures = relationship("WeighingPicture", back_populates="weighing", cascade="all, delete")
    
class TypeSubjectEnum(PyEnum):
    CUSTOMER = "Cliente"
    SUPPLIER = "Fornitore"

class ReservationStatus(PyEnum):
    WAITING = "Attesa"
    CALLED = "Chiamato"
    ENTERED = "Entrato"
    CLOSED = "Chiusa"

# Model for Reservation table
class Reservation(Base):
    __tablename__ = 'reservation'
    id = Column(Integer, primary_key=True, index=True)
    typeSubject = Column(Enum(TypeSubjectEnum), default=None, nullable=True)
    idSubject = Column(Integer, ForeignKey('subject.id'))
    idVector = Column(Integer, ForeignKey('vector.id'))
    idDriver = Column(Integer, ForeignKey('driver.id'))
    idVehicle = Column(Integer, ForeignKey('vehicle.id'))
    idMaterial = Column(Integer, ForeignKey('material.id'))
    number_weighings = Column(Integer, default=0, nullable=False)
    note = Column(String)
    selected = Column(Boolean, index=True, default=False)
    date_created = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.WAITING)
    document_reference = Column(String, nullable=True)

    # Relationships
    subject = relationship("Subject", back_populates="reservations")
    vector = relationship("Vector", back_populates="reservations")
    driver = relationship("Driver", back_populates="reservations")
    vehicle = relationship("Vehicle", back_populates="reservations")
    material = relationship("Material", back_populates="reservations")	
    weighings = relationship("Weighing", back_populates="reservation", cascade="all, delete")

class LockRecordType(PyEnum):
    SELECT = "select"
    UPDATE = "update"
    DELETE = "delete"
    CALL = "call"
    CANCEL_CALL = "cancel_call"

class LockRecord(Base):
    __tablename__ = 'lock_record'
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, nullable=False)
    idRecord = Column(Integer, nullable=False)
    type = Column(Enum(LockRecordType), default=LockRecordType.SELECT)
    websocket_identifier = Column(String, nullable=True)

# Dictionary of models to map table names to model classes
table_models = {
    'user': User,
    'subject': Subject,
    'vector': Vector,
    'driver': Driver,
    'vehicle': Vehicle,
    'material': Material,
    'weighing': Weighing,
    'reservation': Reservation,
    'lock_record': LockRecord
}

upload_file_datas_required_columns = {
	"subject": {"social_reason": str, "telephone": str, "cfpiva": str},
	"vector": {"social_reason": str, "telephone": str, "cfpiva": str},
    "driver": {"social_reason": str, "telephone": str},
	"vehicle": {"plate": str, "description": str},
	"material": {"description": str},
	"reservation": {"typeSocialReason": int, "idSocialReason": int, "idVector": int, "idVehicle": int, "idMaterial": int, "number_weighings": int, "note": str}
}

Base.metadata.create_all(engine)