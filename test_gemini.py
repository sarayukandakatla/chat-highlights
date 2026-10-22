import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

key = os.environ.get("GEMINI_API_KEY")
print("Key found:", bool(key))

client = genai.Client(
    api_key=key,
    http_options=types.HttpOptions(timeout=60000),  # 60 seconds
)

models_to_try = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
]

for name in models_to_try:
    print(f"\nTrying {name} ...")
    try:
        response = client.models.generate_content(
            model=name,
            contents="Say hello in one short sentence.",
        )
        print("WORKS! Gemini says:", response.text)
        break
    except Exception as e:
        print("Failed:", str(e)[:150])