import os
import asyncio
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- ค่า Config (จะไปตั้งใน Render) ---
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

# --- ส่วน Web Server (เพื่อให้ Render ไม่ปิดบอท) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_web():
    # Render จะส่ง Port มาให้ทาง Environment Variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- ส่วน Bot Userbot ---
client = TelegramClient(StringSession(session_string), api_id, api_hash)

# โฟลเดอร์ชั่วคราว
temp_folder = 'downloads'
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

# ฟังก์ชันดึง ID
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
            status_msg = await event.reply(f"⏳ กำลังทำงาน...")
            
            chat_id, msg_id = get_chat_id_and_msg_id(link)
            if chat_id:
                msg = await client.get_messages(chat_id, ids=msg_id)
                if msg and (msg.video or msg.photo or msg.document):
                    file_name = msg.file.name or f"video_{msg.id}.mp4"
                    save_dest = os.path.join(temp_folder, file_name)
                    
                    await status_msg.edit(f"⬇️ กำลังโหลด...")
                    await client.download_media(msg, save_dest)
                    
                    await status_msg.edit(f"⬆️ กำลังส่ง...")
                    await event.reply(file=save_dest, message="เรียบร้อยครับเจ้านาย")
                    
                    os.remove(save_dest)
                    await status_msg.delete()
                else:
                    await status_msg.edit("❌ ไม่พบสื่อ")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")

# --- Main Start ---
if __name__ == "__main__":
    keep_alive() # เปิดเว็บเซิร์ฟเวอร์
    print("Bot Started...")
    client.start()
    client.run_until_disconnected()