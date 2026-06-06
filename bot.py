import discord
from discord.ext import commands, tasks
import os
import threading
import asyncio
import re
import requests
from flask import Flask
from groq import Groq

# 1. ตั้งค่าพื้นฐาน
app = Flask(__name__)
@app.route('/')
def home():
    return "Nike Bot (Dual-Core Fixed Version) is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# 🔑 ระบบดักจับ API Key (ฉลาดขึ้น ดักทุกทาง)
# ==========================================
# ดักจับทั้ง GROQ_API_KEY หรือ GROQ_API_KEYS (เผื่อแกใส่แบบไหนมาก็ใช้ได้หมด)
GROQ_KEY = os.environ.get('GROQ_API_KEY') or os.environ.get('GROQ_API_KEYS')
OR_KEY = os.environ.get('OPENROUTER_API_KEY')

# ล้างช่องว่างเผื่อก๊อปติดมา
if GROQ_KEY: GROQ_KEY = GROQ_KEY.strip()
if OR_KEY: OR_KEY = OR_KEY.strip()

client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

user_histories = {}
user_stats = {} 

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

# 🕒 ฟังก์ชันสำหรับเล่นเสียงใบ้แบบวนลูป (แก้บั๊ก No such file)
def play_silent_loop(vc):
    if vc and vc.is_connected() and not vc.is_playing():
        try:
            # แก้ไขตรงนี้: ใช้ช่องทางตรง -i null เพื่อสร้างเสียงเงียบสนิท ไม่ต้องเรียกชื่อไฟล์มั่วซั่ว
            source = discord.FFmpegPCMAudio(
                "-",
                before_options="-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000",
                options="-f s16le"
            )
            vc.play(source, after=lambda e: bot.loop.create_task(check_and_loop_voice(vc)))
        except Exception as e:
            print(f"ขัดข้องตอนเปิดเสียงใบ้: {e}")

async def check_and_loop_voice(vc):
    await asyncio.sleep(2) # เพิ่มเวลาหน่วงกันลูปนรกสแปม
    if vc and vc.is_connected() and not vc.is_playing():
        play_silent_loop(vc)

@tasks.loop(minutes=1)
async def keep_voice_alive():
    for vc in bot.voice_clients:
        if vc and vc.is_connected() and not vc.is_playing():
            try:
                play_silent_loop(vc)
                print("🐍 บักเกิบล็อคสายเสียงเงียบ ปั๊มเวลาสะสมดิสหลักเรียบร้อย")
            except: pass

# 4. คำสั่งจัดการ Voice และ Stats
@bot.command(name="nikejoin")
async def nikejoin(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        await ctx.send("ครับ... พี่ไนกี้มาหาแล้วครับหนู อยากให้พี่อยู่ด้วยนานๆ ใช่ไหมคะ? 🐍")
        play_silent_loop(vc)
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
    if not keep_voice_alive.is_running():
        keep_voice_alive.start()
    print(f'Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None and before.channel is not None:
        await asyncio.sleep(5)
        try:
            vc = await before.channel.connect()
            play_silent_loop(vc)
        except: pass

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
            response_text = ""
            messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + history

            try:
                # 🧠 แผน A: พยายามใช้ Groq (ตัวหลัก)
                if not client:
                    raise Exception("400: No Groq Client Configured")
                    
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_payload 
                )
                response_text = completion.choices[0].message.content
                print("✅ ตอบด้วยสมอง: Groq")

            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Groq ช็อตด้วยอาการ ({error_msg[:30]})! สลับไปถาม OpenRouter...")
                
                # 🧠 แผน B: ใช้ OpenRouter (ตัวสำรอง)
                if OR_KEY:
                    try:
                        headers = {
                            "Authorization": f"Bearer {OR_KEY}",
                        }
                        data = {
                            "model": "meta-llama/llama-3-8b-instruct:free",
                            "messages": messages_payload
                        }
                        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                        or_data = response.json()
                        
                        response_text = or_data['choices'][0]['message']['content']
                        print("✅ ตอบด้วยสมอง: OpenRouter (สำรอง)")
                        
                    except Exception as or_e:
                        await message.channel.send("หนูคะ... ตอนนี้พี่ติดงานด่วนที่ภาควิชาแป๊บนึงนะครับ รอพี่สักครู่นะคะคนดี 🐍")
                        history.pop()
                        return
                else:
                    await message.channel.send("พี่เบลอไปหมดแล้วครับหนู ลืมเช็กค่า API KEY ในหน้าตั้งค่าหรือเปล่าคะคนดี? 🐍")
                    history.pop()
                    return

            if response_text:
                history.append({"role": "assistant", "content": response_text})
                user_stats[user_id] = "กำลังหลอกล่อด้วยความแสนดี" if "ดี" in response_text else "เริ่มหวั่นไหว..."
                await message.channel.send(response_text[:1950])

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get('DISCORD_TOKEN'))
