from sqlalchemy import create_engine, MetaData, Table

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/omnidex"

engine = create_engine(DATABASE_URL)

metadata = MetaData()
achievements = Table("achievements", metadata, autoload_with=engine)

ACHIEVEMENTS = [
    (1, "First Step", 1, 50,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%91%A3&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (2, "Touch Grass", 2, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%8C%BF&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (3, "Darf man das streicheln", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%90%BE&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (4, "Spider-Man", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%95%B7%EF%B8%8F&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (5, "Du bist nicht du, wenn du hungrig bist", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%8D%94&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (6, "Science!", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%A7%AA&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (7, "Tüftler", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%94%A7&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (8, "Es ist kein Brocken, es ist ein Fels", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%E2%9B%B0%EF%B8%8F&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (9, "Was bist du?", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%3F&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (10, "Gerümpel", 10, 100,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%97%91%EF%B8%8F&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30"),

    (11, "Gonna catch 'em all", 90, 1000,
     "https://images.placeholders.dev/?width=50&height=50&text=%F0%9F%8E%AF&bgColor=%23f7f6f6&textColor=%236d6e71&fontSize=30")
]

columns = achievements.columns.keys()

rows = [
    dict(zip(columns, values))
    for values in ACHIEVEMENTS
]

with engine.begin() as conn:
    conn.execute(achievements.insert(), rows)

print(f"{len(rows)} Achievements eingefügt.")
