import os
import requests

API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = "deepseek-reasoner"
ENDPOINT = "https://api.deepseek.com/chat/completions"

if not API_KEY:
    raise RuntimeError("Missing DEEPSEEK_API_KEY environment variable")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

data = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"},
    ],
}

response = requests.post(
    ENDPOINT,
    headers=headers,
    json=data,
    timeout=30,
)

response.raise_for_status()
content = response.json()["choices"][0]["message"]["content"]
print(content.strip())
