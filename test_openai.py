from dotenv import load_dotenv
import os
from openai import OpenAI

def main():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        raise RuntimeError("OPENAI_API_KEY not found. Make sure .env is in project root and has OPENAI_API_KEY=...")

    # Safe confirmation (do NOT print full key)
    print("Loaded OPENAI_API_KEY prefix:", key[:10])

    client = OpenAI(api_key=key)

    # Minimal, cheap sanity check: list models
    models = client.models.list()
    first = models.data[0].id if models.data else "NO_MODELS_RETURNED"
    print("API OK. Example model id:", first)

if __name__ == "__main__":
    main()