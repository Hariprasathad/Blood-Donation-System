from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit(1)

print(f"Checking available Gemini models for Key: {API_KEY[:10]}...")

try:
    client = genai.Client(api_key=API_KEY)
    
    # List models
    print("\nListing available models:")
    try:
        for m in client.models.list():
             if "generateContent" in m.supported_generation_methods:
                 print(f" - {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

except Exception as e:
    print("FAILURE! Client initialization error:")
    print(e)
