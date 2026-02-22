import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== CONFIG ==================
api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

if not api_id or not api_hash or not session_string:
    raise RuntimeError("Missing environment variables")

api_id = int(api_id)

# ================== KEEP RENDER ALIVE ==================
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_web).start()

# ================== TELEGRAM CLIENT ==================
client = TelegramClient(StringSession(session_string), api_id, api_hash)

temp_folder = "downloads"
os.makedirs(temp_folder, exist_ok=True)

def get_chat_id_and_msg_id(link):
    try:
        if 't.me/c/' in link:
            parts = link.split('/')
            chat_id = int('-100' + parts[-2])
            msg_id = int(parts[-1])
            return chat_id, msg_id
        elif 't.me/' in link:
            parts = link.split('/')
            chat_id = parts[-2]
            msg_id = int(parts[-1])
            return chat_id, msg_id
    except:
        pass
    return None, None

@client.on(events.NewMessage(chats='me'))
async def handler(event):
    text = event.message.text

    if text and text.startswith('/save'):
        try:
            link = text.split()[1]
            status_msg = await event.reply("⏳ กำลังทำงาน...")

            chat_id, msg_id = get_chat_id_and_msg_id(link)
            if not chat_id:
                await status_msg.edit("❌ ลิงก์ไม่ถูกต้อง")
                return

            msg = await client.get_messages(chat_id, ids=msg_id)

            if not msg:
                await status_msg.edit("❌ หาโพสต์ไม่เจอ")
                return

            # ====== ถ้าเป็นอัลบั้ม ======
            if msg.grouped_id:
                await status_msg.edit("⬇️ กำลังโหลดอัลบั้ม...")

                album = await client.get_messages(
                    chat_id,
                    min_id=msg.id - 20,
                    max_id=msg.id + 20
                )

                media_files = []

                for m in album:
                    if m.grouped_id == msg.grouped_id and (m.photo or m.video or m.document):
                        file_name = m.file.name or f"{m.id}"
                        save_path = os.path.join(temp_folder, file_name)
                        await client.download_media(m, save_path)
                        media_files.append(save_path)

                if media_files:
                    await status_msg.edit("⬆️ กำลังส่งอัลบั้ม...")
                    await event.reply(file=media_files)

                    for f in media_files:
                        os.remove(f)

                    await status_msg.delete()
                else:
                    await status_msg.edit("❌ ไม่พบสื่อในอัลบั้ม")

            # ====== สื่อเดี่ยว ======
            else:
                if msg.photo or msg.video or msg.document:
                    file_name = msg.file.name or f"{msg.id}"
                    save_path = os.path.join(temp_folder, file_name)

                    await status_msg.edit("⬇️ กำลังโหลด...")
                    await client.download_media(msg, save_path)

                    await status_msg.edit("⬆️ กำลังส่ง...")
                    await event.reply(file=save_path)

                    os.remove(save_path)
                    await status_msg.delete()
                else:
                    await status_msg.edit("❌ ไม่พบสื่อ")

        except Exception as e:
            await event.reply(f"❌ Error: {e}")

# ================== START ==================
if __name__ == "__main__":
    keep_alive()
    print("Bot Started...")
    client.start()
    client.run_until_disconnected()
