import os
import sqlite3
from datetime import datetime, timezone
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

MODEL = "gemini-3.1-flash-lite"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# The exact shape we want Gemini to return for each highlight
class Highlight(BaseModel):
    title: str
    summary: str
    type: Literal["decision", "topic", "action_item"]
    start_message_id: int
    end_message_id: int


# The shape of a new chat message sent by the frontend
class NewMessage(BaseModel):
    sender: str
    content: str


def get_db():
    conn = sqlite3.connect("chat.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def home():
    return {"message": "Hello! My Chat Highlights server is working."}


@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, sender, content, created_at FROM messages "
        "WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Save a new chat message (the frontend calls this every time someone sends a message)
@app.post("/conversations/{conversation_id}/messages")
def add_message(conversation_id: int, message: NewMessage):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO messages (conversation_id, sender, content, created_at) "
        "VALUES (?, ?, ?, ?)",
        (conversation_id, message.sender, message.content, now),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {
        "id": new_id,
        "conversation_id": conversation_id,
        "sender": message.sender,
        "content": message.content,
        "created_at": now,
    }


@app.get("/conversations/{conversation_id}/highlights")
def get_highlights(conversation_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, summary, type, start_message_id, end_message_id "
        "FROM highlights WHERE conversation_id = ? ORDER BY start_message_id",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Generate REAL highlights with Gemini
@app.post("/conversations/{conversation_id}/highlights/generate")
def generate_highlights(conversation_id: int):
    # 1. Read the messages
    conn = get_db()
    rows = conn.execute(
        "SELECT id, sender, content FROM messages "
        "WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No messages found for this conversation.")

    # 2. Build the numbered transcript
    transcript = "\n".join(f"[msg_{r['id']}] {r['sender']}: {r['content']}" for r in rows)

    prompt = f"""You are analyzing a chat transcript. Each line starts with a message id like [msg_6].

Find the key decisions, main discussion topics, and action items.
For each one return:
- title: short, max 6 words
- summary: exactly one sentence
- type: "decision", "topic", or "action_item"
- start_message_id: the number of the FIRST message about it
- end_message_id: the number of the LAST message about it

Only use message ids that appear in the transcript. Order highlights by start_message_id.

TRANSCRIPT:
{transcript}
"""

    # 3. Call Gemini
    try:
        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
            http_options=types.HttpOptions(timeout=60000),
        )
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Highlight],
            ),
        )
        ai_highlights = response.parsed
    except KeyError:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing in the .env file.")
    except Exception as e:
        print("Gemini error:", e)  # shows the real reason in the server terminal
        raise HTTPException(
            status_code=502,
            detail="The AI service failed or is busy. Please try again in a minute.",
        )

    if not ai_highlights:
        raise HTTPException(status_code=502, detail="The AI returned no highlights. Please try again.")

    # 4. Validate: never trust the AI's ids blindly
    valid_ids = {r["id"] for r in rows}
    good = []
    for h in ai_highlights:
        if h.start_message_id not in valid_ids or h.end_message_id not in valid_ids:
            print("DROPPED (id does not exist):", h.title)
        elif h.start_message_id > h.end_message_id:
            print("DROPPED (start is after end):", h.title)
        else:
            good.append(h)

    if not good:
        raise HTTPException(status_code=502, detail="The AI gave no usable highlights. Please try again.")

    # 5. Save: replace the old highlights with the new ones
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute("DELETE FROM highlights WHERE conversation_id = ?", (conversation_id,))
    for h in good:
        conn.execute(
            "INSERT INTO highlights (conversation_id, title, summary, type, "
            "start_message_id, end_message_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conversation_id, h.title, h.summary, h.type,
             h.start_message_id, h.end_message_id, now),
        )
    conn.commit()
    conn.close()

    return get_highlights(conversation_id)