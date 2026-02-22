from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit(1)

print(f"Checking available Gemini models for Key: {API_KEY[:5]}...")

try:
    client = genai.Client(api_key=API_KEY)
    
    # Try a simple generation with a known stable model first as a fallback check
    print("\nAttempting generation with 'gemini-1.5-flash'...")
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents='Hello'
        )
        print(f"SUCCESS: gemini-1.5-flash is working. Response: {response.text}")
    except Exception as e:
        print(f"FAILED: gemini-1.5-flash not working. Error: {e}")

    print("\nAttempting generation with 'gemini-2.0-flash'...")
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='Hello'
        )
        print(f"SUCCESS: gemini-2.0-flash is working. Response: {response.text}")
    except Exception as e:
        print(f"FAILED: gemini-2.0-flash not working. Error: {e}")

except Exception as e:
    print("FAILURE! Client initialization error:")
    print(e)
