import requests

API_KEY = "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"
MODEL = "deepseek/deepseek-chat-v3.1:free"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Title": "Hello World Test",
    "HTTP-Referer": "https://openrouter.ai",  # use the main site domain
}

data = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"}
    ]
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=data
)

content = response.json()["choices"][0]["message"]["content"]
print(content.strip().replace("<｜begin▁of▁sentence｜>", ""))

