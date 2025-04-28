from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, table_models
import libs.lb_config as lb_config

def migrate_tables():
    path_database = lb_config.g_config['app_api']['path_database']
    engine = create_engine(f"sqlite:///{path_database}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Step 1: Salva tutti i dati esistenti
        saved_data = {}
        for table_name, model in table_models.items():
            print(f"📦 Salvando dati da tabella: {table_name}")
            saved_data[table_name] = session.query(model).all()

        session.close()

        # Step 2: Droppa tutte le tabelle
        print("🧹 Eliminando tutte le tabelle...")
        Base.metadata.drop_all(engine)

        # Step 3: Ricrea tutte le tabelle
        print("🛠️  Ricreando tutte le tabelle...")
        Base.metadata.create_all(engine)

        # Step 4: Reinserisci i dati salvati
        session = SessionLocal()
        for table_name, objects in saved_data.items():
            model = table_models[table_name]
            print(f"🔄 Ripopolando tabella: {table_name}")
            for obj in objects:
                data = {col.name: getattr(obj, col.name) for col in model.__table__.columns.keys()}
                new_obj = model(**data)
                session.add(new_obj)
        session.commit()
        print("✅ Migrazione completata con successo!")

    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate_tables()