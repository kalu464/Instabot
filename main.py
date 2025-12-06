import asyncio, json, os, random, time, io, tempfile, datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging

# ---------------------------
# CONFIG
# ---------------------------
TOKENS = [
    "8556840049:AAFbRzRxhLRR7naSpdY2kUHZwlmK2HUaMmw",
    "8223994180:AAGeHlpRfdDOs_H4ATnZCCBbPel_ueVhGy0",
    "7747777752:AAHhNx_mR8omVRum9RQzlE_GkL435bW_wsQ",
    "7861901817:AAGKqKmx1zC5Qc5nV18Mf-0UvVFj2dw3vas",
    "8539074692:AAHH_6_IvqrIkLKjyjGXDkCEQYRyQuR1OKU",
    ]

OWNER_ID = 6469582618
SUDO_FILE = "sudo.json"

# ---------------------------
# RAID TEXTS
# ---------------------------
RAID_TEXTS = [
    "NOBI IS  FUCKING YOUR MOM LIL NIGGA 🥱🤬🖕🏻",
    "😂😂😂😂SON OF MY SLUT 😂😂😂😂",
    "YOUR MOMS BUSY WITH ME LIL BRO 😌",
    "TMKC MAAR LUNGEE RAND KA BACCH3  !!🔥😂🩴",
    "😉😈🔥هههههههههههههه Teri maa रंडी",
    "😏𝐂ʜʟ 𝐇ᴀʀᴍᴢᴀᴅ𝐈 𝐊ᴇ लड़के 💛🤍🩵",
    "🥹😜HLO BBY MAJEE A RAHE HAI CHUDD NA MAI?",
    "🤬🖕🏻AAJ TERI MA NOBI PAPA SAI CHUDE GI ",
    "ITNI JALDI CHUDD GYA TU?🤮",
    "FASS FASS CHUDDD AAB TU 🤣😭",
    "RAAND KA BACCHE , NOBI PAPA JINDE BAAD BOL 🤣🖕",
    "TERI MA RUNDI?OKH?NOBI PAPA OP BOL 🤮🤢",
    "TERI MA KI CHUT MAI LODE OkH?",
    "AWAZ NICHE KR , TERI BAAP NOBI HERE 👿",
    "SAWAL MT PUCH , CHUP CHAAP CHUDD TU 😍",
]

# ---------------------------
# NCEMO EMOJIS
# ---------------------------
NCEMO_EMOJIS = [
    "🔥","⚡","💥","💀","🕊","💫","🌪","🐉","👑","🌟","💎","🎭","🚀","✨","🔮",
 "🎯","🌀","🐺","🦅","🐍","🎇","🎆","💠","💣","🧨","🎉","🎊","🌈","🌊","🌙",
 "⭐","🌞","🌝","🌛","🌚","☄️","🌋","🏆","🥇","🎖️","🏅","🎗️","🏵️","🌺","🌸",
 "🌼","🌻","🌹","⚓","🛡️","⚔️","🪄","🧿","🪶","🕹️","🎮","🎲","🧩","🎵","🎶",
 "🎼","🎧","🎤","🎷","🎸","🎺","🥁","📯","📀","📣","📯","🛸","🛰️","🏹","🗡️",
 "🛡️","🩸","⚗️","🔭","🔬","💉","🧪","📚","📖","📝","✒️","🖋️","🖊️","✏️","📐",
 "📏","🧭","🔧","⚙️","🔩","🧱","🏗️","🏛️","🧭","🗺️","🧭","🔔","🔕","💡","🔦"
]

# ---------------------------
# GLOBAL STATE
# ---------------------------
if os.path.exists(SUDO_FILE):
    try:
        with open(SUDO_FILE, "r") as f:
            _loaded = json.load(f)
            SUDO_USERS = set(int(x) for x in _loaded)
    except Exception:
        SUDO_USERS = {OWNER_ID}
else:
    SUDO_USERS = {OWNER_ID}
with open(SUDO_FILE, "w") as f: json.dump(list(SUDO_USERS), f)

def save_sudo():
    with open(SUDO_FILE, "w") as f: json.dump(list(SUDO_USERS), f)

group_tasks = {}
slide_targets = set()
slidespam_targets = set()
swipe_mode = {}
apps, bots = [], []
delay = 1
spam_tasks = {}  # chat_id -> bot.id -> task
spam_delay = 1   # fixed 1s delay for /gcspam

# ---------------------------
# NEW: DP / PFP auto-change state (multi-bot)
# ---------------------------
# Structure:
#   dp_tasks[chat_id] = { bot_id: asyncio.Task(...) , ... }
#   dp_image_cache[chat_id] = image_bytes
dp_tasks = {}
dp_image_cache = {}
pfp_delay = 5  # seconds between each change per bot (you can change if needed)

# ---------------------------
# NEW: Menu & Stats state
# ---------------------------
START_TIME = time.time()

MENU_TEXT = """
🔥  ️𝗞𝗛𝗔𝗧𝗔𝗥𝗡𝗔𝗞 𝗠𝗘𝗡𝗨  — 𝗡𝗢𝗕𝗜𝗫 𝗘𝗗𝗜𝗧𝗢𝗥 🔥

────────────────────────────────────────
⚡ 𝗚𝗘𝗡𝗘𝗥𝗔𝗟 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦:
• /help      — Full Help Panel
• /menu      — Khatarnak Menu (this)
• /stats     — Live Bot Stats
• /myid      — Your ID
• /ping      — Ping Bot

────────────────────────────────────────
👑 𝗢𝗪𝗡𝗘𝗥 & 𝗦𝗨𝗗𝗢:
• /addsudo   — Add sudo (reply)
• /delsudo   — Remove sudo (reply)
• /listsudo  — List sudos

────────────────────────────────────────
🌀 𝗟𝗢𝗢𝗣 𝗠𝗢𝗗𝗘𝗦:
• /gcnc <text>  — GC name loop (raid)
• /ncemo <text> — Emoji loop
• /stopgcnc     — Stop GC loops
• /stopall      — Stop all loops

────────────────────────────────────────
🖼️ 𝗣𝗙𝗣 / 𝗗𝗣:
• Reply to a photo with /dpchange  — Start multi-bot DP auto-change
• /stoppfp                         — Stop DP auto-change for this chat

────────────────────────────────────────
⚠️ 𝗡𝗢𝗧𝗘𝗦:
• Add every bot from TOKENS into the target chat and give 'change info' permission.
• Change pfp_delay at top to speed up/slow down.
────────────────────────────────────────

🔥 𝗧𝗛𝗜𝗦 𝗜𝗦 𝗔 𝗞𝗛𝗔𝗧𝗔𝗥𝗡𝗔𝗞 𝗗𝗘𝗩 𝗦𝗖𝗥𝗜𝗣𝗧 — 𝗕𝗘 𝗖𝗔𝗥𝗘𝗙𝗨𝗟 🔥
"""

logging.basicConfig(level=logging.INFO)

# ---------------------------
# DECORATORS
# ---------------------------
def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in SUDO_USERS:
            return await update.message.reply_text("❌ You are not sudo, bitch.")
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            return await update.message.reply_text("❌ Only owner can do this.")
        return await func(update, context)
    return wrapper

# ---------------------------
# Helper: write bytes to temp file (kept for compatibility)
# ---------------------------
def write_temp_bytes(data, ext=".jpg"):
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path

# ---------------------------
# NEW: DP worker per bot
# ---------------------------
async def _pfp_worker(bot_instance, chat_id, img_bytes):
    """
    Background worker that repeatedly sets chat photo for given bot_instance.
    It will exit when cancelled.
    """
    bot_id = bot_instance.id
    try:
        while True:
            try:
                bio = io.BytesIO(img_bytes)
                bio.name = "pfp.jpg"
                bio.seek(0)
                await bot_instance.set_chat_photo(chat_id, bio)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[WARN] set_chat_photo failed for bot {bot_id} in chat {chat_id}: {e}")
                await asyncio.sleep(2)
            await asyncio.sleep(pfp_delay)
    finally:
        tasks = dp_tasks.get(chat_id)
        if tasks:
            tasks.pop(bot_id, None)
            if not tasks:
                dp_tasks.pop(chat_id, None)
                dp_image_cache.pop(chat_id, None)

# ---------------------------
# NEW COMMAND: /dpchange
# ---------------------------
@only_sudo
async def dpchange_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: Reply to a photo with /dpchange
    Starts multi-bot pfp auto-change (one worker per bot in TOKENS).
    """
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await update.message.reply_text("Reply to a photo and use /dpchange")

    chat_id = update.message.chat_id

    # download highest-res photo
    fobj = await update.message.reply_to_message.photo[-1].get_file()
    img_bytes = await fobj.download_as_bytearray()

    # store image
    dp_image_cache[chat_id] = img_bytes

    # ensure dict
    dp_tasks.setdefault(chat_id, {})

    started = 0
    for bot in bots:
        # if a worker already exists for this bot in this chat, cancel & restart it
        existing = dp_tasks[chat_id].get(bot.id)
        if existing:
            try:
                existing.cancel()
            except:
                pass

        # create new worker for this bot
        task = asyncio.create_task(_pfp_worker(bot, chat_id, img_bytes))
        dp_tasks[chat_id][bot.id] = task
        started += 1

    if started:
        await update.message.reply_text(f"🌀 DP/PFP auto-change started on {started} bots. Use /stoppfp to stop.")
    else:
        await update.message.reply_text("⚠️ No bots available to start DP auto-change.")

# ---------------------------
# NEW COMMAND: /stoppfp
# ---------------------------
@only_sudo
async def stoppfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Stops DP auto-change (for the chat where command is used).
    """
    chat_id = update.message.chat_id
    tasks = dp_tasks.get(chat_id)
    if not tasks:
        return await update.message.reply_text("⚠️ No running DP auto-change found in this chat.")

    for task in list(tasks.values()):
        try:
            task.cancel()
        except:
            pass

    dp_tasks.pop(chat_id, None)
    dp_image_cache.pop(chat_id, None)

    await update.message.reply_text("🛑 Auto DP change stopped for this chat.")

# ---------------------------
# MENU COMMAND
# ---------------------------
async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Public menu with aesthetic styling.
    """
    # send the MENU_TEXT (keep formatting)
    await update.message.reply_text(MENU_TEXT)

# ---------------------------
# STATS COMMAND
# ---------------------------
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns runtime stats: number of bots, active DP tasks, active GC loops, uptime.
    """
    uptime_seconds = int(time.time() - START_TIME)
    uptime = str(datetime.timedelta(seconds=uptime_seconds))
    total_bots = len(bots)
    dp_chats = len(dp_tasks)
    dp_workers = sum(len(t) for t in dp_tasks.values()) if dp_tasks else 0
    active_gc_chats = len(group_tasks)
    msg = (
        f"📊 <b>Bot Stats</b>\n"
        f"• Bots loaded: {total_bots}\n"
        f"• DP-auto chats: {dp_chats}\n"
        f"• DP-workers total: {dp_workers}\n"
        f"• Active GC-loop chats: {active_gc_chats}\n"
        f"• Uptime: {uptime}\n"
    )
    # edit: send as plain text (no HTML parse to keep simple)
    await update.message.reply_text(msg)

# ---------------------------
# LOOP FUNCTION (unchanged)
# ---------------------------
async def bot_loop(bot, chat_id, base, mode):
    i = 0
    while True:
        try:
            if mode == "raid":
                text = f"{base} {RAID_TEXTS[i % len(RAID_TEXTS)]}"
            else:
                text = f"{base} {NCEMO_EMOJIS[i % len(NCEMO_EMOJIS)]}"
            await bot.set_chat_title(chat_id, text)
            i += 1
            await asyncio.sleep(delay)
        except Exception as e:
            print(f"[WARN] Bot error in chat {chat_id}: {e}")
            await asyncio.sleep(2)

# ---------------------------
# COMMANDS (unchanged except added menu & stats handlers)
# ---------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "𓆩𓆩⃟⚡𝐍𝐎𝐁𝐈𝐗 ~ भगवान हूँ - 🔱 ⃟𓆪𓆪\n"
        "✨ Welcome! Use /menu to open the Khatarnak Menu."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "𓆩𓆩⃟⚡𝐍𝐎𝐁𝐈𝐗 ~ भगवान हूँ - 🔱 ⃟𓆪𓆪\n"
        "Use /menu for the full Khatarnak menu."
    )

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    latency = int((end_time - start_time) * 1000)
    await msg.edit_text(f"🏓 Pong! ✅ {latency} ms")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your ID: {update.effective_user.id}")

# --- GC Loops ---
@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("⚠️ Usage: /gcnc <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for bot in bots:
        if bot.id not in group_tasks[chat_id]:
            task = asyncio.create_task(bot_loop(bot, chat_id, base, "raid"))
            group_tasks[chat_id][bot.id] = task
    await update.message.reply_text("🔄 GC name loop started with raid texts.")

@only_sudo
async def ncemo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("⚠️ Usage: /ncemo <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for bot in bots:
        if bot.id not in group_tasks[chat_id]:
            task = asyncio.create_task(bot_loop(bot, chat_id, base, "emoji"))
            group_tasks[chat_id][bot.id] = task
    await update.message.reply_text("🔄 Emoji loop started with all bots.")

@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in group_tasks:
        for task in group_tasks[chat_id].values():
            task.cancel()
        group_tasks[chat_id] = {}
        await update.message.reply_text("⏹ Loop stopped in this GC.")

@only_sudo
async def stopall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(group_tasks.keys()):
        for task in group_tasks[chat_id].values():
            task.cancel()
        group_tasks[chat_id] = {}
    await update.message.reply_text("⏹ All loops stopped.")

@only_sudo
async def delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global delay
    if not context.args: return await update.message.reply_text(f"⏱ Current delay: {delay}s")
    try:
        delay = max(0.5, float(context.args[0]))
        await update.message.reply_text(f"✅ Delay set to {delay}s")
    except: await update.message.reply_text("⚠️ Invalid number.")

@only_sudo
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 Active Loops:\n"
    for chat_id, tasks in group_tasks.items():
        msg += f"Chat {chat_id}: {len(tasks)} bots running\n"
    await update.message.reply_text(msg)

# --- SUDO ---
@only_owner
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
        SUDO_USERS.add(uid); save_sudo()
        await update.message.reply_text(f"✅ {uid} added as sudo.")

@only_owner
async def delsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
        if uid in SUDO_USERS:
            SUDO_USERS.remove(uid); save_sudo()
            await update.message.reply_text(f"🗑 {uid} removed from sudo.")

@only_sudo
async def listsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 SUDO USERS:\n" + "\n".join(map(str, SUDO_USERS)))

# --- Slide / Spam / Swipe ---
@only_sudo
async def targetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slide_targets.add(update.message.reply_to_message.from_user.id)
        await update.message.reply_text("🎯 Target slide added.")

@only_sudo
async def stopslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
        slide_targets.discard(uid)
        await update.message.reply_text("🛑 Target slide stopped.")

@only_sudo
async def slidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slidespam_targets.add(update.message.reply_to_message.from_user.id)
        await update.message.reply_text("💥 Slide spam started.")

@only_sudo
async def stopslidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slidespam_targets.discard(update.message.reply_to_message.from_user.id)
        await update.message.reply_text("🛑 Slide spam stopped.")

@only_sudo
async def swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("⚠️ Usage: /swipe <name>")
    swipe_mode[update.message.chat_id] = " ".join(context.args)
    await update.message.reply_text(f"⚡ Swipe mode ON with name: {swipe_mode[update.message.chat_id]}")

@only_sudo
async def stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    swipe_mode.pop(update.message.chat_id, None)
    await update.message.reply_text("🛑 Swipe mode stopped.")

# --- Auto Replies ---
async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid, chat_id = update.message.from_user.id, update.message.chat_id
    if uid in slide_targets:
        for text in RAID_TEXTS: await update.message.reply_text(text)
    if uid in slidespam_targets:
        for text in RAID_TEXTS: await update.message.reply_text(text)
    if chat_id in swipe_mode:
        for text in RAID_TEXTS: await update.message.reply_text(f"{swipe_mode[chat_id]} {text}")

# --- GC Spam ---
@only_sudo
async def gcspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    texts = [" ".join(context.args)] if context.args else RAID_TEXTS

    spam_tasks.setdefault(chat_id, {})
    started = 0

    for bot in bots:
        if bot.id not in spam_tasks[chat_id]:
            async def spam_loop(bot_instance):
                i = 0
                while True:
                    try:
                        await bot_instance.send_message(chat_id, texts[i % len(texts)])
                        i += 1
                        await asyncio.sleep(spam_delay)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        print(f"[WARN] Spam error in chat {chat_id}, bot {bot_instance.id}: {e}")
                        await asyncio.sleep(1)

            task = asyncio.create_task(spam_loop(bot))
            spam_tasks[chat_id][bot.id] = task
            started += 1

    if started:
        await update.message.reply_text(f"💥 Spam started with {started} bots!")
    else:
        await update.message.reply_text("⚠️ All bots already spamming in this GC.")

@only_sudo
async def stopspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in spam_tasks:
        for task in spam_tasks[chat_id].values():
            task.cancel()
        spam_tasks[chat_id] = {}
        await update.message.reply_text("🛑 Spam stopped in this GC.")
    else:
        await update.message.reply_text("⚠️ No spam running in this GC.")

# ---------------------------
# BUILD APP & RUN (handlers registration includes menu & stats)
# ---------------------------
def build_app(token):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("ncemo", ncemo))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("stopall", stopall))
    app.add_handler(CommandHandler("delay", delay_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("delsudo", delsudo))
    app.add_handler(CommandHandler("listsudo", listsudo))
    app.add_handler(CommandHandler("targetslide", targetslide))
    app.add_handler(CommandHandler("stopslide", stopslide))
    app.add_handler(CommandHandler("slidespam", slidespam))
    app.add_handler(CommandHandler("stopslidespam", stopslidespam))
    app.add_handler(CommandHandler("swipe", swipe))
    app.add_handler(CommandHandler("stopswipe", stopswipe))
    app.add_handler(CommandHandler("gcspam", gcspam))
    app.add_handler(CommandHandler("stopspam", stopspam))

    # DP handlers (already integrated)
    app.add_handler(CommandHandler("dpchange", dpchange_cmd))
    app.add_handler(CommandHandler("stoppfp", stoppfp_cmd))

    # NEW: menu & stats
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandH
