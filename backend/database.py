from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Use SQLite for development to ensure it runs out of the box, 
# but this can be easily swapped to MySQL by changing the URL below.
# MySQL Example: SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://user:password@localhost/dbname"
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root@localhost/coursework_db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
