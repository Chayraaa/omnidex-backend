from sqlalchemy import create_engine, MetaData, Table

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/omnidex"

engine = create_engine(DATABASE_URL)

metadata = MetaData()
achievements = Table("achievements", metadata, autoload_with=engine)

ACHIEVEMENTS = [
    (1, "First Step", 1, 50, ""),
    (2, "Touch Grass", 2, 100, ""),
    (3, "Darf man das streicheln", 10, 100, ""),
    (4, "Spider-Man", 10, 100, ""),
    (5, "Du bist nicht du, wenn du hungrig bist", 10, 100, ""),
    (6, "Science!", 10, 100, ""),
    (7, "Tüftler", 10, 100, ""),
    (8, "Es ist kein Brocken, es ist ein Fels", 10, 100, ""),
    (9, "Was bist du?", 10, 100, ""),
    (10, "Gerümpel", 10, 100, ""),
    (11, "Gonna catch 'em all", 90, 1000, ""),
]

columns = achievements.columns.keys()

rows = [
    dict(zip(columns, values))
    for values in ACHIEVEMENTS
]

with engine.begin() as conn:
    conn.execute(achievements.insert(), rows)

print(f"{len(rows)} Achievements eingefügt.")