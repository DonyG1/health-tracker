import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from contextlib import asynccontextmanager

from database import create_database

DB_NAME = "events.db"

# Lifespan менеджер для выполнения кода при старте/остановке
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется при старте
    print("Приложение запускается, создаем базу данных...")
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