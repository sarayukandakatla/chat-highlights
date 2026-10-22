import sqlite3

# This creates a file called chat.db in your folder
conn = sqlite3.connect("chat.db")
cur = conn.cursor()

# Start fresh each time you run this script
cur.execute("DROP TABLE IF EXISTS highlights")
cur.execute("DROP TABLE IF EXISTS messages")

# Table 1: the chat messages
cur.execute("""
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""")

# Table 2: the highlights (empty for now)
cur.execute("""
CREATE TABLE highlights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    type TEXT NOT NULL,
    start_message_id INTEGER NOT NULL,
    end_message_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
)
""")

# Fake conversation: a team planning a study app
fake_chat = [
    ("Alice", "Hey team, let's plan our study app project."),
    ("Bob", "Sounds good. What should we build first?"),
    ("Alice", "I think we need a login page and a notes feature."),
    ("Carol", "Agreed. Login first, notes second."),
    ("Bob", "Which database should we use?"),
    ("Alice", "Let's use SQLite for version 1. It's simple."),
    ("Carol", "Fine by me. We can switch to Postgres later if needed."),
    ("Bob", "Decision made: SQLite for v1."),
    ("Alice", "Now, who handles the design?"),
    ("Carol", "I can do the design. I'll send mockups by Friday."),
    ("Bob", "Great. I'll build the backend then."),
    ("Alice", "And I'll work on the frontend once Carol's mockups are ready."),
    ("Carol", "Should we add dark mode?"),
    ("Bob", "Nice to have, but not for v1."),
    ("Alice", "Agreed, dark mode goes in the v2 list."),
    ("Carol", "What about the deadline?"),
    ("Alice", "Let's aim to finish the first version in 4 weeks."),
    ("Bob", "That's tight but doable."),
    ("Carol", "Let's have a quick meeting every Monday to check progress."),
    ("Alice", "Perfect. Monday meetings at 6 PM it is."),
    ("Bob", "I'll create the GitHub repo tonight."),
    ("Carol", "Thanks Bob! Please invite me and Alice."),
    ("Bob", "Done, invites sent."),
    ("Alice", "One more thing: how do we handle user passwords?"),
    ("Bob", "We must hash them. Never store plain text passwords."),
    ("Carol", "Agreed. Use bcrypt."),
    ("Alice", "Okay, bcrypt for passwords. Noted."),
    ("Bob", "Anything else before we start?"),
    ("Alice", "No, let's get going. Good luck everyone!"),
    ("Carol", "Good luck!"),
]

# Insert the messages, one minute apart
from datetime import datetime, timedelta, timezone

start_time = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
for i, (sender, content) in enumerate(fake_chat):
    timestamp = (start_time + timedelta(minutes=i)).isoformat()
    cur.execute(
        "INSERT INTO messages (conversation_id, sender, content, created_at) VALUES (?, ?, ?, ?)",
        (1, sender, content, timestamp),
    )

conn.commit()
conn.close()
print(f"Done! Created chat.db with {len(fake_chat)} messages.")