from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, BLOB, Float, ForeignKey, Enum, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from typing import Optional, List, Union
from pydantic import BaseModel, validator
from datetime import datetime
import os

# Database connection
Base = declarative_base()
cwd = os.getcwd()
engine = create_engine(f"sqlite:///{cwd}/database.db")
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

# Model for Vehicle table
class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    plate = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete")

# Model for Material table
class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, index=True) 
    name = Column(String, index=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    reservations = relationship("Reservation", back_populates="material", cascade="all, delete")

# Common attributes mixin
class CommonAttributes:
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    cell = Column(String)
    cfpiva = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

# Model for Subject table
class Subject(Base, CommonAttributes):
    __tablename__ = 'subject'
    reservations = relationship("Reservation", back_populates="subject", cascade="all, delete")

# Model for Vector table
class Vector(Base, CommonAttributes):
    __tablename__ = 'vector'
    reservations = relationship("Reservation", back_populates="vector", cascade="all, delete")

# Model for Driver table
class Driver(Base, CommonAttributes):
    __tablename__ = 'driver'
    reservations = relationship("Reservation", back_populates="driver", cascade="all, delete")  # Fixed typo: resservations -> reservations

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

# Model for Reservation table
class Reservation(Base):
    __tablename__ = 'reservation'
    id = Column(Integer, primary_key=True, index=True)
    typeSubject = Column(Integer, nullable=True)
    idSubject = Column(Integer, ForeignKey('subject.id'))
    idVector = Column(Integer, ForeignKey('vector.id'))
    idDriver = Column(Integer, ForeignKey('driver.id'))
    idVehicle = Column(Integer, ForeignKey('vehicle.id'))
    idMaterial = Column(Integer, ForeignKey('material.id'))
    number_weighings = Column(Integer, default=0, nullable=False)
    note = Column(String)
    selected = Column(Boolean, index=True, default=False)
    date_created = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subject = relationship("Subject", back_populates="reservations")
    vector = relationship("Vector", back_populates="reservations")
    driver = relationship("Driver", back_populates="reservations")
    vehicle = relationship("Vehicle", back_populates="reservations")
    material = relationship("Material", back_populates="reservations")	
    weighings = relationship("Weighing", back_populates="reservation", cascade="all, delete")

# Dictionary of models to map table names to model classes
table_models = {
    'user': User,
    'vehicle': Vehicle,
    'material': Material,
    'subject': Subject,
    'vector': Vector,
    'driver': Driver,
    'weighing': Weighing,
    'reservation': Reservation
}

required_columns = {
	"vehicle": {"name": str, "plate": str},
	"subject": {"name": str, "cell": str, "cfpiva": str},
	"vector": {"name": str, "cell": str, "cfpiva": str},
    "driver": {"name": str, "cell": str},
	"material": {"name": str},
	"weighing": {"weight": float, "date": datetime, "pid": str, "weigher": str},
	"reservation": {"typeSocialReason": int, "idSocialReason": int, "idVector": int, "idVehicle": int, "idMaterial": int, "number_weighings": int, "note": str}
}

Base.metadata.create_all(engine)