import sqlite3
from datetime import datetime, timezone

CONVERSATION_ID = 2

messages = [
    ("Dev", "Team, we need to finalize the launch plan for the new app."),
    ("Maya", "I think we should launch on Friday so we don't lose momentum."),
    ("Dev", "Friday is tight. Is the payment page ready?"),
    ("Sam", "Payment page still has two bugs. I need two more days."),
    ("Maya", "Okay, then let's move the launch to next Monday."),
    ("Dev", "Agreed. Final decision: we launch next Monday."),
    ("Sam", "I will fix the payment bugs by Saturday."),
    ("Maya", "I will write the release notes and send them to the team."),
    ("Dev", "Now, about pricing. Should we offer a free plan?"),
    ("Maya", "Yes, a free plan with limited features will bring more users."),
    ("Sam", "Agreed. Free plan plus a paid plan at 10 dollars a month."),
    ("Dev", "Decision made: free plan and a 10 dollar monthly plan."),
    ("Maya", "Dev, can you prepare the pricing page by Sunday?"),
    ("Dev", "Yes, I will build the pricing page by Sunday."),
]

conn = sqlite3.connect("chat.db")
conn.execute("DELETE FROM highlights WHERE conversation_id = ?", (CONVERSATION_ID,))
conn.execute("DELETE FROM messages WHERE conversation_id = ?", (CONVERSATION_ID,))

now = datetime.now(timezone.utc).isoformat()
for sender, content in messages:
    conn.execute(
        "INSERT INTO messages (conversation_id, sender, content, created_at) "
        "VALUES (?, ?, ?, ?)",
        (CONVERSATION_ID, sender, content, now),
    )

conn.commit()
conn.close()
print(f"Added {len(messages)} messages to conversation {CONVERSATION_ID}.")