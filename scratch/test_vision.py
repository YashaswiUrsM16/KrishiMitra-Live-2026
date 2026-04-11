import os
from groq import Groq
from config import Config

def test_vision():
    print("Testing Vision Model...")
    try:
        key = Config.GROQ_API_KEY
        client = Groq(api_key=key)
        # Empty image-like prompt just to test key
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )
        print("Success:", response.choices[0].message.content)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_vision()
