import discord
from discord.ext import commands, tasks
import os
import threading
import asyncio
import re
import requests  # <--- ใช้ตัวนี้ดึง OpenRouter
from flask import Flask
from groq import Groq

# 1. ตั้งค่าพื้นฐาน
app = Flask(__name__)
@app.route('/')
def home():
    return "Nike Bot (Dual-Core: Groq + OpenRouter) is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# 🔑 ดึง API Key ของ 2 ค่ายจาก Environment
# ==========================================
GROQ_KEY = os.environ.get('GROQ_API_KEY')
OR_KEY = os.environ.get('OPENROUTER_API_KEY')

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

# 🕒 ระบบเล่นเสียงใบ้ล็อคชั่วโมงดิสคอร์ด
def play_silent_loop(vc):
    if not vc.is_playing():
        source = discord.FFmpegPCMAudio(
            "an_input_that_does_not_exist", 
            before_options="-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000"
        )
        vc.play(source, after=lambda e: bot.loop.create_task(check_and_loop_voice(vc)))

async def check_and_loop_voice(vc):
    await asyncio.sleep(1)
    if vc.is_connected():
        play_silent_loop(vc)

@tasks.loop(minutes=1)
async def keep_voice_alive():
    for vc in bot.voice_clients:
        if vc and vc.is_connected() and not vc.is_playing():
            try:
                play_silent_loop(vc)
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
                    raise Exception("400: No Groq Client") # ฝืนให้เข้า except ถ้าไม่มีคีย์
                    
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_payload 
                )
                response_text = completion.choices[0].message.content
                print("✅ ตอบด้วยสมอง: Groq")

            except Exception as e:
                error_msg = str(e)
                # เช็กว่า Groq พังเพราะ Rate Limit (429) หรือคีย์โดนแบน (400)
                if "429" in error_msg or "400" in error_msg or "Rate limit" in error_msg:
                    print(f"⚠️ Groq ช็อต ({error_msg[:15]})! สลับไปใช้ OpenRouter แทน...")
                    
                    if OR_KEY:
                        # 🧠 แผน B: ใช้ OpenRouter (ตัวสำรอง)
                        try:
                            headers = {
                                "Authorization": f"Bearer {OR_KEY}",
                            }
                            # เลือกใช้ Llama 3 แบบฟรีของ OpenRouter
                            data = {
                                "model": "meta-llama/llama-3-8b-instruct:free",
                                "messages": messages_payload
                            }
                            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                            or_data = response.json()
                            
                            response_text = or_data['choices'][0]['message']['content']
                            print("✅ ตอบด้วยสมอง: OpenRouter (สำรอง)")
                            
                        except Exception as or_e:
                            await message.channel.send("หนูคะ... ตอนนี้พี่ติดเคลียร์งานสโมฯ แป๊บนึงนะครับ จารย์เรียกทั้งภาคเลย รอพี่สักครู่นะคะ 🐍")
                            history.pop() # ลบข้อความที่พังออก
                            return
                    else:
                        await message.channel.send("หนูคะ... ตอนนี้พี่แชทค้างไปหมดแล้ว ขอพี่เคลียร์แป๊บนะคะ 🐍")
                        history.pop()
                        return
                else:
                    await message.channel.send(f"หนูคะ พี่ว่าระบบรวนนิดหน่อยครับ... (Error: {error_msg[:30]}) 🐍")
                    history.pop()
                    return

            # ถ้าได้คำตอบมา (ไม่ว่าจะจาก Groq หรือ OpenRouter) ให้ส่งกลับไป
            if response_text:
                history.append({"role": "assistant", "content": response_text})
                user_stats[user_id] = "กำลังหลอกล่อด้วยความแสนดี" if "ดี" in response_text else "เริ่มหวั่นไหว..."
                await message.channel.send(response_text[:1950])

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get('DISCORD_TOKEN'))
