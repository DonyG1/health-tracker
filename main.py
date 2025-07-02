import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated

DB_NAME = "events.db"

app = FastAPI()

# Pydantic-модель для валидации входящих данных (синтаксис Pydantic v2)
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
        # Получаем ID последней вставленной строки
        event_id = cursor.lastrowid
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    return {"status": "success", "event_id": event_id}