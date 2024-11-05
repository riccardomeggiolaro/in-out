from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os

# Connessione al database
engine = create_engine(f'sqlite:///{os.getcwd()}/database.db', echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Modello per la tabella Vehicle
class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String)
    description = Column(String)

# Modello per la tabella SocialReason
class SocialReason(Base):
    __tablename__ = 'social_reason'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    name = Column(String)
    description = Column(String)

# Modello per la tabella Material
class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, index=True)
    material = Column(String)

# Tabella che tiene traccia degli ID delle altre tabelle
class MainIndex(Base):
    __tablename__ = 'main_index'
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicle.id'))
    social_reason_id = Column(Integer, ForeignKey('social_reason.id'))
    material_id = Column(Integer, ForeignKey('material.id'))

    # Relazioni per unire i dati delle altre tabelle
    vehicle = relationship("Vehicle")
    social_reason = relationship("SocialReason")
    material = relationship("Material")

# Creazione delle tabelle
Base.metadata.create_all(engine)

# Sessione per interagire con il database
session = SessionLocal()

# Inserimento di dati di esempio
vehicle = Vehicle(plate="ABC123", description="Iveco")
social_reason = SocialReason(type="Company", name="Example Corp", description="A sample company")
material = Material(material="Steel")
session.add_all([vehicle, social_reason, material])
session.commit()

# Creazione di un record nella tabella MainIndex con riferimenti agli altri record
index_record = MainIndex(vehicle_id=vehicle.id, social_reason_id=social_reason.id, material_id=material.id)
session.add(index_record)
session.commit()

# Esempio di lettura: Recupero di tutti i dati congiunti da MainIndex
result = session.query(MainIndex).first()
print("Vehicle:", result.vehicle.plate, result.vehicle.description)
print("Social Reason:", result.social_reason.type, result.social_reason.name, result.social_reason.description)
print("Material:", result.material.material)

# Chiusura della sessione
session.close()