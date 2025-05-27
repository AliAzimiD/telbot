#!/usr/bin/env python3
import os
import sys

try:
    import openai
except ImportError:
    print("Please install the OpenAI library first:\n    pip install openai")
    sys.exit(1)

def test_openai_api():
    # 1. Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        return False

    openai.api_key = api_key

    # 2. Try to list models using the new API
    try:
        print("Listing models…")
        resp = openai.models.list()
        # resp is a SyncPage of Model objects, so use .data
        models = resp.data  
        print(f"✅ Successfully retrieved {len(models)} models.")
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return False

    # 3. Send a quick chat completion
    try:
        print("Sending test completion…")
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # widely available model
            messages=[{"role": "user", "content": "Say hello in one word."}],
            temperature=0
        )
        content = chat.choices[0].message.content.strip()
        print(f"✅ Completion succeeded: “{content}”")
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_openai_api()
    sys.exit(0 if success else 1)
