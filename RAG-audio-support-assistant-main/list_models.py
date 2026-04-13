import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return

    print(f"Listing models for key: {api_key[:5]}...{api_key[-5:]}")
    try:
        client = genai.Client(api_key=api_key)
        # Using the v1 endpoint to list models
        models = client.models.list()
        print("\nAvailable Models:")
        for model in models:
            # strip 'models/' prefix if it exists for the generator logic
            name = model.name.replace('models/', '')
            print(f"- {name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_models()
