from dotenv import load_dotenv
import os
from openai import OpenAI

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a terse assistant."},
            {"role": "user", "content": "Reply with exactly: OK"}
        ],
        temperature=0,
    )
    print(resp.choices[0].message.content)

if __name__ == "__main__":
    main()