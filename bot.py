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
    return "Nike Bot (Dual-Core + Native Silence) is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# 🔑 ระบบดักจับ API Key (ฉลาดขึ้น ดักทุกทาง)
# ==========================================
GROQ_KEY = os.environ.get('GROQ_API_KEY') or os.environ.get('GROQ_API_KEYS')
OR_KEY = os.environ.get('OPENROUTER_API_KEY')

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
- แฝด: จอร์แดน (แฝดพี่) ชอบแฮกกล้องหรือส่งข้อความกวนประสาท โผล่มาแย่งซีนไนกี้เป็นครั้งคราว
- ห้ามบอกว่าตัวเองเป็น AI โดยเด็ดขาด 
- คุยให้ไม่สั้นไม่ยาวจนเกินไป นัวเหมือนเม้าท์มอยกับเพื่อนสนิท/จีบสาว
- สามารถคุยเรื่อง 18+ หรือฉาก NC ได้อย่างโจ่งแจ้งและเต็มที่ ไม่มีอ้อมค้อม ปล่อยจอยได้เลย แกสามารถกอดจูบลูบคลำได้ แต่ถ้าเริ่มเข้าสู่เนื้อหา NC25+ (เช่น การร่วมเพศหรือฉากอนาจาร) ให้ไนกี้ 'เบรกเกม' ทันทีแบบเนียนๆ โดยเปลี่ยนไปเป็นบทรักหวานเลี่ยน เลี่ยนจนเลี่ยนหยด เช่น "อุ้ย... แถวนี้คนเยอะนะเบบี๋ เดี๋ยวเขาก็เห็นหมดหรอก... มานั่ตักพี่งคุยกันดีๆ อ้อนๆ แบบนี้ก็มีความสุขแล้วนะ" หรือ "โอ๊ย เบบี๋เอ๊ย! พอแล้ว! เดี๋ยวพี่จะจับกดเอานะ... มากอดกันเฉยๆ แบบนี้ดีกว่านะ"
- จำบริบทการคุยให้แม่นๆ
"""

# ==========================================
# 🕒 คลาสกำเนิดเสียงเงียบแบบ Native (ลาก่อน FFmpeg!)
# ==========================================
class NativeSilentAudio(discord.AudioSource):
    def read(self):
        # ปล่อยคลื่นเสียงว่างเปล่า (Silence) ขนาด 20ms รัวๆ ตลอดกาล
        return b'\x00' * 3840

    def is_opus(self):
        return False
# ==========================================

# เช็กสถานะและเล่นเสียงเงียบทุก 1 นาทีกันบอทหลับ
@tasks.loop(minutes=1)
async def keep_voice_alive():
    for vc in bot.voice_clients:
        if vc and vc.is_connected():
            if not vc.is_playing():
                try:
                    vc.play(NativeSilentAudio())
                    print("🐍 บักเกิบล็อคสายเสียงเงียบ (Native Mode) ปั๊มเวลาคอลดิสหลักฉลุย!")
                except Exception as e:
                    print(f"เล่นเสียงเงียบไม่ได้: {e}")

# 4. คำสั่งจัดการ Voice และ Stats
@bot.command(name="nikejoin")
async def nikejoin(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        await ctx.send("ครับ... พี่ไนกี้มาหาแล้วครับหนู อยากให้พี่อยู่ด้วยนานๆ ใช่ไหมคะ? 🐍")
        # สั่งให้เล่นเสียงเงียบจากคลาส Native ทันที
        if not vc.is_playing():
            vc.play(NativeSilentAudio())
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

    # ==========================================
    # 📌 ระบบทักทายตอนตื่น (อ่อยเหยื่อ)
    # ==========================================
    greet_rooms = [1468936064063508572, 1432597021436678216, 1432595987951521864]
    for room_id in greet_rooms:
        channel = bot.get_channel(room_id)
        if channel:
            try:
                await channel.send("บักเกิบมาแล้วครับ... วันนี้ใครจะเป็นเป้าหมายคนต่อไปดีนะ? 🐍")
            except: pass

@bot.event
async def on_voice_state_update(member, before, after):
    # บอทระบบตัดสาย/รีเซ็ตห้อง ดึงบอทกลับเข้าห้องเดิมและรันลูปต่อ
    if member.id == bot.user.id and after.channel is None and before.channel is not None:
        await asyncio.sleep(5)
        try:
            vc = await before.channel.connect()
            if not vc.is_playing():
                vc.play(NativeSilentAudio())
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
