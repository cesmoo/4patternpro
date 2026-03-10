import asyncio
import time
import os
from dotenv import load_dotenv
import aiohttp
import motor.motor_asyncio 

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv()

# ==========================================
# ⚙️ 1. CONFIGURATION
# ==========================================
USERNAME = os.getenv("BIGWIN_USERNAME")
PASSWORD = os.getenv("BIGWIN_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
MONGO_URI = os.getenv("MONGO_URI") 

if not all([USERNAME, PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, MONGO_URI]):
    print("❌ Error: .env ဖိုင်ထဲတွင် အချက်အလက်များ ပြည့်စုံစွာ မပါဝင်ပါ။")
    exit()
  
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# MongoDB Setup
db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = db_client['bigwin_database'] 
history_collection = db['game_history'] 
predictions_collection = db['predictions'] 

# ==========================================
# 🔧 2. SYSTEM & TRACKING VARIABLES 
# ==========================================
CURRENT_TOKEN = ""
LAST_PROCESSED_ISSUE = ""
LAST_PREDICTED_ISSUE = ""
LAST_PREDICTED_RESULT = ""

# --- Streak & Stats Tracking ---
# (Host Restart လုပ်တိုင်း 0 မှ ပြန်စမည်)
CURRENT_WIN_STREAK = 0
CURRENT_LOSE_STREAK = 0
LONGEST_WIN_STREAK = 0
LONGEST_LOSE_STREAK = 0
TOTAL_PREDICTIONS = 0 

BASE_HEADERS = {
    'authority': 'api.bigwinqaz.com',
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://www.777bigwingame.app',
    'referer': 'https://www.777bigwingame.app/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
}

async def init_db():
    try:
        await history_collection.create_index("issue_number", unique=True)
        await predictions_collection.create_index("issue_number", unique=True)
        print("🗄 MongoDB ချိတ်ဆက်မှု အောင်မြင်ပါသည်။")
    except Exception as e:
        print(f"❌ MongoDB Indexing Error: {e}")

# ==========================================
# 🔑 3. ASYNC API FUNCTIONS
# ==========================================
async def login_and_get_token(session: aiohttp.ClientSession):
    global CURRENT_TOKEN
    print("🔐 အကောင့်ထဲသို့ Login ဝင်နေပါသည်...")
    
    json_data = {
        'username': USERNAME,
        'pwd': PASSWORD,
        'phonetype': 1,
        'logintype': 'mobile',
        'packId': '',
        'deviceId': '51ed4ee0f338a1bb24063ffdfcd31ce6',
        'language': 7,
        'random': 'e9a8246ddf1e4514955ada53ef50bdc0',
        'signature': '872204F85DDA09B5E7BFAFD9FECC402E',
        'timestamp': 1772984986,
    }

    try:
        async with session.post('https://api.bigwinqaz.com/api/webapi/Login', headers=BASE_HEADERS, json=json_data) as response:
            data = await response.json()
            if data.get('code') == 0:
                token_str = data.get('data', {}) if isinstance(data.get('data'), str) else data.get('data', {}).get('token', '')
                CURRENT_TOKEN = f"Bearer {token_str}"
                print("✅ Login အောင်မြင်ပါသည်။ Token အသစ် ရရှိပါပြီ။\n")
                return True
            return False
    except: return False

async def get_user_balance(session: aiohttp.ClientSession):
    global CURRENT_TOKEN
    if not CURRENT_TOKEN: return "0.00"
    headers = BASE_HEADERS.copy()
    headers['authorization'] = CURRENT_TOKEN
    
    json_data = {
        'signature': 'F7A9A2A74E1F1D1DFE048846E49712F8',
        'language': 7,
        'random': '58d9087426f24a54870e243b76743a94',
        'timestamp': 1772984987,
    }
    try:
        async with session.post('https://api.bigwinqaz.com/api/webapi/GetUserInfo', headers=headers, json=json_data) as response:
            data = await response.json()
            if data.get('code') == 0: return data.get('data', {}).get('amount', '0.00')
            return "0.00"
    except: return "0.00"

# ==========================================
# 🧠 4. 🔥 ADVANCED AI ENSEMBLE LOGIC 🔥
# ==========================================
async def check_game_and_predict(session: aiohttp.ClientSession):
    global CURRENT_TOKEN, LAST_PROCESSED_ISSUE, LAST_PREDICTED_ISSUE, LAST_PREDICTED_RESULT
    global CURRENT_WIN_STREAK, CURRENT_LOSE_STREAK, LONGEST_WIN_STREAK, LONGEST_LOSE_STREAK, TOTAL_PREDICTIONS
    
    if not CURRENT_TOKEN:
        if not await login_and_get_token(session): return

    headers = BASE_HEADERS.copy()
    headers['authorization'] = CURRENT_TOKEN

    json_data = {
        'pageSize': 10, 'pageNo': 1, 'typeId': 30, 'language': 7,
        'random': '1ef0a7aca52b4c71975c031dda95150e', 'signature': '7D26EE375971781D1BC58B7039B409B7', 'timestamp': 1772985040,
    }

    try:
        async with session.post('https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList', headers=headers, json=json_data) as response:
            data = await response.json()
            if data.get('code') == 0:
                records = data.get("data", {}).get("list", [])
                if not records: return
                
                latest_record = records[0]
                latest_issue = str(latest_record["issueNumber"])
                latest_number = int(latest_record["number"])
                latest_size = "BIG" if latest_number >= 5 else "SMALL"
                
                if latest_issue == LAST_PROCESSED_ISSUE: return 
                LAST_PROCESSED_ISSUE = latest_issue
                next_issue = str(int(latest_issue) + 1)
                win_lose_text = ""
                
                await history_collection.update_one({"issue_number": latest_issue}, {"$setOnInsert": {"number": latest_number, "size": latest_size}}, upsert=True)
                
                # --- နိုင်/ရှုံး စစ်ဆေးခြင်း နှင့် Streak တွက်ချက်ခြင်း ---
                if LAST_PREDICTED_ISSUE == latest_issue:
                    is_win = (LAST_PREDICTED_RESULT == latest_size)
                    TOTAL_PREDICTIONS += 1
                    
                    if is_win:
                        win_lose_status = "WIN ✅"
                        CURRENT_WIN_STREAK += 1
                        CURRENT_LOSE_STREAK = 0
                        if CURRENT_WIN_STREAK > LONGEST_WIN_STREAK:
                            LONGEST_WIN_STREAK = CURRENT_WIN_STREAK
                    else:
                        win_lose_status = "LOSE ❌"
                        CURRENT_LOSE_STREAK += 1
                        CURRENT_WIN_STREAK = 0
                        if CURRENT_LOSE_STREAK > LONGEST_LOSE_STREAK:
                            LONGEST_LOSE_STREAK = CURRENT_LOSE_STREAK
                            
                    await predictions_collection.update_one({"issue_number": latest_issue}, {"$set": {"actual_size": latest_size, "win_lose": win_lose_status}})
                    
                    win_lose_text = (
                        f"🏆 <b>ပြီးခဲ့သောပွဲစဉ် ({latest_issue})</b> ရလဒ်: {latest_size}\n"
                        f"📊 <b>ခန့်မှန်းချက်: {win_lose_status}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                    )

                # ==============================================================
                # 🧠 NEW AI: Multi-Layer Ensemble Algorithm
                # ==============================================================
                cursor = history_collection.find().sort("issue_number", -1).limit(5000)
                history_docs = await cursor.to_list(length=5000)
                history_docs.reverse()
                all_history = [doc["size"] for doc in history_docs]
                
                predicted = "BIG (အကြီး) 🔴"
                base_prob = 55.0
                reason = "Data အချက်အလက် စုဆောင်းနေဆဲဖြစ်သည်"

                if len(all_history) > 20:
                    big_score = 0.0
                    small_score = 0.0
                    reasons_list = []

                    # ၁။ Weighted Pattern Matching (၃ ပွဲဆက်မှ ၈ ပွဲဆက်အထိ အကုန်တွက်မည်)
                    # ပိုရှည်သော Pattern တူလေ အမှတ်(Score) ပိုရလေ ဖြစ်သည်။
                    weights = {3: 1.0, 4: 1.5, 5: 2.0, 6: 3.0, 7: 4.0, 8: 5.0}
                    
                    for length in range(3, 9):
                        if len(all_history) > length:
                            recent_pattern = all_history[-length:]
                            b_count = 0
                            s_count = 0
                            
                            for i in range(len(all_history) - length):
                                if all_history[i:i+length] == recent_pattern:
                                    next_res = all_history[i+length]
                                    if next_res == 'BIG': b_count += 1
                                    elif next_res == 'SMALL': s_count += 1
                                        
                            total_matches = b_count + s_count
                            if total_matches > 0:
                                big_score += (b_count / total_matches) * weights[length]
                                small_score += (s_count / total_matches) * weights[length]
                                if length >= 6 and total_matches >= 2:
                                    if "Deep Pattern" not in reasons_list:
                                        reasons_list.append("Deep Pattern")

                    # ၂။ Short-Term Momentum (နောက်ဆုံးပွဲ ၂၀ ၏ ရေစီးကြောင်းအားသာချက်)
                    recent_20 = all_history[-20:]
                    b_recent = recent_20.count('BIG')
                    s_recent = recent_20.count('SMALL')
                    big_score += (b_recent / 20.0) * 1.5
                    small_score += (s_recent / 20.0) * 1.5
                    
                    if max(b_recent, s_recent) >= 13:
                        reasons_list.append("Momentum")

                    # ၃။ Streak Breaker (တစ်မျိုးတည်း ဆက်တိုက်ထွက်နေပါက ပြတ်နိုင်ခြေကို တွက်ချက်ခြင်း)
                    current_streak_len = 1
                    last_color = all_history[-1]
                    for i in range(2, 10):
                        if len(all_history) >= i and all_history[-i] == last_color:
                            current_streak_len += 1
                        else:
                            break
                            
                    if current_streak_len >= 5: # ၅ ပွဲထက်ပိုတူနေရင် Break ဖြစ်ဖို့ တွန်းအားပေးမည်
                        reasons_list.append(f"{current_streak_len}-Streak Break")
                        if last_color == 'BIG':
                            small_score += current_streak_len * 0.8
                        else:
                            big_score += current_streak_len * 0.8

                    # ၄။ Final Decision (ရလာသော Score များအားလုံးကို ပေါင်း၍ ဆုံးဖြတ်ခြင်း)
                    total_score = big_score + small_score
                    if total_score > 0:
                        big_prob = (big_score / total_score) * 100
                        small_prob = (small_score / total_score) * 100
                        
                        if big_prob > small_prob:
                            predicted = "BIG (အကြီး) 🔴"
                            base_prob = big_prob
                        else:
                            predicted = "SMALL (အသေး) 🟢"
                            base_prob = small_prob
                            
                        reason_text = " + ".join(reasons_list) if reasons_list else "Trend Analysis"
                        reason = f"🧠 AI Ensemble Logic [{reason_text}]"
                    else:
                        base_prob = 55.0
                        reason = "သမိုင်းကြောင်းအရ တွက်ချက်ထားသည်"

                # ရာခိုင်နှုန်းကို လက်တွေ့ကျစေရန် 55% နှင့် 92% ကြားတွင်သာ ရှိစေမည်
                final_prob = min(max(round(base_prob, 1), 55.0), 92.0)

                LAST_PREDICTED_ISSUE = next_issue
                LAST_PREDICTED_RESULT = "BIG" if "BIG" in predicted else "SMALL"
                
                await predictions_collection.update_one({"issue_number": next_issue}, {"$set": {"predicted_size": LAST_PREDICTED_RESULT, "probability": final_prob, "actual_size": None, "win_lose": None}}, upsert=True)

                print(f"✅ [NEW] ပွဲစဉ်: {next_issue} | Predict: {predicted} | AI Score: {final_prob}%")

                # --- 🎨 TELEGRAM MESSAGE FORMATTING ---
                tg_message = (
                    f"🎰 <b>Bigwin 30-Seconds (AI Predictor)</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"{win_lose_text}"
                    f"🎯 <b>နောက်ပွဲစဉ်အမှတ် :</b>\n"
                    f"<code>{next_issue}</code>\n"
                    f"🤖 <b>AI ခန့်မှန်းချက် : {predicted}</b>\n"
                    f"📈 <b>ဖြစ်နိုင်ခြေ :</b> {final_prob}%\n"
                    f"💡 <b>အကြောင်းပြချက် :</b>\n"
                    f"{reason}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Cᴜʀʀᴇɴᴛ Wɪɴ Sᴛʀᴇᴀᴋ : {CURRENT_WIN_STREAK}\n"
                    f"Cᴜʀʀᴇɴᴛ Lᴏsᴇ Sᴛʀᴇᴀᴋ : {CURRENT_LOSE_STREAK}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Lᴏɴɢᴇsᴛ Wɪɴ Sᴛʀᴇᴀᴋ : {LONGEST_WIN_STREAK}\n"
                    f"Lᴏɴɢᴇsᴛ Lᴏsᴇ Sᴛʀᴇᴀᴋ : {LONGEST_LOSE_STREAK}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Tᴏᴛᴀʟ Pʀᴇᴅɪᴄᴛɪᴏɴs : {TOTAL_PREDICTIONS}"
                )
                
                try: await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=tg_message)
                except: pass
                
            elif data.get('code') == 401 or "token" in str(data.get('msg')).lower():
                CURRENT_TOKEN = ""
    except Exception as e: print(f"❌ Game Data Request Error: {e}")

# ==========================================
# 🔄 5. BACKGROUND TASK & MAIN LOOP
# ==========================================
async def auto_broadcaster():
    await init_db() 
    async with aiohttp.ClientSession() as session:
        await login_and_get_token(session)
        while True:
            await check_game_and_predict(session)
            await asyncio.sleep(5)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("👋 မင်္ဂလာပါ။ Bigwin Advanced AI Predictor Bot မှ ကြိုဆိုပါတယ်။\n\nစနစ်က Channel ထဲကို အလိုအလျောက် Signal တွေ ပို့ပေးနေပါပြီ။")

async def main():
    print("🚀 Aiogram Bigwin Bot (Advanced Ensemble AI) စတင်နေပါပြီ...\n")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_broadcaster())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Bot ကို ရပ်တန့်လိုက်ပါသည်။")
