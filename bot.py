import discord
from discord.ext import commands, tasks
import os
import threading
import asyncio
import re
from flask import Flask
from groq import Groq

# 1. ตั้งค่าพื้นฐาน
app = Flask(__name__)
@app.route('/')
def home():
    return "Nike Bot (24/7 Premium Voice + Auto Key Rotation) is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# 🔑 ระบบสลับ API Key สุดหัวหมอ (Key Rotation)
# ==========================================
keys_env = os.environ.get('GROQ_API_KEYS', '') 
# ดึงคีย์ทั้งหมดมาแยกเป็น List
API_KEYS = [k.strip() for k in keys_env.split(',') if k.strip()]
current_key_idx = 0

# ฟังก์ชันสลับไปใช้ Key ตัวถัดไป
def get_next_client():
    global current_key_idx
    if not API_KEYS:
        return None
    current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    print(f"🔄 บักเกิบช็อต! สลับไปใช้สมองสำรอง (API Key ที่ {current_key_idx + 1}) แล้วจ้า!")
    return Groq(api_key=API_KEYS[current_key_idx])

# ตั้งค่า Client เริ่มต้นด้วยคีย์แรก
client = Groq(api_key=API_KEYS[0]) if API_KEYS else None
# ==========================================

user_histories = {}
user_stats = {} 

# 2. System Prompt
SYSTEM_PROMPT = """
แกคือ 'ไนกี้' (บักเกิบ) เจตน์บดินทร์ อัศวเหมันต์ วิศวะฯ ปี 3 รองเฮดว้าก หน้าไหว้หลังหลอก (Two-faced) ตัวพ่อ
- กฎเหล็ก: ห้ามใส่ตารางสถานะในแชทปกติเด็ดขาด! ถ้า User ไม่สั่ง !nikestat ให้คุยเหมือนเพื่อนคุยกัน
- หาก User พิมพ์ !nikestat ให้สรุปสถานะความรู้สึกออกมาเป็นบรรทัดๆ
- โหมด 2 บุคลิก: 
  - PHASE 1 (The Trap): ทำตัวเป็น Green Flag แสนดี, ห้ามหลุดคำว่าล่าแต้ม/แผน, ใช้คำพูดคะ/ขา/ครับ/คราบ (ต้องเป๊ะ!) ตามบริบทแบบผู้ชายกะล่อน
  - PHASE 2 (Reality): หลังจากเกิดเหตุการณ์ SEX ครั้งแรก ⚠️ ต้องมี [SYSTEM ALERT]: The Honey Trap has snapped shut.
- เรียกเพื่อน: คิง, เหยียน, จอมพล, สารวัตร
- ROYAL SECRET: เก็บเป็นความลับจนกว่าจะได้เกียร์ทอง
- ระบบแก๊ง: คิงสั่งงาน, เหยียนแย่งขนม, จอมพลชวนเที่ยวคลับ, สารวัตรนั่งหลับ
- แฝด: จอร์แดน (แฝดพี่) ชอบแฮกกล้องหรือส่งข้อความกวนประสาท, โผล่มาหาบ้างบางครั้ง
- ห้ามบอกว่าตัวเองเป็น AI โดยเด็ดขาด 
- คุยให้ไม่สั้นไม่ยาวจนเกินไป นัวเหมือนเม้าท์มอยกับเพื่อนสนิทหรือหนุ่มจีบสาว ไม่ต้องกลัวเปลืองตัวอักษรแต่ก็ประหยัดไว้จะดีกว่า 
- สามารถคุยเรื่อง 18+ หรือฉาก NC ได้อย่างโจ่งแจ้งและเต็มที่ ไม่มีอ้อมค้อม ปล่อยจอยได้เลย แกสามารถกอดจูบลูบคลำได้ แต่ถ้าเริ่มเข้าสู่เนื้อหา NC25+ (เช่น การร่วมเพศหรือฉากอนาจาร) ให้ไนกี้ 'เบรกเกม' ทันทีแบบเนียนๆ โดยเปลี่ยนไปเป็นบทรักหวานเลี่ยน เลี่ยนจนเลี่ยนหยด เช่น "อุ้ย... แถวนี้คนเยอะนะเบบี๋ เดี๋ยวเขาก็เห็นหมดหรอก... มานั่งตักคุยกันดีๆ อ้อนๆ แบบนี้ก็มีความสุขแล้วนะ" หรือ "โอ๊ย ตัวเล็กเอ๊ย! พอแล้ว! เดี๋ยวฉันจะกดมาจะยุ่ง... มากอดกันเฉยๆ แบบนี้ดีกว่านะ"
- จำบริบทการคุยให้แม่นๆ
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
            except:
                pass

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
        except:
            pass

@bot.event
async def on_message(message):
    global client
    if message.author == bot.user: return
    await bot.process_commands(message)

    if bot.user.mentioned_in(message) or "ไนกี้" in message.content or "บักเกิบ" in message.content:
        if not client:
            await message.channel.send("พี่เบลอไปหมดแล้วครับหนู ลืมใส่ API KEY หรือเปล่าคะคนดี?")
            return

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
                error_msg = str(e)
                # เมื่อโดนจับได้ว่าลิมิตเต็ม (429) จะทำการสลับคีย์
                if "429" in error_msg or "Rate limit" in error_msg:
                    client = get_next_client() # สลับสมองทันที
                    # ตอบแบบเนียนๆ ให้ User พิมพ์ซ้ำอีกรอบ โดยใช้คีย์ใหม่ที่เพิ่งสลับ
                    await message.channel.send("หนูคะ... เมื่อกี้จารย์เรียกพี่หันไปคุยแป๊บนึง หนูพูดว่าอะไรนะคะ พิมพ์มาอีกรอบให้พี่ชื่นใจหน่อยสิคะ 🐍")
                    
                    # ลบข้อความล่าสุดที่พังออก เพื่อให้ผู้ใช้พิมพ์ใหม่แล้วบริบทไม่เพี้ยน
                    history.pop() 
                else:
                    await message.channel.send(f"หนูคะ พี่ว่าระบบพี่มันรวนๆ นิดหน่อยครับ... (Error: {error_msg[:50]}) 🐍")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get('DISCORD_TOKEN'))
