import sqlite3
import os

DB_NAME = "events.db"

def create_database():
    """
    Создает базу данных и таблицу 'events', если они не существуют.
    """
    if os.path.exists(DB_NAME):
        print(f"База данных '{DB_NAME}' уже существует.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('food', 'symptom', 'mood', 'energy', 'activity')),
            event_value TEXT NOT NULL,
            meta_data TEXT
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        print(f"База данных '{DB_NAME}' и таблица 'events' успешно созданы.")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с SQLite: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()