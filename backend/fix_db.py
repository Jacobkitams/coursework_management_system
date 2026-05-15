import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import engine, Base
from models import models

def fix_database():
    print("Connecting to database...")
    with engine.connect() as connection:
        # Disable foreign key checks to allow dropping tables in any order
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        tables_to_drop = [
            "grades", 
            "submissions", 
            "mcq_choices", 
            "mcq_questions", 
            "coursework_files", 
            "courseworks"
        ]
        
        for table in tables_to_drop:
            print(f"Dropping table: {table}")
            connection.execute(text(f"DROP TABLE IF EXISTS {table};"))
        
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        connection.commit()
    
    print("Recreating tables with correct schema...")
    Base.metadata.create_all(bind=engine)
    print("Database fix completed successfully!")

if __name__ == "__main__":
    fix_database()
