from database import SessionLocal
from models import Athlete

db = SessionLocal()

athlete = Athlete(
    name="DB PROOF",
    position="Tester",
    height_cm=175,
    weight_kg=70,
    age=21
)

db.add(athlete)
db.commit()
db.refresh(athlete)

print("✅ INSERT WORKED")
print("ID:", athlete.id)
print("Name:", athlete.name)

db.close()
