import google.generativeai as genai
import os
from bot.config import GEMINI_API_KEY

def list_models():
    if not GEMINI_API_KEY:
        print("No API Key found")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    
    print("Fetching available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
