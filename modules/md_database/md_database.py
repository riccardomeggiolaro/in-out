from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from enum import Enum as PyEnum
from datetime import datetime
import libs.lb_config as lb_config
from libs.lb_utils import hash_password

# Database connection
Base = declarative_base()
path_database = lb_config.g_config['app_api']['path_database']
engine = create_engine(f"sqlite:///{path_database}")
SessionLocal = sessionmaker(bind=engine)

# Model for User table
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(collation="NOCASE"), unique=True, index=True)
    password = Column(String)
    level = Column(Integer)
    description = Column(String)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    # Relazione con LockRecord
    lock_records = relationship("LockRecord", back_populates="user", cascade="all, delete")

# Model for Subject table
class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String(collation="NOCASE"), index=True, unique=True)
    telephone = Column(String(collation="NOCASE"), unique=True, nullable=True)
    cfpiva = Column(String(collation="NOCASE"), unique=True, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    reservations = relationship("Reservation", back_populates="subject", cascade="all, delete")

# Model for Vector table
class Vector(Base):
    __tablename__ = 'vector'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String(collation="NOCASE"), index=True, unique=True)
    telephone = Column(String(collation="NOCASE"), unique=True, nullable=True)
    cfpiva = Column(String(collation="NOCASE"), unique=True, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    reservations = relationship("Reservation", back_populates="vector", cascade="all, delete")

# Model for Driver table
class Driver(Base):
    __tablename__ = 'driver'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String)
    telephone = Column(String(collation="NOCASE"), index=True, unique=True, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    reservations = relationship("Reservation", back_populates="driver", cascade="all, delete")

# Model for Vehicle table
class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(collation="NOCASE"), index=True, unique=True)
    description = Column(String, nullable=True)
    tare = Column(Integer, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete")

# Model for Material table
class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, index=True) 
    description = Column(String(collation="NOCASE"), index=True, unique=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    in_out = relationship("InOut", back_populates="material", cascade="all, delete")

# Model for Weighing table
class Weighing(Base):
    __tablename__ = 'weighing'
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, server_default=func.now(), default=datetime.now)
    weigher = Column(String, nullable=True)
    weigher_serial_number = Column(String, nullable=True)
    pid = Column(String, index=True, unique=True, nullable=True)
    is_preset_tare = Column(Boolean, default=False, nullable=True)
    tare = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    log = Column(String, nullable=True)

    # Relationships
    weighing_pictures = relationship("WeighingPicture", back_populates="weighing", cascade="all, delete")
    in_out_weight1 = relationship("InOut", foreign_keys="InOut.idWeight1", back_populates="weight1")
    in_out_weight2 = relationship("InOut", foreign_keys="InOut.idWeight2", back_populates="weight2")

class WeighingPicture(Base):
    __tablename__ = 'weighing_picture'
    id = Column(Integer, primary_key=True, index=True)
    path_name = Column(String, nullable=False)
    idWeighing = Column(Integer, ForeignKey('weighing.id'))

    weighing = relationship("Weighing", back_populates="weighing_pictures")

class TypeSubjectEnum(PyEnum):
    CUSTOMER = "Cliente"
    SUPPLIER = "Fornitore"

class ReservationStatus(PyEnum):
    WAITING = "Attesa"
    CALLED = "Chiamato"
    ENTERED = "Entrato"
    CLOSED = "Chiusa"

class TypeReservation(PyEnum):
    RESERVATION = "Prenotazione"
    MANUALLY = "Manuale"
    TEST = "Test"

# Model for Reservation table
class Reservation(Base):
    __tablename__ = 'reservation'
    id = Column(Integer, primary_key=True, index=True)
    typeSubject = Column(Enum(TypeSubjectEnum), default=None, nullable=True)
    idSubject = Column(Integer, ForeignKey('subject.id'))
    idVector = Column(Integer, ForeignKey('vector.id'))
    idDriver = Column(Integer, ForeignKey('driver.id'))
    idVehicle = Column(Integer, ForeignKey('vehicle.id'))
    number_in_out = Column(Integer, default=0, nullable=False)
    note = Column(String, nullable=True)
    selected = Column(Boolean, index=True, default=False)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.WAITING)
    document_reference = Column(String, nullable=True)
    type = Column(Enum(TypeReservation), default=TypeReservation.MANUALLY)
    badge = Column(String(collation='NOCASE'), index=True, unique=True, nullable=True)
    hidden = Column(Boolean, default=False)

    # Relationships
    subject = relationship("Subject", back_populates="reservations")
    vector = relationship("Vector", back_populates="reservations")
    driver = relationship("Driver", back_populates="reservations")
    vehicle = relationship("Vehicle", back_populates="reservations")
    in_out = relationship("InOut", back_populates="reservation", cascade="all, delete")

class InOut(Base):
    __tablename__ = 'in_out'
    id = Column(Integer, primary_key=True, index=True)
    idReservation = Column(Integer, ForeignKey('reservation.id'))
    idMaterial = Column(Integer, ForeignKey('material.id'), nullable=True)
    idWeight1 = Column(Integer, ForeignKey('weighing.id'), nullable=True)  # ADDED: nullable=True
    idWeight2 = Column(Integer, ForeignKey('weighing.id'), nullable=True)  # ADDED: nullable=True
    net_weight = Column(Integer, nullable=True)

    # Relationships
    reservation = relationship("Reservation", back_populates="in_out")    
    material = relationship("Material", back_populates="in_out")
    weight1 = relationship("Weighing", foreign_keys=[idWeight1], back_populates="in_out_weight1")  # FIXED: added foreign_keys
    weight2 = relationship("Weighing", foreign_keys=[idWeight2], back_populates="in_out_weight2")  # FIXED: added foreign_keys

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
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    weigher_name = Column(String, nullable=True)

    user = relationship("User", back_populates="lock_records")

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
    'lock_record': LockRecord,
    'weighing_picture': WeighingPicture,
    'in_out': InOut  # ADDED: missing from original
}

upload_file_datas_required_columns = {
    "subject": {"social_reason": str, "telephone": str, "cfpiva": str},
    "vector": {"social_reason": str, "telephone": str, "cfpiva": str},
    "driver": {"social_reason": str, "telephone": str},
    "vehicle": {"plate": str, "description": str, "tare": int},
    "material": {"description": str},
    "reservation": {"typeSocialReason": int, "idSocialReason": int, "idVector": int, "idVehicle": int, "number_in_out": int, "note": str, "badge": str}
}

# Create tables
Base.metadata.create_all(engine)

# Create default users
def create_default_users():
    with SessionLocal() as db_session:
        # Check if admin user exists
        admin_user = db_session.query(User).filter(User.username == "admin").first()

        if admin_user is None:
            admin_user = User(
                username="admin",
                password=hash_password("admin"),  # Change to a secure password in production
                level=3,
                description="Administrator"
            )
            db_session.add(admin_user)
            db_session.commit()
            print("Admin user created")
            
        # Check if cam capture user exists
        cam_capture_plate_user = db_session.query(User).filter(User.username == "camcaptureplate").first()
        
        if cam_capture_plate_user is None:
            cam_capture_plate_user = User(
                username="camcaptureplate",
                password=None,  # FIXED: explicitly set password to None
                level=0,
                description="Cam Capture Plate"
            )
            db_session.add(cam_capture_plate_user)
            db_session.commit()
            print("Cam capture user created")

# Execute the function to create default users
create_default_users()