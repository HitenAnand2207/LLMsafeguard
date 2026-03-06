"""
Run this from inside your backend folder:
  cd backend
  python test_groq.py
"""

import os
from dotenv import load_dotenv
import httpx

load_dotenv()

key = os.getenv("GROQ_API_KEY", "")

print("=" * 50)
print("GROQ API KEY DIAGNOSTIC")
print("=" * 50)

if not key:
    print("ERROR: GROQ_API_KEY is empty")
    print("   Fix: Open backend/.env and add:")
    print("   GROQ_API_KEY=your_key_here")
else:
    print(f"OK: Key found: {key[:8]}...{key[-4:]}")
    print(f"   Length: {len(key)} characters")

    # Test actual API call
    print("\nTesting Groq API call...")
    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Say hello in 3 words"}],
                "max_tokens": 20
            },
            timeout=15.0
        )

        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            print(f"OK: Groq API works. Response: {reply}")
            print("\nOK: Everything looks fine. Restart backend with: python main.py")
        elif response.status_code == 401:
            print("ERROR: API key is invalid or expired")
            print("   Go to https://console.groq.com and get a new key")
        elif response.status_code == 429:
            print("WARNING: Rate limit hit — wait a minute and try again")
        else:
            print(f"ERROR: Groq returned {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"ERROR: Network error: {e}")
        print("   Check your internet connection")