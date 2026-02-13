"""manage_athletes.py

Consolidated management utilities for the `athletes` table:
- check status
- add `short_id` column (if missing)
- assign zero-padded short IDs using a single SQL statement
- remove duplicate athletes (by name+position)
- drop `short_id` column (rebuilds table)

Usage (from project root):
    ./.venv/Scripts/python.exe -m backend.manage_athletes --status
    ./.venv/Scripts/python.exe -m backend.manage_athletes --add-shortid
    ./.venv/Scripts/python.exe -m backend.manage_athletes --assign-shortid
    ./.venv/Scripts/python.exe -m backend.manage_athletes --remove-duplicates
    ./.venv/Scripts/python.exe -m backend.manage_athletes --drop-shortid
"""
from __future__ import annotations
import argparse
from sqlalchemy import text
from backend.database import engine, SessionLocal


def status(n=10):
    """Print table columns and first `n` rows."""
    conn = engine.connect()
    try:
        cols = [r['name'] for r in conn.execute(text("PRAGMA table_info('athletes');")).mappings().all()]
        print('Columns:', cols)
        rows = conn.execute(text(f"SELECT * FROM athletes ORDER BY created_at DESC LIMIT {n};")).mappings().all()
        for r in rows:
            print({k: r[k] for k in r.keys()})
    finally:
        conn.close()


def add_short_id_column_if_missing():
    with engine.connect() as conn:
        res = conn.execute(text("PRAGMA table_info('athletes');")).mappings().all()
        cols = [r['name'] for r in res]
        if 'short_id' not in cols:
            print('Adding column short_id to athletes...')
            conn.execute(text("ALTER TABLE athletes ADD COLUMN short_id TEXT;"))
            conn.commit()
        else:
            print('Column short_id already exists.')


def remove_duplicate_athletes():
    session = SessionLocal()
    try:
        rows = session.execute(
            text(
                """
                SELECT id, name, position, created_at
                FROM athletes
                ORDER BY lower(name), position, created_at
                """
            )
        ).mappings().all()

        seen = {}
        to_delete = []
        for r in rows:
            key = (r['name'].strip().lower() if r['name'] else '', r['position'] or '')
            if key not in seen:
                seen[key] = r['id']
            else:
                to_delete.append(r['id'])

        if not to_delete:
            print('No duplicate athletes found.')
            return

        print(f'Deleting {len(to_delete)} duplicate athlete rows...')
        for aid in to_delete:
            session.execute(text("DELETE FROM athletes WHERE id = :id"), {"id": aid})
        session.commit()
        print('Duplicates removed.')
    finally:
        session.close()


def assign_short_ids():
    session = SessionLocal()
    try:
        count = session.execute(text("SELECT COUNT(1) FROM athletes;")).scalar_one()
        if count == 0:
            print('No athletes to assign short_id.')
            return

        assign_sql = """
        WITH numbered AS (
            SELECT id, printf('%03d', ROW_NUMBER() OVER (ORDER BY created_at)) AS sid
            FROM athletes
        )
        UPDATE athletes
        SET short_id = (SELECT sid FROM numbered WHERE numbered.id = athletes.id);
        """
        session.execute(text(assign_sql))
        session.commit()
        print(f'Assigned short_id for {count} athletes.')
    finally:
        session.close()


def drop_short_id_column():
    conn = engine.connect()
    try:
        print('Rebuilding `athletes` table without short_id...')
        conn.execute(text('PRAGMA foreign_keys = OFF;'))
        conn.execute(
            text(
                '''
                CREATE TABLE IF NOT EXISTS athletes_new (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    position TEXT,
                    height_cm REAL,
                    weight_kg REAL,
                    age INTEGER,
                    created_at DATETIME
                );
                '''
            )
        )
        conn.execute(
            text(
                '''
                INSERT INTO athletes_new (id, name, position, height_cm, weight_kg, age, created_at)
                SELECT id, name, position, height_cm, weight_kg, age, created_at FROM athletes;
                '''
            )
        )
        conn.execute(text('DROP TABLE athletes;'))
        conn.execute(text('ALTER TABLE athletes_new RENAME TO athletes;'))
        conn.execute(text('PRAGMA foreign_keys = ON;'))
        conn.commit()
        print('Dropped short_id and rebuilt athletes table.')
    finally:
        conn.close()


def populate_goals():
    """Populate goals table with synthetic data for all 11 athletes."""
    session = SessionLocal()
    try:
        # Get all athlete IDs
        athlete_ids = session.execute(text("SELECT id FROM athletes ORDER BY created_at ASC")).scalars().all()
        
        if not athlete_ids:
            print('No athletes found.')
            return
        
        goal_types = ['lean', 'strength', 'weight_loss']
        
        # Create 2-3 goals per athlete
        created_count = 0
        for idx, athlete_id in enumerate(athlete_ids):
            for goal_idx in range(2 + (idx % 2)):  # 2 or 3 goals per athlete
                goal_type = goal_types[goal_idx % len(goal_types)]
                session.execute(
                    text(
                        """
                        INSERT INTO goals (athlete_id, goal_type, target_date)
                        VALUES (:athlete_id, :goal_type, datetime('now', '+' || :days || ' days'))
                        """
                    ),
                    {
                        'athlete_id': athlete_id,
                        'goal_type': goal_type,
                        'days': 30 + (goal_idx * 20)
                    }
                )
                created_count += 1
        
        session.commit()
        print(f'Created {created_count} goals for {len(athlete_ids)} athletes.')
    finally:
        session.close()


def populate_baselines():
    """Populate baselines table with synthetic data for all 11 athletes."""
    session = SessionLocal()
    try:
        # Get all athlete IDs
        athlete_ids = session.execute(text("SELECT id FROM athletes ORDER BY created_at ASC")).scalars().all()
        
        if not athlete_ids:
            print('No athletes found.')
            return
        
        metrics = ['rmssd', 'hrv', 'heart_rate', 'spo2', 'body_temperature']
        
        # Create baseline metrics for each athlete
        created_count = 0
        for idx, athlete_id in enumerate(athlete_ids):
            for metric_idx, metric in enumerate(metrics):
                # Generate synthetic baseline values based on metric type
                if metric == 'rmssd':
                    avg_value = 30.0 + (idx * 2.5)  # 30-57.5
                elif metric == 'hrv':
                    avg_value = 50.0 + (idx * 3)    # 50-83
                elif metric == 'heart_rate':
                    avg_value = 60.0 + (idx * 1)    # 60-70
                elif metric == 'spo2':
                    avg_value = 97.0 + (idx * 0.1)  # 97-98.1
                else:  # body_temperature
                    avg_value = 36.8 + (idx * 0.05) # 36.8-37.35
                
                session.execute(
                    text(
                        """
                        INSERT INTO baselines (athlete_id, metric_name, avg_7_day)
                        VALUES (:athlete_id, :metric_name, :avg_7_day)
                        """
                    ),
                    {
                        'athlete_id': athlete_id,
                        'metric_name': metric,
                        'avg_7_day': avg_value
                    }
                )
                created_count += 1
        
        session.commit()
        print(f'Created {created_count} baselines for {len(athlete_ids)} athletes ({len(metrics)} metrics each).')
    finally:
        session.close()


def add_and_assign_short_id():
    """Rebuild athletes table with short_id as first column and UUID as last."""
    conn = engine.connect()
    try:
        print('Rebuilding athletes table: short_id (001-011) first, UUID last...')
        conn.execute(text('PRAGMA foreign_keys = OFF;'))
        
        # Create new table with desired column order
        conn.execute(
            text(
                '''
                CREATE TABLE IF NOT EXISTS athletes_new (
                    short_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    position TEXT,
                    height_cm REAL,
                    weight_kg REAL,
                    age INTEGER,
                    created_at DATETIME NOT NULL,
                    id TEXT PRIMARY KEY
                );
                '''
            )
        )
        
        # Copy data with short_id assignment using ROW_NUMBER
        conn.execute(
            text(
                '''
                INSERT INTO athletes_new (short_id, name, position, height_cm, weight_kg, age, created_at, id)
                SELECT 
                    printf('%03d', ROW_NUMBER() OVER (ORDER BY created_at)) AS short_id,
                    name,
                    position,
                    height_cm,
                    weight_kg,
                    age,
                    created_at,
                    id
                FROM athletes
                ORDER BY created_at;
                '''
            )
        )
        
        # Drop old table and rename new one
        conn.execute(text('DROP TABLE athletes;'))
        conn.execute(text('ALTER TABLE athletes_new RENAME TO athletes;'))
        conn.execute(text('PRAGMA foreign_keys = ON;'))
        conn.commit()
        
        count = conn.execute(text('SELECT COUNT(*) FROM athletes')).scalar()
        print(f'Rebuilt athletes table: {count} athletes with short_id 001-{count:03d}')
    finally:
        conn.close()


def rebuild_baselines_with_short_id():
    """Rebuild baselines table to use short_id (001-011) instead of UUID athlete_id."""
    conn = engine.connect()
    try:
        print('Rebuilding baselines table: using short_id (001-011)...')
        conn.execute(text('PRAGMA foreign_keys = OFF;'))
        
        # Create new baselines table with short_id
        conn.execute(
            text(
                '''
                CREATE TABLE IF NOT EXISTS baselines_new (
                    id INTEGER PRIMARY KEY,
                    short_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    avg_7_day REAL,
                    FOREIGN KEY (short_id) REFERENCES athletes(short_id)
                );
                '''
            )
        )
        
        # Copy data from old baselines, joining with athletes to get short_id
        conn.execute(
            text(
                '''
                INSERT INTO baselines_new (id, short_id, metric_name, avg_7_day)
                SELECT 
                    b.id,
                    a.short_id,
                    b.metric_name,
                    b.avg_7_day
                FROM baselines b
                JOIN athletes a ON b.athlete_id = a.id
                ORDER BY a.short_id, b.metric_name;
                '''
            )
        )
        
        # Drop old table and rename new one
        conn.execute(text('DROP TABLE baselines;'))
        conn.execute(text('ALTER TABLE baselines_new RENAME TO baselines;'))
        conn.execute(text('PRAGMA foreign_keys = ON;'))
        conn.commit()
        
        count = conn.execute(text('SELECT COUNT(*) FROM baselines')).scalar()
        print(f'Rebuilt baselines table: {count} rows using short_id references')
    finally:
        conn.close()


def rebuild_goals_with_short_id():
    """Rebuild goals table to use short_id (001-011) and clean up (1 goal per athlete)."""
    conn = engine.connect()
    try:
        print('Rebuilding goals table: using short_id (001-011), 1 goal per athlete...')
        conn.execute(text('PRAGMA foreign_keys = OFF;'))
        
        # Create new goals table with short_id
        conn.execute(
            text(
                '''
                CREATE TABLE IF NOT EXISTS goals_new (
                    id INTEGER PRIMARY KEY,
                    short_id TEXT NOT NULL UNIQUE,
                    goal_type TEXT NOT NULL,
                    target_date DATETIME,
                    FOREIGN KEY (short_id) REFERENCES athletes(short_id)
                );
                '''
            )
        )
        
        # Copy ONE goal per athlete (first goal), mapping to short_id
        conn.execute(
            text(
                '''
                INSERT INTO goals_new (id, short_id, goal_type, target_date)
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY a.short_id),
                    a.short_id,
                    CASE CAST(SUBSTR(a.short_id, 1, 2) AS INTEGER) % 3
                        WHEN 0 THEN 'lean'
                        WHEN 1 THEN 'strength'
                        ELSE 'weight_loss'
                    END as goal_type,
                    datetime('now', '+60 days')
                FROM athletes a
                ORDER BY a.short_id;
                '''
            )
        )
        
        # Drop old table and rename new one
        conn.execute(text('DROP TABLE goals;'))
        conn.execute(text('ALTER TABLE goals_new RENAME TO goals;'))
        conn.execute(text('PRAGMA foreign_keys = ON;'))
        conn.commit()
        
        count = conn.execute(text('SELECT COUNT(*) FROM goals')).scalar()
        print(f'Rebuilt goals table: {count} rows (1 per athlete) using short_id references')
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--add-shortid', action='store_true')
    parser.add_argument('--assign-shortid', action='store_true')
    parser.add_argument('--remove-duplicates', action='store_true')
    parser.add_argument('--drop-shortid', action='store_true')
    parser.add_argument('--populate-goals', action='store_true')
    parser.add_argument('--populate-baselines', action='store_true')
    parser.add_argument('--populate-all', action='store_true')
    parser.add_argument('--add-short-display', action='store_true', help='Add short_id (001-011) as first column, UUID as last')
    parser.add_argument('--rebuild-baselines-short', action='store_true', help='Rebuild baselines to use short_id instead of UUID')
    parser.add_argument('--rebuild-goals-short', action='store_true', help='Rebuild goals to use short_id (1 per athlete)')
    args = parser.parse_args()

    if args.status:
        status()
    if args.add_shortid:
        add_short_id_column_if_missing()
    if args.remove_duplicates:
        remove_duplicate_athletes()
    if args.assign_shortid:
        add_short_id_column_if_missing()
        assign_short_ids()
    if args.drop_shortid:
        drop_short_id_column()
    if args.populate_goals:
        populate_goals()
    if args.populate_baselines:
        populate_baselines()
    if args.populate_all:
        populate_goals()
        populate_baselines()
        print('All data populated successfully.')
    if args.add_short_display:
        add_and_assign_short_id()
    if args.rebuild_baselines_short:
        rebuild_baselines_with_short_id()
    if args.rebuild_goals_short:
        rebuild_goals_with_short_id()


if __name__ == '__main__':
    main()
