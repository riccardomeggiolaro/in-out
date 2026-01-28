from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, func, Date, Time
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, object_session
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum as PyEnum
from datetime import datetime
import libs.lb_config as lb_config
from libs.lb_utils import hash_password, base_path

# Database connection
Base = declarative_base()
path_database = lb_config.g_config['app_api']['path_database']
if not path_database.startswith('/'):
    base_dir = f"{base_path}/{path_database}"
path_database = f"sqlite:///{path_database}"
import libs.lb_log as lb_log
lb_log.warning(path_database)
engine = create_engine(path_database)
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
    weighings = relationship("Weighing", back_populates="user", cascade="all, delete")

# Model for Subject table
class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String(collation="NOCASE"), index=True, unique=True)
    telephone = Column(String(collation="NOCASE"), unique=True, nullable=True)
    cfpiva = Column(String(collation="NOCASE"), unique=True, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    accesses = relationship("Access", back_populates="subject", cascade="all, delete")

# Model for Vector table
class Vector(Base):
    __tablename__ = 'vector'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String(collation="NOCASE"), index=True, unique=True)
    telephone = Column(String(collation="NOCASE"), unique=True, nullable=True)
    cfpiva = Column(String(collation="NOCASE"), unique=True, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    accesses = relationship("Access", back_populates="vector", cascade="all, delete")

# Model for Driver table
class Driver(Base):
    __tablename__ = 'driver'
    id = Column(Integer, primary_key=True, index=True)
    social_reason = Column(String)
    telephone = Column(String(collation="NOCASE"), index=True, unique=True, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    accesses = relationship("Access", back_populates="driver", cascade="all, delete")

# Model for Vehicle table
class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(collation="NOCASE"), index=True, unique=True)
    description = Column(String, nullable=True)
    tare = Column(Integer, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    accesses = relationship("Access", back_populates="vehicle", cascade="all, delete")

# Model for Material table
class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, index=True) 
    description = Column(String(collation="NOCASE"), index=True, unique=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

    in_out = relationship("InOut", back_populates="material", cascade="all, delete")

class Operator(Base):
    __tablename__ = 'operator'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(collation="NOCASE"), index=True, unique=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)
    
    weighings = relationship("Weighing", back_populates="operator", cascade="all, delete")

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
    idUser = Column(Integer, ForeignKey('user.id'))
    idOperator = Column(Integer, ForeignKey('operator.id'))

    # Relationships
    weighing_pictures = relationship("WeighingPicture", back_populates="weighing", cascade="all, delete")
    in_out_weight1 = relationship("InOut", foreign_keys="InOut.idWeight1", back_populates="weight1")
    in_out_weight2 = relationship("InOut", foreign_keys="InOut.idWeight2", back_populates="weight2")
    user = relationship("User", back_populates="weighings")
    operator = relationship("Operator", back_populates="weighings")

class WeighingPicture(Base):
    __tablename__ = 'weighing_picture'
    id = Column(Integer, primary_key=True, index=True)
    path_name = Column(String, nullable=False)
    idWeighing = Column(Integer, ForeignKey('weighing.id'))

    weighing = relationship("Weighing", back_populates="weighing_pictures")

class TypeSubjectEnum(PyEnum):
    CUSTOMER = "Cliente"
    SUPPLIER = "Fornitore"

class AccessStatus(PyEnum):
    WAITING = "Attesa"
    CALLED = "Chiamato"
    ENTERED = "Entrato"
    CLOSED = "Chiusa"

class TypeAccess(PyEnum):
    RESERVATION = "Prenotazione"
    MANUALLY = "Manuale"
    TEST = "Test"

class WeighingTerminal(Base):
    __tablename__ = 'weighing-terminal'
    id = Column(Integer, primary_key=True, index=True)
    id_terminal = Column(String, nullable=True, index=True)
    bil = Column(String, nullable=True)
    badge = Column(String, nullable=True, index=True)
    plate = Column(String, nullable=True, index=True)
    customer = Column(String, nullable=True, index=True)
    supplier = Column(String, nullable=True, index=True)
    material = Column(String, nullable=True, index=True)
    notes1 = Column(String, nullable=True)
    notes2 = Column(String, nullable=True)
    datetime1 = Column(DateTime, nullable=True, index=True)
    date1 = Column(String, nullable=True)
    time1 = Column(String, nullable=True)
    datetime2 = Column(DateTime, nullable=True, index=True)
    date2 = Column(String, nullable=True)
    time2 = Column(String, nullable=True)
    prog1 = Column(String, nullable=True, index=True)
    prog2 = Column(String, nullable=True, index=True)
    weight1 = Column(Integer, nullable=True)
    pid1 = Column(String, nullable=True, index=True)
    weight2 = Column(Integer, nullable=True)
    pid2 = Column(String, nullable=True, index=True)
    net_weight = Column(Integer, nullable=True)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)

# Model for Access table
class Access(Base):
    __tablename__ = 'access'
    id = Column(Integer, primary_key=True, index=True)
    typeSubject = Column(Enum(TypeSubjectEnum), default=None, nullable=True)
    idSubject = Column(Integer, ForeignKey('subject.id'))
    idVector = Column(Integer, ForeignKey('vector.id'))
    idDriver = Column(Integer, ForeignKey('driver.id'))
    idVehicle = Column(Integer, ForeignKey('vehicle.id'))
    number_in_out = Column(Integer, nullable=True)
    note = Column(String, nullable=True)
    selected = Column(Boolean, index=True, default=False)
    date_created = Column(DateTime, server_default=func.now(), default=datetime.now)
    status = Column(Enum(AccessStatus), default=AccessStatus.WAITING)
    document_reference = Column(String, nullable=True)
    type = Column(Enum(TypeAccess), default=TypeAccess.MANUALLY)
    badge = Column(String(collation='NOCASE'), index=True, unique=True, nullable=True)
    hidden = Column(Boolean, default=False)

    # Relationships
    subject = relationship("Subject", back_populates="accesses")
    vector = relationship("Vector", back_populates="accesses")
    driver = relationship("Driver", back_populates="accesses")
    vehicle = relationship("Vehicle", back_populates="accesses")
    in_out = relationship("InOut", back_populates="access", cascade="all, delete")

    @hybrid_property  
    def is_latest_for_vehicle(self):
        if not self.idVehicle:
            return None
        
        session = object_session(self)
        if not session:
            return False
            
        max_id = session.query(func.max(Access.id)).filter(
            Access.idVehicle == self.idVehicle
        ).scalar()
        
        return self.id == max_id

    @is_latest_for_vehicle.expression
    def is_latest_for_vehicle(cls):
        return cls.id == func.max(cls.id).over(partition_by=cls.idVehicle)

class InOut(Base):
    __tablename__ = 'in_out'
    id = Column(Integer, primary_key=True, index=True)
    idAccess = Column(Integer, ForeignKey('access.id'))
    idMaterial = Column(Integer, ForeignKey('material.id'), nullable=True)
    idWeight1 = Column(Integer, ForeignKey('weighing.id'), nullable=True)  # ADDED: nullable=True
    idWeight2 = Column(Integer, ForeignKey('weighing.id'), nullable=True)  # ADDED: nullable=True
    net_weight = Column(Integer, nullable=True)

    # Relationships
    access = relationship("Access", back_populates="in_out")    
    material = relationship("Material", back_populates="in_out")
    weight1 = relationship("Weighing", foreign_keys=[idWeight1], back_populates="in_out_weight1")  # FIXED: added foreign_keys
    weight2 = relationship("Weighing", foreign_keys=[idWeight2], back_populates="in_out_weight2")  # FIXED: added foreign_keys

    @hybrid_property  
    def is_last(self):
        if not self.idAccess:
            return False
        
        session = object_session(self)
        if not session:
            return False
            
        max_id = session.query(func.max(InOut.id)).filter(
            InOut.idAccess == self.idAccess
        ).scalar()
        
        return self.id == max_id

    @is_last.expression
    def is_last(cls):
        return cls.id == func.max(cls.id).over(partition_by=cls.idAccess)

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
    'operator': Operator,
    'access': Access,
    'lock_record': LockRecord,
    'weighing_picture': WeighingPicture,
    'weighing-terminal': WeighingTerminal,
    'in_out': InOut  # ADDED: missing from original
}

upload_file_datas_required_columns = {
    "subject": {"social_reason": str, "telephone": str, "cfpiva": str},
    "vector": {"social_reason": str, "telephone": str, "cfpiva": str},
    "driver": {"social_reason": str, "telephone": str},
    "vehicle": {"plate": str, "description": str, "tare": int},
    "material": {"description": str},
    "operator": {"description": str},
    "access": {"typeSocialReason": int, "idSocialReason": int, "idVector": int, "idVehicle": int, "number_in_out": int, "note": str, "badge": str},
    "weighing-terminal": {"type": str, "id": str, "bil": str, "datetime1": str, "date1": str, "time1": str, "datetime2": str, "date2": str, "time2": str, "prog1": str, "prog2": str, "badge": str, "plate": str, "customer": str, "supplier": str, "material": str, "notes1": str, "notes2": str, "weight1": int, "pid1": str, "weight2": int, "pid2": str, "net_weight": int}
}

instances = [User, Subject, Vector, Driver, Vehicle, Material, Operator, Weighing, WeighingPicture, Access, LockRecord, InOut, WeighingTerminal]

# Create tables
Base.metadata.create_all(engine)

# Create default users
def create_default_users():
    with SessionLocal() as db_session:
        # Check if admin user exists
        admin_user = db_session.query(User).filter(User.username == "baronpesi").first()

        if admin_user is None:
            admin_user = User(
                username="baronpesi",
                password=hash_password("318101"),  # Change to a secure password in production
                level=4,
                description="baronopesi"
            )
            db_session.add(admin_user)
            db_session.commit()
            print("Admin user created")
            
        # Check if cam capture user exists
        cam_capture_plate_user = db_session.query(User).filter(User.username == "camcaptureplate").first()
        terminal = db_session.query(User).filter(User.username == "terminal").first()
        
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

        if terminal is None:
            terminal = User(
                username="terminal",
                password=None,  # FIXED: explicitly set password to None
                level=0,
                description="Terminal"
            )
            db_session.add(terminal)
            db_session.commit()
            print("Weighing terminal user created")

# Execute the function to create default users
create_default_users()
