from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, func, Date, Time, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, object_session
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum as PyEnum
from datetime import datetime
import libs.lb_config as lb_config
from libs.lb_utils import hash_password, base_path
import libs.lb_log as lb_log

# Database connection
Base = declarative_base()
path_database = lb_config.g_config['app_api']['path_database']
if not path_database.startswith('/'):
    base_dir = f"{base_path}/{path_database}"
path_database = f"sqlite:///{path_database}"
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
    is_preset_weight = Column(Boolean, default=False, nullable=True)
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
    ENTERED = "Entrato"
    CLOSED = "Chiusa"

class TypeAccess(PyEnum):
    RESERVATION = "Prenotazione"
    MANUALLY = "Manuale"
    TEST = "Test"

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
    'in_out': InOut  # ADDED: missing from original
}

upload_file_datas_required_columns = {
    "subject": {"social_reason": str, "telephone": str, "cfpiva": str},
    "vector": {"social_reason": str, "telephone": str, "cfpiva": str},
    "driver": {"social_reason": str, "telephone": str},
    "vehicle": {"plate": str, "description": str, "tare": int},
    "material": {"description": str},
    "operator": {"description": str},
    "access": {"typeSocialReason": int, "idSocialReason": int, "idVector": int, "idVehicle": int, "number_in_out": int, "note": str, "badge": str}
}

instances = [User, Subject, Vector, Driver, Vehicle, Material, Operator, Weighing, WeighingPicture, Access, LockRecord, InOut]


def sync_database_columns():
    """
    Sincronizza le colonne del database con i modelli SQLAlchemy.
    - Aggiunge colonne mancanti (definite nel modello ma non nel database)
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    for table_name, model in table_models.items():
        # Gestisci il nome della tabella
        actual_table_name = model.__tablename__

        if actual_table_name not in existing_tables:
            lb_log.info(f"Tabella '{actual_table_name}' non esiste, verrà creata automaticamente")
            continue

        # Ottieni le colonne esistenti nel database
        db_columns = {col['name'] for col in inspector.get_columns(actual_table_name)}

        # Ottieni le colonne definite nel modello
        model_columns = {col.name for col in model.__table__.columns}

        # Colonne da aggiungere (nel modello ma non nel database)
        columns_to_add = model_columns - db_columns

        # Aggiungi colonne mancanti
        if columns_to_add:
            lb_log.info(f"Tabella '{actual_table_name}': aggiungendo colonne {columns_to_add}")
            with engine.connect() as conn:
                for col_name in columns_to_add:
                    column = model.__table__.columns[col_name]
                    col_type = _get_sqlite_type(column)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default = _get_column_default(column)

                    # SQLite non supporta NOT NULL senza DEFAULT per colonne aggiunte
                    if not column.nullable and default == "":
                        default = _get_type_default(column)

                    sql = f'ALTER TABLE "{actual_table_name}" ADD COLUMN "{col_name}" {col_type} {nullable} {default}'
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        lb_log.info(f"  - Aggiunta colonna '{col_name}' ({col_type})")
                    except Exception as e:
                        lb_log.error(f"  - Errore aggiungendo colonna '{col_name}': {e}")


def _get_sqlite_type(column):
    """Converte il tipo SQLAlchemy in tipo SQLite"""
    type_name = type(column.type).__name__.upper()

    if type_name in ('INTEGER', 'INT', 'SMALLINT', 'BIGINT'):
        return 'INTEGER'
    elif type_name in ('STRING', 'VARCHAR', 'TEXT', 'CHAR'):
        return 'TEXT'
    elif type_name in ('BOOLEAN', 'BOOL'):
        return 'INTEGER'  # SQLite usa INTEGER per boolean
    elif type_name in ('DATETIME', 'DATE', 'TIME', 'TIMESTAMP'):
        return 'TEXT'  # SQLite memorizza date come TEXT
    elif type_name in ('FLOAT', 'REAL', 'DOUBLE'):
        return 'REAL'
    elif type_name == 'ENUM':
        return 'TEXT'
    else:
        return 'TEXT'


def _get_column_default(column):
    """Ottiene il valore DEFAULT per una colonna"""
    if column.default is not None:
        if hasattr(column.default, 'arg'):
            default_val = column.default.arg
            if callable(default_val):
                return ""  # Non possiamo usare callable come default SQL
            elif isinstance(default_val, bool):
                return f"DEFAULT {1 if default_val else 0}"
            elif isinstance(default_val, (int, float)):
                return f"DEFAULT {default_val}"
            elif isinstance(default_val, str):
                return f"DEFAULT '{default_val}'"
    if column.server_default is not None:
        return ""  # Server default viene gestito automaticamente
    return ""


def _get_type_default(column):
    """Ottiene un valore default basato sul tipo per colonne NOT NULL"""
    type_name = type(column.type).__name__.upper()

    if type_name in ('INTEGER', 'INT', 'SMALLINT', 'BIGINT', 'BOOLEAN', 'BOOL'):
        return "DEFAULT 0"
    elif type_name in ('FLOAT', 'REAL', 'DOUBLE'):
        return "DEFAULT 0.0"
    else:
        return "DEFAULT ''"


def migrate_called_status():
    """
    Migrazione per convertire lo stato 'CALLED' (deprecato).
    Necessario per database creati con versioni precedenti del software
    dove AccessStatus includeva il valore CALLED.
    - CALLED con almeno un in_out → ENTERED
    - CALLED senza in_out → WAITING
    """
    try:
        with engine.connect() as conn:
            # Verifica se la tabella access esiste
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='access'"))
            if result.fetchone() is None:
                return  # La tabella non esiste ancora, niente da migrare

            # Aggiorna CALLED → ENTERED per accessi che hanno almeno un in_out
            result_entered = conn.execute(text("""
                UPDATE access SET status = 'ENTERED'
                WHERE status = 'CALLED'
                AND id IN (SELECT DISTINCT idAccess FROM in_out)
            """))

            # Aggiorna CALLED → WAITING per accessi senza in_out
            result_waiting = conn.execute(text("""
                UPDATE access SET status = 'WAITING'
                WHERE status = 'CALLED'
            """))

            conn.commit()

            total = result_entered.rowcount + result_waiting.rowcount
            if total > 0:
                lb_log.info(f"Migrazione stato CALLED: {result_entered.rowcount} → ENTERED, {result_waiting.rowcount} → WAITING")
    except Exception as e:
        lb_log.error(f"Errore durante la migrazione dello stato CALLED: {e}")

# Esegui migrazione per stati deprecati
migrate_called_status()

# Sincronizza le colonne del database prima di creare nuove tabelle
sync_database_columns()

# Create tables (crea tabelle mancanti)
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
