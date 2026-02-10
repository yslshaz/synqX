from database import SessionLocal
from models import Athlete

SAMPLE_ATHLETES = [
    {"name": "Shazryl Hakeemy", "position": "Forward", "height_cm": 180, "weight_kg": 80, "age": 23},
    {"name": "Saef Allah", "position": "Midfielder", "height_cm": 178, "weight_kg": 75, "age": 27},
    {"name": "Syahminaldo", "position": "Defender", "height_cm": 165, "weight_kg": 68, "age": 33},
    {"name": "Sean White", "position": "Goalkeeper", "height_cm": 185, "weight_kg": 82, "age": 29},
    {"name": "Foo Wai Xuan", "position": "Forward", "height_cm": 168, "weight_kg": 59, "age": 23},
    {"name": "Cole Palmer", "position": "Defender", "height_cm": 182, "weight_kg": 78, "age": 26},
    {"name": "Caicedo", "position": "Midfielder", "height_cm": 175, "weight_kg": 72, "age": 25},
    {"name": "Enzo", "position": "Forward", "height_cm": 177, "weight_kg": 74, "age": 24},
    {"name": "Reece James", "position": "Goalkeeper", "height_cm": 188, "weight_kg": 85, "age": 31},
    {"name": "Andy Kalule", "position": "Defender", "height_cm": 179, "weight_kg": 76, "age": 28},
    {"name": "Chitz", "position": "Midfielder", "height_cm": 172, "weight_kg": 68, "age": 22},
]


def add_athletes(players):
    db = SessionLocal()
    created = []
    try:
        for p in players:
            athlete = Athlete(**p)
            db.add(athlete)
            created.append(athlete)
        db.commit()
        for a in created:
            db.refresh(a)
            print(f"Inserted: ID={a.id} Name={a.name} Position={a.position}")
    except Exception as e:
        db.rollback()
        print("Error inserting athletes:", e)
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Adding {len(SAMPLE_ATHLETES)} sample athletes...")
    add_athletes(SAMPLE_ATHLETES)
