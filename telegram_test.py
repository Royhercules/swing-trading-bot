import os
import requests

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

print("BOT_TOKEN:", BOT_TOKEN)
print("CHAT_ID:", CHAT_ID)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

resp = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": "✅ TELEGRAM TEST FROM GITHUB ACTION",
    },
    timeout=10
)

print("STATUS:", resp.status_code)
print("RESPONSE:", resp.text)
