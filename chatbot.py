import sys
import time
from openai import (
    OpenAI,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
)

# Make Urdu / Punjabi text work in the terminal
for stream in (sys.stdout, sys.stdin):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

# ---------------- SETTINGS (only change this part) ----------------
PROVIDER = "groq"  # "groq" = Groq (free tier, key starts with gsk_)
# "xai"  = Grok by xAI (credit based, key from console.x.ai)

API_KEY = "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"  # keep the quotes

# Model names change often. If you get "model not found", the program
# will print the models your key can use; copy one of them here.
MODELS = {
    "groq": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
    "xai": ["grok-4.3"],
}
BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "xai": "https://api.x.ai/v1",
}
# ------------------------------------------------------------------

MODEL_LIST = list(MODELS[PROVIDER])  # tried in order
MODEL = MODEL_LIST[0]

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URLS[PROVIDER],
    timeout=60.0,
)

SYSTEM_PROMPT = (
    "You are a friendly, helpful chatbot. Always reply in the same language "
    "and script the user writes in. You understand English, Urdu (اردو), "
    "Roman Urdu, Punjabi (پنجابی), and Roman Punjabi. If the user writes "
    "Roman Urdu, reply in Roman Urdu. Keep answers clear and concise."
)

history = [{"role": "system", "content": SYSTEM_PROMPT}]

print("=" * 50)
print("  Multilingual Chatbot (English / اردو / پنجابی)")
print("  Type 'exit' or 'quit' to stop")
print(f"  Provider: {PROVIDER}   Model: {MODEL}")
print("=" * 50)

while True:
    try:
        user_input = input("\nYou: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        break

    if not user_input:
        continue
    if user_input.lower() in ("exit", "quit"):
        print("Bot: Goodbye! Khuda hafiz!")
        break

    history.append({"role": "user", "content": user_input})
    print("[System] Bot is thinking...")
    answered = False

    for attempt in range(4):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=history,
                max_tokens=2000,
            )
            reply = (response.choices[0].message.content or "").strip()
            if not reply:
                print("[System] Empty reply, trying again...")
                continue
            history.append({"role": "assistant", "content": reply})
            print(f"\nBot: {reply}")
            answered = True
            break

        except AuthenticationError:
            print("\n[System] API key galat hai. Console se nayi key banayein.")
            break

        except NotFoundError:
            if len(MODEL_LIST) > 1:
                print(f"[System] Model '{MODEL}' not found, trying the next one.")
                MODEL_LIST.pop(0)
                MODEL = MODEL_LIST[0]
                print(f"[System] Model: {MODEL}")
                continue
            print(
                f"\n[System] Model '{MODEL}' not found. Your key can use these models:"
            )
            try:
                for m in client.models.list():
                    print("   ", m.id)
            except Exception as e2:
                print("    (could not list models):", e2)
            print("Put one chat model name in MODELS above and run again.")
            break

        except RateLimitError as e:
            print(f"\n[System] Limit ya credits ka masla: {e}")
            break

        except APIConnectionError:
            wait = 3 * (attempt + 1)
            print(f"[System] Internet ka masla, {wait}s baad dobara try...")
            time.sleep(wait)

        except APIStatusError as e:
            if e.status_code in (500, 502, 503, 504) and attempt < 3:
                wait = 3 * (attempt + 1)
                print(f"[System] Server busy, {wait}s baad dobara try...")
                time.sleep(wait)
            else:
                print(f"\n[System] Error: {e}")
                break

    if not answered:
        history.pop()  # remove the unanswered user message
        print("[System] Jawab nahi aaya. Thori der baad dobara message bhejein.")
