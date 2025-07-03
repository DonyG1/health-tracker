import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from contextlib import asynccontextmanager
import os

# --- КОД ИЗ DATABASE.PY ПЕРЕНЕСЕН СЮДА ---
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
# --- КОНЕЦ ПЕРЕНЕСЕННОГО КОДА ---


# Lifespan менеджер для выполнения кода при старте/остановке
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется при старте
    print("Приложение запускается, проверяем/создаем базу данных...")
    create_database()
    yield
    # Код, который выполняется при остановке (здесь не нужен)
    print("Приложение останавливается.")

app = FastAPI(lifespan=lifespan)

# Pydantic-модель для валидации входящих данных
class Event(BaseModel):
    user_id: int
    timestamp: str
    event_type: Annotated[str, Field(pattern=r"^(food|symptom|mood|energy|activity)$")]
    event_value: str
    meta_data: str | None = None

@app.post("/events", status_code=201)
def create_event(event: Event):
    """
    Принимает событие и записывает его в базу данных.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (user_id, timestamp, event_type, event_value, meta_data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event.user_id, event.timestamp, event.event_type, event.event_value, event.meta_data)
        )
        conn.commit()
        event_id = cursor.lastrowid
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    return {"status": "success", "event_id": event_id}