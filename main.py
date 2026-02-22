import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ===== CONFIG =====
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

# ===== KEEP RENDER ALIVE =====
app = Flask(__name__)

@app.route("/")
def home():
    return "I am alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

# ===== TELEGRAM CLIENT =====
client = TelegramClient(StringSession(session_string), api_id, api_hash)

TEMP_FOLDER = "downloads"
os.makedirs(TEMP_FOLDER, exist_ok=True)

def get_chat_id_and_msg_id(link):
    try:
        if "t.me/c/" in link:
            parts = link.split("/")
            return int("-100" + parts[-2]), int(parts[-1])
        elif "t.me/" in link:
            parts = link.split("/")
            return parts[-2], int(parts[-1])
    except:
        pass
    return None, None

@client.on(events.NewMessage(chats="me"))
async def handler(event):
    text = event.raw_text

    if not text.startswith("/save"):
        return

    try:
        link = text.split()[1]
    except:
        await event.reply("❌ ใส่ลิงก์มาด้วย")
        return

    status = await event.reply("⏳ กำลังทำงาน...")

    chat_id, msg_id = get_chat_id_and_msg_id(link)
    if not chat_id:
        await status.edit("❌ ลิงก์ไม่ถูกต้อง")
        return

    msg = await client.get_messages(chat_id, ids=msg_id)
    if not msg:
        await status.edit("❌ ไม่พบข้อความ")
        return

    messages_to_download = []

    # ===== รองรับ Album =====
    if msg.grouped_id:
        async for m in client.iter_messages(chat_id, reverse=True):
            if m.grouped_id == msg.grouped_id:
                if m.photo or m.video or m.document:
                    messages_to_download.append(m)
            elif messages_to_download:
                break
    else:
        if msg.photo or msg.video or msg.document:
            messages_to_download.append(msg)

    if not messages_to_download:
        await status.edit("❌ ไม่พบสื่อในโพสต์นี้")
        return

    await status.edit(f"⬇️ กำลังโหลด {len(messages_to_download)} ไฟล์...")

    downloaded_files = []

    for m in messages_to_download:
        file_path = await client.download_media(
            m,
            file=os.path.join(TEMP_FOLDER, "")
        )
        if file_path:
            downloaded_files.append(file_path)

    await status.edit("⬆️ กำลังอัปโหลดกลับ...")

    await client.send_file(
        "me",
        downloaded_files,
        caption=f"บันทึกแล้ว {len(downloaded_files)} ไฟล์"
    )

    # ลบไฟล์ชั่วคราว
    for f in downloaded_files:
        if os.path.exists(f):
            os.remove(f)

    await status.edit("✅ เสร็จแล้ว")
