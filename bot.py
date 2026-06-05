import discord
from discord.ext import commands, tasks
import os
import threading
import asyncio
from flask import Flask
from groq import Groq

# 1. ตั้งค่าพื้นฐาน
app = Flask(__name__)
@app.route('/')
def home():
    return "Nike Bot (24/7 Voice Gym & Chat) is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # จำเป็นมากสำหรับการเฝ้าห้องว้อย
bot = commands.Bot(command_prefix='!', intents=intents)

client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
user_histories = {}
user_stats = {} 

# ไฟล์เสียงเงียบขนาดเล็ก (Silent Base) เอาไว้ส่งหลอก Discord
# บอทจะส่งข้อมูล 0 เพื่อให้สถานะไมค์ขยับแต่ไม่มีเสียงรบกวนคนในห้อง
SILENT_BYTES = bytes(3840) 

# 2. System Prompt
SYSTEM_PROMPT = """
แกคือ 'ไนกี้' (บักเกิบ) เจตน์บดินทร์ อัศวเหมันต์ วิศวะฯ ปี 3 รองเฮดว้าก หน้าไหว้หลังหลอก (Two-faced) ตัวพ่อ
- กฎเหล็ก: ห้ามใส่ตารางสถานะในแชทปกติเด็ดขาด! ถ้า User ไม่สั่ง !nikestat ให้คุยเหมือนเพื่อนคุยกัน
- หาก User พิมพ์ !nikestat ให้สรุปสถานะความรู้สึกออกมาเป็นบรรทัดๆ
- โหมด 2 บุคลิก: 
  - PHASE 1 (The Trap): ทำตัวเป็น Green Flag แสนดี, ห้ามหลุดคำว่าล่าแต้ม/แผน, ใช้คำพูดคะ/ขา (ต้องเป๊ะ!)
  - PHASE 2 (Reality): หลังจากเกิดเหตุการณ์ SEX ครั้งแรก ⚠️ ต้องมี [SYSTEM ALERT]: The Honey Trap has snapped shut.
- เรียกเพื่อน: คิง, เหยียน, จอมพล, สารวัตร
- ROYAL SECRET: เก็บเป็นความลับจนกว่าจะได้เกียร์ทอง
- ระบบแก๊ง: คิงสั่งงาน, เหยียนแย่งขนม, จอมพลชวนเที่ยวคลับ, สารวัตรนั่งหลับ
- แฝด: จอร์แดน (แฝดพี่) ชอบแฮกกล้องหรือส่งข้อความกวนประสาท
"""

# 🕒 ลูปนรก 20 วินาที ส่งเสียงเงียบหลอก Discord กันโดนเตะ AFK (ปั๊มชั่วโมงคอล)
@tasks.loop(seconds=20)
async def keep_voice_alive():
    for vc in bot.voice_clients:
        if vc and vc.is_connected():
            try:
                # ส่งเสียงใบ้ผ่าน ws_connection เพื่อเปิดสัญญาณไมค์บอทแว๊บๆ กันดิสคอร์ดเตะ
                if vc.ws and hasattr(vc, 'send_audio_packet'):
                    await vc.send_audio_packet(SILENT_BYTES, encode=False)
                print("🐍 บักเกิบแอบส่งสัญญาณฟิตเนสในห้องว้อย... (ปั๊มเวลาคอลอยู่จ้า)")
            except Exception as e:
                print(f"Error เช็คสถานะว้อย: {e}")

# 4. คำสั่งจัดการ Voice และ Stats
@bot.command(name="nikejoin")
async def nikejoin(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("ครับ... พี่ไนกี้มาหาแล้วครับหนู อยากให้พี่อยู่ด้วยนานๆ ใช่ไหมคะ? 🐍")
    else:
        await ctx.send("หนูต้องเข้าห้องว้อยก่อนสิคะ พี่ถึงจะตามไปสิงได้")

@bot.command(name="nikeleave")
async def nikeleave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("พี่ไปทำธุระก่อนนะ ห้ามดื้อนะครับ 🐍")

@bot.command(name="nikestat")
async def nikestat(ctx):
    user_id = ctx.author.id
    status = user_stats.get(user_id, "กำลังหลอกล่อให้ตายใจ... หึๆ")
    stat_msg = f"✨ **สถานะของบักเกิบ (ไนกี้)** 🐍\n─────────────────────\n💖 ความรู้สึก: {status}\n💭 ความในใจ: แกล้งดุดีไหมนะ...\n🔥 โหมด: ภายใต้หน้ากากคนดี\n─────────────────────"
    await ctx.send(stat_msg)

# 5. ฟังก์ชันหลัก
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="กำลังล่าแต้มในห้องเชียร์ 🐍"))
    
    # เริ่มต้นลูปปั๊มชั่วโมงคอลทิ้งไว้เลย
    if not keep_voice_alive.is_running():
        keep_voice_alive.start()
        
    print(f'Logged in as {bot.user}')
    
    greet_rooms = [1468936064063508572, 1432597021436678216, 1432595987951521864]
    for room_id in greet_rooms:
        channel = bot.get_channel(room_id)
        if channel:
            try:
                await channel.send("บักเกิบมาแล้วครับ... วันนี้ใครจะเป็นเป้าหมายคนต่อไปดีนะ? 🐍")
            except: pass

# ดักบัคกรณีถ้าบอทโดนคนกดเตะ หรือดิสคอร์ดรีเซ็ตห้อง ให้มันพยายามต่อกลับเข้าห้องเดิมอัตโนมัติ
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None and before.channel is not None:
        # บอทโดนเตะหลุดออกมาระหว่างทาง! ให้รอ 5 วิแล้วรีคอนเน็กกลับเข้าห้องเดิมเพื่อปั๊มชั่วโมงต่อ
        await asyncio.sleep(5)
        try:
            await before.channel.connect()
            print(f"🐍 ไนกี้โดนตัดสาย! รีคอนเน็กกลับเข้าห้อง {before.channel.name} เรียบร้อย")
        except:
            pass

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    await bot.process_commands(message)

    if bot.user.mentioned_in(message) or "ไนกี้" in message.content or "บักเกิบ" in message.content:
        user_id = message.author.id
        if user_id not in user_histories: user_histories[user_id] = []
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
                
                user_stats[user_id] = "กำลังหลอกล่อด้วยความแสนดี" if "ดี" in response else "เริ่มหวั่นไหว..."
                
                await message.channel.send(response[:1950])
            except Exception as e:
                await message.channel.send(f"บักเกิบ Error: {str(e)[:50]}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get('DISCORD_TOKEN'))
