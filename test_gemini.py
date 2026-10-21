import json
import os
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "api_key.txt")
MODEL = "gemini-2.5-flash"

key = os.environ.get("GEMINI_API_KEY")
if not key and os.path.exists(KEY_FILE):
    key = open(KEY_FILE, encoding="utf-8").read().strip()

if not key:
    raise SystemExit("NO KEY FOUND. Create api_key.txt next to this file with only your key in it.")

print("Key found, length:", len(key), "| starts with:", key[:4] + "...")

url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
body = json.dumps({"contents": [{"parts": [{"text": "Say hello in 5 words."}]}]}).encode("utf-8")
req = urllib.request.Request(
    url, data=body,
    headers={"Content-Type": "application/json", "x-goog-api-key": key},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    print("WORKS:", data["candidates"][0]["content"]["parts"][0]["text"])
except urllib.error.HTTPError as e:
    print("HTTP ERROR", e.code)
    print(e.read().decode("utf-8"))
except Exception as e:
    print("ERROR:", e)