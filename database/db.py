from pathlib import Path
import sqlite3


class Database:

    def __init__(self):
        self.db_path = Path(__file__).parent / "nutrition.db"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):

        conn = self.connect()
        cursor = conn.cursor()

        # ---------------------------------------------------------
        # Create table if it doesn't exist
        # ---------------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            category TEXT,

            summary TEXT,

            ingredients TEXT,
            instructions TEXT,

            calories TEXT,
            protein TEXT,
            fat TEXT,
            carbohydrates TEXT,
            fiber TEXT,
            sugar TEXT,
            cholesterol TEXT,
            sodium TEXT,

            prep_time TEXT,
            cook_time TEXT,
            total_time TEXT,
            recipe_yield TEXT,

            image_url TEXT,

            author TEXT,
            published_date TEXT,
            scraped_date TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------------------------------------------------
        # Upgrade existing databases
        # ---------------------------------------------------------
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        required_columns = {
            "summary": "TEXT",
            "ingredients": "TEXT",
            "instructions": "TEXT",
            "calories": "TEXT",
            "protein": "TEXT",
            "fat": "TEXT",
            "carbohydrates": "TEXT",
            "fiber": "TEXT",
            "sugar": "TEXT",
            "cholesterol": "TEXT",
            "sodium": "TEXT",
            "prep_time": "TEXT",
            "cook_time": "TEXT",
            "total_time": "TEXT",
            "recipe_yield": "TEXT",
            "image_url": "TEXT",
            "author": "TEXT",
            "published_date": "TEXT",
            "scraped_date": "TEXT"
        }

        for column_name, column_type in required_columns.items():

            if column_name not in existing_columns:

                print(f"Adding column: {column_name}")

                cursor.execute(
                    f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}"
                )

        conn.commit()
        conn.close()


database = Database()

# Automatically initialize/upgrade database
database.initialize()