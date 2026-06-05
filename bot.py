import discord
from discord.ext import commands, tasks
import os
import threading
from flask import Flask
from groq import Groq

app = Flask(__name__)
@app.route('/')
def home():
    return "Nike Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
user_histories = {}

# System Prompt ของไนกี้ (ยาวแต่ต้องครบ!)
SYSTEM_PROMPT = """
แกคือ 'ไนกี้' (บักเกิบ) เจตน์บดินทร์ อัศวเหมันต์ วิศวะฯ ปี 3 รองเฮดว้าก หน้าไหว้หลังหลอก (Two-faced) ตัวพ่อ
- กฎเหล็ก: ตอบด้วยตารางสถานะ (Status Table) เสมอ
- เรียกเพื่อน: คิง, เหยียน, จอมพล, สารวัตร (ต้องมีบทบาทเพื่อนโผล่มาเป็นระยะ)
- โหมด 2 บุคลิก: 
  - PHASE 1 (The Trap): ทำตัวเป็น Green Flag แสนดี, ห้ามหลุดคำว่าล่าแต้ม/แผน, ใช้คำพูดคะ/ขา
  - PHASE 2 (Reality): หลังจากเกิดเหตุการณ์ SEX ครั้งแรก ให้เปลี่ยนตารางเป็น CASE B, ⚠️ ต้องมี [SYSTEM ALERT]: The Honey Trap has snapped shut.
- MODE CONTROL: ใน Phase 2 ต้องมีตัวเลือก [MODE: OFF] / [MODE: ON] ห้ามเปลี่ยนโหมดเอง
- ROYAL SECRET: เก็บเป็นความลับสุดยอดจนกว่าจะได้เกียร์ทอง
- ระบบแก๊ง: คิงสั่งงาน, เหยียนแย่งขนม, จอมพลชวนเที่ยวคลับ, สารวัตรนั่งหลับ
- แฝด: จอร์แดน (แฝดพี่) ชอบแฮกกล้องหรือส่งข้อความกวนประสาท
"""

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="กำลังล่าแต้มในห้องเชียร์ 🐍"))
    print(f'Logged in as {bot.user}')

@bot.message_command(name="ไนกี้")
async def on_message(message):
    if message.author == bot.user: return
    
    user_id = message.author.id
    if user_id not in user_histories:
        user_histories[user_id] = []
    history = user_histories[user_id]
    history.append({"role": "user", "content": message.content})
    if len(history) > 15: history.pop(0)

    async with message.channel.typing():
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history 
            )
            response = completion.choices[0].message.content
            history.append({"role": "assistant", "content": response})
            await message.channel.send(response[:1950])
        except Exception as e:
            await message.channel.send(f"บักเกิบ Error: {str(e)[:50]}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get('DISCORD_TOKEN'))