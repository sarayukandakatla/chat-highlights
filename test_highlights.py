import os
import sqlite3
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

MODEL = "gemini-3.1-flash-lite"


# The exact shape we want Gemini to return for each highlight
class Highlight(BaseModel):
    title: str
    summary: str
    type: Literal["decision", "topic", "action_item"]
    start_message_id: int
    end_message_id: int


# 1. Read the messages from the database
conn = sqlite3.connect("chat.db")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT id, sender, content FROM messages WHERE conversation_id = 1 ORDER BY id"
).fetchall()
conn.close()

# 2. Turn them into numbered lines like: [msg_6] Alice: Let's use SQLite
transcript = "\n".join(f"[msg_{r['id']}] {r['sender']}: {r['content']}" for r in rows)

# 3. Tell Gemini what to do
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

# 4. Call Gemini and force JSON output in our shape
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=60000),
)

print("Asking Gemini... (can take a few seconds)")
response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=list[Highlight],
    ),
)
highlights = response.parsed

# 5. Validate: never trust the AI's ids blindly
valid_ids = {r["id"] for r in rows}
good = []
for h in highlights:
    if h.start_message_id not in valid_ids or h.end_message_id not in valid_ids:
        print("DROPPED (id does not exist):", h.title)
    elif h.start_message_id > h.end_message_id:
        print("DROPPED (start is after end):", h.title)
    else:
        good.append(h)

# 6. Show the result
print(f"\nGemini returned {len(highlights)} highlights, {len(good)} are valid:\n")
for h in good:
    print(f"[{h.type}] {h.title}")
    print(f"   {h.summary}")
    print(f"   messages {h.start_message_id} to {h.end_message_id}\n")