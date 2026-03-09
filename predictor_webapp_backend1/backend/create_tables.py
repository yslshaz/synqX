import sys
import os
from sqlalchemy import inspect

if __package__ is None or __package__ == '':
    # Script execution: add parent to sys.path and use relative imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import engine
    import models
else:
    # Module execution: use relative imports
    from .database import engine
    import models

def init_db():
    print(" Connecting to Database...")
    
    # 1. The Magic Line (Actually creates the file)
    models.Base.metadata.create_all(bind=engine)
    
    # 2. The Verification (Proves it worked)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if len(tables) > 0:
        print(f"SUCCESS! Created the following tables: {tables}")
    else:
        print(" ERROR: No tables were created.")

if __name__ == "__main__":
    init_db()