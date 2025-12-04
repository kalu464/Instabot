import os
import time
import requests
from pathlib import Path
from instagrapi import Client

# ----------------------------
# CONFIG (ENV)
# ----------------------------
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

if not IG_USERNAME or not IG_PASSWORD:
    print("❌ Set IG_USERNAME and IG_PASSWORD in environment variables!")
    exit()

# ----------------------------
# FOLDERS
# ----------------------------
BASE = Path(__file__).parent
STORAGE = BASE / "storage"
SESSION = BASE / "session.json"

STORAGE.mkdir(exist_ok=True)

cl = Client()

# ----------------------------
# LOGIN
# ----------------------------
def login():
    if SESSION.exists():
        try:
            cl.load_settings(str(SESSION))
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("✓ Session loaded")
            return
        except:
            print("⚠ Old session invalid, logging fresh...")

    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(str(SESSION))
    print("✓ Logged in & saved session")


login()

# ----------------------------
# SEND DM
# ----------------------------
def send_dm(text, thread_id, file=None):
    try:
        cl.direct_send(text, thread_id, file=file)
    except Exception as e:
        print("DM ERROR:", e)

# ----------------------------
# COMMAND HANDLER
# ----------------------------
def handle_command(msg, thread_id, user_id):
    text = msg.lower()

    if text == "/help":
        send_dm(
            "📌 Commands:\n"
            "/save <name> (send with file)\n"
            "/get <name>\n"
            "/list\n"
            "/whoami",
            thread_id
        )
        return

    if text == "/whoami":
        send_dm("👑 TEAM NXR Secure Storage Bot", thread_id)
        return

    if text == "/list":
        files = os.listdir(STORAGE)
        user_files = [f for f in files if f.startswith(f"{user_id}_")]

        if not user_files:
            send_dm("📂 No saved items.", thread_id)
        else:
            names = [f.split("_", 1)[1] for f in user_files]
            send_dm("📁 Saved items:\n" + "\n".join(names), thread_id)
        return

    if text.startswith("/get "):
        name = text.replace("/get ", "").strip()
        filepath = STORAGE / f"{user_id}_{name}"

        if not filepath.exists():
            send_dm("❌ Not found.", thread_id)
            return

        send_dm("", thread_id, file=str(filepath))
        return

    if text.startswith("/save "):
        send_dm("📥 Now send file again with same name.", thread_id)
        return


# ----------------------------
# SAVE FILE
# ----------------------------
def save_file(msg, thread_id, user_id):
    if not msg.text:
        send_dm("❌ Use: /save <name> with file", thread_id)
        return

    filename = msg.text.strip()
    file_path = STORAGE / f"{user_id}_{filename}"

    try:
        url = msg.media_url
        if not url:
            send_dm("❌ Media URL missing!", thread_id)
            return

        data = requests.get(url).content
        with open(file_path, "wb") as f:
            f.write(data)

        send_dm(f"✅ Saved as {filename}", thread_id)
    except Exception as e:
        print("SAVE ERROR:", e)
        send_dm("❌ Failed to save file.", thread_id)


# ----------------------------
# MAIN LOOP
# ----------------------------
print("🤖 TEAM NXR STORAGE BOT STARTED…")

processed = set()

while True:
    try:
        inbox = cl.direct_threads()

        for th in inbox:
            if not th.items:
                continue

            msg = th.items[0]  # latest message
            msg_id = msg.id
            user = th.users[0]
            user_id = user.pk

            if msg_id in processed:
                continue
            processed.add(msg_id)

            # COMMAND
            if msg.text and msg.text.startswith("/"):
                handle_command(msg.text, th.id, user_id)
                continue

            # MEDIA
            if msg.media:
                save_file(msg, th.id, user_id)

    except Exception as e:
        print("LOOP ERROR:", e)

    time.sleep(5)
