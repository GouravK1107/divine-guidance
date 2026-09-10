from dotenv import load_dotenv
load_dotenv()

from google import genai
import os

api_key = os.getenv("GEMINI_API_KEY")

print("API KEY LOADED:", bool(api_key))

client = genai.Client(
    api_key=api_key
)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Say hello in one short sentence."
)

print("\nRESPONSE:")
print(response.text)