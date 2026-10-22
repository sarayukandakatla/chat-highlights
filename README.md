# Chat Highlights Backend

FastAPI + SQLite + Gemini. Reads a chat and returns highlight cards (decision, topic, action_item) with start and end message ids, so a frontend can scroll to the exact message.

## Run it
1. Install Python.
2. pip install -r requirements.txt
3. Create a file named .env with this line: GEMINI_API_KEY=your_own_key
4. python setup_db.py
5. python -m uvicorn main:app --reload
6. Open http://127.0.0.1:8000/docs

## Endpoints
- GET  /conversations/{id}/messages
- POST /conversations/{id}/messages        body: {"sender": "...", "content": "..."}
- GET  /conversations/{id}/highlights
- POST /conversations/{id}/highlights/generate

## For the frontend
- Call POST /messages every time a user sends a message, and use the returned id as the message id on screen.
- Highlights point to messages with start_message_id and end_message_id. Scroll to start_message_id when a card is clicked.
- Each chat uses its own conversation id number.