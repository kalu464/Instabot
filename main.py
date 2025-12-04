import os
import time
from instagrapi import Client
from pathlib import Path

# ----------------------------
# CONFIG (READ FROM ENV)
# ----------------------------
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

if not IG_USERNAME or not IG_PASSWORD:
    print("❌ ERROR: IG_USERNAME or IG_PASSWORD not set as environment variables!")
    exit()

# ----------------------------
# SETUP
# ----------------------------
BASE = Path(__file__).parent
STORAGE_DIR = BASE / "storage"
SESSION_FILE = BASE / "session.json"

STORAGE_DIR.mkdir(exist_ok=True)

cl = Client()

# ----------------------------
# LOGIN
# ----------------------------
def login():
    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("✓ Loaded session file")
            return
        except:
            print("⚠ Session invalid, logging normally…")

    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(str(SESSION_FILE))
    print("✓ Logged in & saved session")

login()

# ----------------------------
# COMMAND HANDLERS
# ----------------------------
def handle_command(msg, thread_id, user_id, username):
    text = msg.lower()

    # /whoami
    if text == "/whoami":
        cl.direct_send(
            "👑 I am the retired leader of TEAM NXR.\nI protect confidential files.\nCommands: /save, /get, /list, /help",
            thread_id
        )
        return

    # /help
    if text == "/help":
        cl.direct_send(
            "📌 Commands:\n"
            "/save <name> (send with file)\n"
            "/get <name>\n"
            "/list\n"
            "/whoami",
            thread_id
        )
        return

    # /list
    if text == "/list":
        files = os.listdir(STORAGE_DIR)
        user_files = [f for f in files if f.startswith(f"{user_id}_")]
        
        if not user_files:
            cl.direct_send("📂 No saved items.", thread_id)
        else:
            names = [f.split("_", 1)[1] for f in user_files]
            cl.direct_send("📁 Saved items:\n" + "\n".join(names), thread_id)
        return

    # /get <name>
    if text.startswith("/get "):
        name = text.replace("/get ", "").strip()
        filename = f"{user_id}_{name}"

        filepath = STORAGE_DIR / filename
        if not filepath.exists():
            cl.direct_send("❌ Item not found.", thread_id)
            return
        
        cl.direct_send("", thread_id, file=str(filepath))
        return

    # /save <name>
    if text.startswith("/save "):
        cl.direct_send("📥 Please send the file with same name again.", thread_id)
        return


# ----------------------------
# POLLING LOOP
# ----------------------------
print("🤖 TEAM NXR STORAGE BOT STARTED…")

processed = set()

while True:
    try:
        inbox = cl.direct_threads()

        for th in inbox:
            if not th.items:
                continue

            msg_obj = th.items[0]
            msg_id = msg_obj.id

            if msg_id in processed:
                continue

            processed.add(msg_id)

            user = th.users[0]
            user_id = user.pk
            username = user.username

            text = msg_obj.text or ""
            media = msg_obj.media or None

            # COMMAND?
            if text.startswith("/"):
                handle_command(text, th.id, user_id, username)
                continue

            # FILE SAVE SYSTEM
            if media:
                name = text.strip()
                if not name:
                    cl.direct_send("❌ Use: /save <name> with file", th.id)
                    continue

                save_path = STORAGE_DIR / f"{user_id}_{name}"
                cl.direct_download(media.pk, str(save_path))

                cl.direct_send(f"✅ Saved as: {name}", th.id)
                continue

    except Exception as e:
        print("Error:", e)

    time.sleep(5)
