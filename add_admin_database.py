from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import os

def add_default_user():
    # Get current working directory and create database connection
    cwd = os.getcwd()
    engine = create_engine(f"sqlite:///{cwd}/database.db", echo=True)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    Base = declarative_base()

    class User(Base):
        __tablename__ = "user"
        id = Column(Integer, primary_key=True)
        username = Column(String, nullable=False)
        password = Column(String, nullable=False)
        level = Column(Integer, nullable=False)
        description = Column(String, nullable=True)
        printer_name = Column(String, nullable=True)
    
    try:
        # Create new user with the provided hashed password
        new_user = User(
            username="admin",  # Change this to desired username
            password="$2b$12$PAHE4kh6lnXo3w9SF9tj7O14rIF.3343ED20YlZCtLsaoPFYevvTO",
            level=3,  # Set appropriate level
            description="Administrator",  # Set appropriate description
            printer_name=None
        )
        
        # Add and commit the new user
        session.add(new_user)
        session.commit()
        print("User added successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding user: {str(e)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    add_default_user()