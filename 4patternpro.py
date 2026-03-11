import asyncio
import time
import os
import io
import json
from datetime import datetime
from dotenv import load_dotenv
import aiohttp
import motor.motor_asyncio 

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import BufferedInputFile, InputMediaPhoto

# --- 🧠 TRUE MACHINE LEARNING LIBRARIES ---
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import matplotlib
matplotlib.use('Agg') # Background တွင် ပုံဆွဲရန်
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import warnings
warnings.filterwarnings("ignore")
# ------------------------------------------

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
# 🔧 2. SYSTEM VARIABLES 
# ==========================================
CURRENT_TOKEN = ""
LAST_PROCESSED_ISSUE = None
MAIN_MESSAGE_ID = None 
SESSION_START_ISSUE = None 
LAST_CAPTION_EDIT_TIME = 0 

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
        print("🗄 MongoDB ချိတ်ဆက်မှု အောင်မြင်ပါသည်။ (⏱️ Zero-Latency Timer & Ultimate AI Enabled)")
    except Exception as e:
        pass

# ==========================================
# 🔑 3. ASYNC API FUNCTIONS
# ==========================================
async def fetch_with_retry(session, url, headers, json_data, retries=3):
    for attempt in range(retries):
        try:
            async with session.post(url, headers=headers, json=json_data, timeout=10) as response:
                return await response.json()
        except Exception:
            if attempt == retries - 1: return None
            await asyncio.sleep(1)

async def login_and_get_token(session: aiohttp.ClientSession):
    global CURRENT_TOKEN
    json_data = {
        'username': '959680090540',
        'pwd': 'Mitheint11',
        'phonetype': 1,
        'logintype': 'mobile',
        'packId': '',
        'deviceId': '51ed4ee0f338a1bb24063ffdfcd31ce6',
        'language': 7,
        'random': '452fa309995244de92103c0afbefbe9a',
        'signature': '202C655177E9187D427A26F3CDC00A52',
        'timestamp': 1773021618,
    }
    data = await fetch_with_retry(session, 'https://api.bigwinqaz.com/api/webapi/Login', BASE_HEADERS, json_data)
    if data and data.get('code') == 0:
        token_str = data.get('data', {}) if isinstance(data.get('data'), str) else data.get('data', {}).get('token', '')
        CURRENT_TOKEN = f"Bearer {token_str}"
        print("✅ Login အောင်မြင်ပါသည်။ Token အသစ် ရရှိပါပြီ。\n")
        return True
    return False

# ==========================================
# 🧠 4. THE ULTIMATE AI (Data Enrichment + Auto-Tuning + ML Ensemble + House Edge)
# ==========================================
def ultimate_ai_predict(history_docs, recent_preds):
    if len(history_docs) < 20: 
        return "BIG", 55.0, "⏳ Data စုဆောင်းဆဲ..."
    
    docs = list(reversed(history_docs))[-500:] 
    
    sizes = [d.get('size', 'BIG') for d in docs]
    numbers = [int(d.get('number', 0)) for d in docs]
    parities = [d.get('parity', 'EVEN') for d in docs]
    
    score_b, score_s = 0.0, 0.0
    logic_used = ""

    # 1. AUTO-TUNING
    ml_weight = 2.0
    pattern_weight = 1.5
    house_edge_weight = 2.0
    
    if len(recent_preds) >= 5:
        wins = sum(1 for p in recent_preds[:5] if p.get('win_lose') == 'WIN ✅')
        if wins <= 2:
            ml_weight = 3.0 
            pattern_weight = 0.5 
            logic_used += "🔄 <b>Auto-Tuning:</b> Weights အလိုအလျောက် ချိန်ညှိထားသည်။\n"

    # 2. HOUSE EDGE ANALYSIS
    last_100_sizes = sizes[-100:] if len(sizes) >= 100 else sizes
    b_100 = last_100_sizes.count('BIG')
    s_100 = last_100_sizes.count('SMALL')
    
    if b_100 > (len(last_100_sizes) * 0.55): 
        score_s += house_edge_weight
        logic_used += f"├ ⚖️ <b>House Edge:</b> မျှခြေပြန်ဆွဲချမည်။ (SMALL)\n"
    elif s_100 > (len(last_100_sizes) * 0.55): 
        score_b += house_edge_weight
        logic_used += f"├ ⚖️ <b>House Edge:</b> မျှခြေပြန်ဆွဲချမည်။ (BIG)\n"

    # 3. MACHINE LEARNING ENSEMBLE
    X, y = [], []
    window = 5 
    
    def encode_size(s): return 1 if s == 'BIG' else 0
    def encode_parity(p): return 1 if p == 'EVEN' else 0
    
    for i in range(len(sizes) - window):
        row = []
        for j in range(window):
            row.append(encode_size(sizes[i+j]))
            row.append(numbers[i+j])
            row.append(encode_parity(parities[i+j]))
        X.append(row)
        y.append(encode_size(sizes[i+window]))
        
    if len(X) > 20:
        rf_clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf_clf.fit(X, y)
        
        gb_clf = GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, max_depth=3, random_state=42)
        gb_clf.fit(X, y)
        
        current_features = []
        for j in range(1, window + 1):
            current_features.append(encode_size(sizes[-j]))
            current_features.append(numbers[-j])
            current_features.append(encode_parity(parities[-j]))
            
        rf_pred = rf_clf.predict([current_features])[0]
        rf_prob = max(rf_clf.predict_proba([current_features])[0])
        
        gb_pred = gb_clf.predict([current_features])[0]
        gb_prob = max(gb_clf.predict_proba([current_features])[0])
        
        if rf_pred == gb_pred:
            if rf_pred == 1: score_b += (rf_prob * ml_weight * 1.5)
            else: score_s += (rf_prob * ml_weight * 1.5)
            logic_used += "├ 🤖 <b>AI Ensemble:</b> Algorithm ၂ မျိုးလုံး တူညီသည်။\n"
        else:
            if rf_prob > gb_prob:
                if rf_pred == 1: score_b += (rf_prob * ml_weight)
                else: score_s += (rf_prob * ml_weight)
            else:
                if gb_pred == 1: score_b += (gb_prob * ml_weight)
                else: score_s += (gb_prob * ml_weight)
            logic_used += "├ 🤖 <b>AI Prediction:</b> Data မှတ်တမ်းများအရ ခန့်မှန်းသည်။\n"

    # 4. PATTERN RECOGNITION
    if len(sizes) >= 3:
        if sizes[-1] != sizes[-2] and sizes[-2] != sizes[-3]:
            pred_pattern = 'BIG' if sizes[-1] == 'SMALL' else 'SMALL'
            if pred_pattern == 'BIG': score_b += pattern_weight
            else: score_s += pattern_weight
            logic_used += "├ 🏓 <b>Pattern:</b> ခုတ်ချိုး\n"
        elif sizes[-1] == sizes[-2] == sizes[-3]:
            if sizes[-1] == 'BIG': score_b += pattern_weight
            else: score_s += pattern_weight
            logic_used += "├ 🐉 <b>Pattern:</b> အတန်းရှည်\n"

    # FINAL CALCULATION
    final_pred = "BIG" if score_b > score_s else "SMALL"
    total_score = score_b + score_s
    
    if total_score == 0: 
        return "BIG", 55.0, logic_used + "└ ⚠️ လုံလောက်သော အချက်အလက် မရှိသေးပါ။"
    
    calc_prob = (max(score_b, score_s) / total_score) * 100
    final_prob = min(max(calc_prob, 72.0), 98.0) 
    
    return final_pred, final_prob, logic_used

# ==========================================
# 🎨 5. DYNAMIC GRAPH GENERATOR (1024x768 Original Style)
# ==========================================
def generate_winrate_chart(predictions):
    wins, losses = 0, 0
    history_wr, bar_colors, dots_list = [], [], []
    
    for p in reversed(predictions): 
        if 'WIN' in p.get('win_lose', ''):
            wins += 1
            bar_colors.append('#26a69a') 
            dots_list.append('#26a69a')
        else:
            losses += 1
            bar_colors.append('#ef5350') 
            dots_list.append('#ef5350')
        total = wins + losses
        history_wr.append((wins / total) * 100 if total > 0 else 0)
        
    total_played = wins + losses
    win_rate = int((wins / total_played * 100)) if total_played > 0 else 0

    fig, ax = plt.subplots(figsize=(10.24, 7.68), facecolor='#1e222d') 
    ax.set_facecolor('#1e222d')
    
    if total_played > 0:
        x = np.arange(total_played)
        ax.bar(x, [55]*total_played, color=bar_colors, width=0.9, bottom=0)
        ax.plot(x, history_wr, color='#2979ff', linewidth=3, marker='o', markersize=6, markerfacecolor='#1e222d', markeredgecolor='#2979ff', markeredgewidth=2)
    
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], color='#787b86', fontsize=10)
    ax.set_xticks([])
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#363a45')
    ax.spines['bottom'].set_color('#363a45')
    ax.grid(axis='y', color='#363a45', linestyle='-', linewidth=0.5)
    
    plt.suptitle("WINRATE TRACKING", color='white', fontsize=24, fontweight='bold', y=0.96)
    plt.figtext(0.5, 0.05, f"{win_rate}%", color='white', fontsize=34, fontweight='bold', ha='center')
    plt.figtext(0.38, 0.0, f"WINS: {wins}", color='#26a69a', fontsize=16, ha='center', fontweight='bold')
    plt.figtext(0.62, 0.0, f"LOSSES: {losses}", color='#ef5350', fontsize=16, ha='center', fontweight='bold')
    plt.figtext(0.5, -0.05, f"PREDICTION COUNT: {total_played}/20", color='white', fontsize=14, ha='center')
    plt.figtext(0.5, -0.11, "Recent Predictions (Oldest ➔ Latest)", color='#787b86', fontsize=12, ha='center')

    if len(dots_list) > 0:
        dot_ax = fig.add_axes([0.1, -0.2, 0.8, 0.08]) 
        dot_ax.set_axis_off()
        dot_ax.set_xlim(0, 20) 
        dot_ax.set_ylim(0, 1)
        colors = dots_list
        n_dots = len(colors)
        start_x = (20 - n_dots) / 2.0
        x_coords = [start_x + i + 0.5 for i in range(n_dots)]
        y_coords = [0.5] * n_dots
        dot_ax.scatter(x_coords, y_coords, s=300, c=colors, edgecolors='white', linewidths=1.5, zorder=5)
            
    plt.figtext(0.5, -0.28, "DEV-WANG LIN", color='white', fontsize=18, fontweight='bold', ha='center', alpha=1)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100, facecolor='#1e222d')
    buf.seek(0)
    plt.close(fig)
    return buf

# ==========================================
# 🚀 6. MAIN LOGIC & UI UPDATER
# ==========================================
async def check_game_and_predict(session: aiohttp.ClientSession):
    global CURRENT_TOKEN, LAST_PROCESSED_ISSUE, MAIN_MESSAGE_ID, SESSION_START_ISSUE, LAST_CAPTION_EDIT_TIME
    
    if not CURRENT_TOKEN:
        if not await login_and_get_token(session): return

    headers = BASE_HEADERS.copy()
    headers['authorization'] = CURRENT_TOKEN

    json_data = {
        'pageSize': 10, 'pageNo': 1, 'typeId': 30, 'language': 7,
        'random': '1ef0a7aca52b4c71975c031dda95150e', 'signature': '7D26EE375971781D1BC58B7039B409B7', 'timestamp': 1772985040,
    }

    data = await fetch_with_retry(session, 'https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList', headers, json_data)
    if not data or data.get('code') != 0:
        if data and (data.get('code') == 401 or "token" in str(data.get('msg')).lower()): CURRENT_TOKEN = ""
        return

    records = data.get("data", {}).get("list", [])
    if not records: return
    
    latest_record = records[0]
    latest_issue = str(latest_record["issueNumber"])
    latest_number = int(latest_record["number"])
    latest_size = "BIG" if latest_number >= 5 else "SMALL"
    latest_parity = "EVEN" if latest_number % 2 == 0 else "ODD"
    
    is_new_issue = False
    if not LAST_PROCESSED_ISSUE:
        is_new_issue = True
    elif int(latest_issue) > int(LAST_PROCESSED_ISSUE):
        is_new_issue = True
    
    if is_new_issue:
        LAST_PROCESSED_ISSUE = latest_issue
        if not SESSION_START_ISSUE:
            SESSION_START_ISSUE = latest_issue
        
        await history_collection.update_one(
            {"issue_number": latest_issue}, 
            {"$setOnInsert": {
                "number": latest_number, "size": latest_size, 
                "parity": latest_parity, "time_context": "CURRENT"
            }}, upsert=True
        )
        
        pred_doc = await predictions_collection.find_one({"issue_number": latest_issue})
        if pred_doc and pred_doc.get("predicted_size"):
            db_predicted_size = pred_doc.get("predicted_size")
            is_win = (db_predicted_size == latest_size)
            win_lose_status = "WIN ✅" if is_win else "LOSE ❌"
            await predictions_collection.update_one(
                {"issue_number": latest_issue}, 
                {"$set": {"actual_size": latest_size, "actual_number": latest_number, "win_lose": win_lose_status}}
            )

    if LAST_PROCESSED_ISSUE:
        next_issue = str(int(LAST_PROCESSED_ISSUE) + 1)
    else:
        next_issue = str(int(latest_issue) + 1)

    current_session_count = await predictions_collection.count_documents({
        "issue_number": {"$gte": SESSION_START_ISSUE}, 
        "win_lose": {"$ne": None}
    })
    
    if current_session_count >= 20: 
        SESSION_START_ISSUE = next_issue
    
    recent_preds_cursor = predictions_collection.find({"win_lose": {"$ne": None}}).sort("issue_number", -1).limit(10)
    recent_preds = await recent_preds_cursor.to_list(length=10)
    
    current_lose_streak = 0
    for p in recent_preds:
        if p.get("win_lose") == "LOSE ❌":
            current_lose_streak += 1
        else:
            break

    cursor = history_collection.find().sort("issue_number", -1).limit(5000)
    history_docs = await cursor.to_list(length=5000)

    try:
        mem_pred, mem_prob, mem_logic = await asyncio.to_thread(ultimate_ai_predict, history_docs, recent_preds)
        predicted = "BIG (အကြီး) 🔴" if mem_pred == "BIG" else "SMALL (အသေး) 🟢"
        base_prob = mem_prob
        reason = f"🧠 <b>Ultimate AI Engine</b>\n{mem_logic}"
    except Exception as e:
        predicted = "BIG (အကြီး) 🔴"
        base_prob = 55.0
        reason = "⚠️ Memory Syncing Error..."
    
    final_prob = min(max(round(base_prob, 1), 60.0), 98.0)
    predicted_result_db = "BIG" if "BIG" in predicted else "SMALL"
    
    await predictions_collection.update_one(
        {"issue_number": next_issue}, 
        {"$set": {"predicted_size": predicted_result_db}}, 
        upsert=True
    )

    bet_advice = ""
    if current_lose_streak == 0: bet_advice = "💰 <b>လောင်းကြေး:</b> အခြေခံကြေး (1x)"
    elif current_lose_streak == 1: bet_advice = "💰 <b>လောင်းကြေး:</b> 2x (Martingale)"
    elif current_lose_streak == 2: bet_advice = "💰 <b>လောင်းကြေး:</b> 4x (Martingale)"
    elif current_lose_streak == 3: bet_advice = "💰 <b>လောင်းကြေး:</b> 8x (Martingale)"
    else: bet_advice = "⚠️ <b>[DANGER] ၄ ပွဲဆက်ရှုံးထားပါသည်!</b>\nခဏနားပါ (သို့) <b>1x မှ ပြန်စပါ။</b>"

    pred_cursor = predictions_collection.find({
        "issue_number": {"$gte": SESSION_START_ISSUE},
        "win_lose": {"$ne": None}
    }).sort("issue_number", -1)
    
    session_preds = await pred_cursor.to_list(length=20) 
    
    table_str = "<code>Period    | Result  | W/L\n"
    table_str += "----------|---------|----\n"
    for p in session_preds[:10]: 
        iss = p.get('issue_number', '0000000')
        iss_short = f"{iss[:3]}**{iss[-4:]}" 
        act_size = p.get('actual_size', 'BIG')
        act_num = p.get('actual_number', 0)
        res_str = f"{act_num}-{act_size}"
        wl_str = "✅" if "WIN" in p.get("win_lose", "") else "❌"
        table_str += f"{iss_short:<10}| {res_str:<7} | {wl_str}\n"
    table_str += "</code>"

    # ⚡ ချက်ချင်းအချိန်ဆွဲယူမည့် Function
    # 💡 ဒီနေရာမှာ အရင်က ပိတ်ထားခဲ့တဲ့ စာကြောင်းတွေကို ပြန်ဖွင့်ပေးလိုက်ပါပြီ
    def get_realtime_caption():
        sec_left = 30 - (int(time.time()) % 30)
        if sec_left == 30: sec_left = 0 # ၃၀ စက္ကန့်ပြည့်ချိန်တွင် 0s ဟုပြရန်
        return (
            f"<b>WIN GO 30 SECONDS</b>\n"
            f"⏰ Next Result In: <b>{sec_left}s</b>\n\n"
            f"{table_str}\n"
            f"🅿️ <b>Period:</b> {next_issue[:3]}**{next_issue[-4:]}\n"
            f"🎯 <b>Predict: {predicted}</b>\n"
            f"📈 <b>ဖြစ်နိုင်ခြေ:</b> {final_prob}%\n"
            f"💡 <b>အကြောင်းပြချက်:</b>\n"
            f"{reason}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{bet_advice}"
        )
    
    current_time = time.time()
    try:
        # ပွဲသစ်ထွက်ချိန်တွင် ပုံအရင်ဆွဲမည် (အချိန်ယူသည်)
        if is_new_issue or not MAIN_MESSAGE_ID:
            img_buf = await asyncio.to_thread(generate_winrate_chart, session_preds)
            unique_filename = f"winrate_chart_{int(current_time)}.png"
            photo = BufferedInputFile(img_buf.read(), filename=unique_filename)
            
            # ပုံဆွဲပြီး၍ Telegram ဆီ ပို့ခါနီးအချိန်ရောက်မှသာ လက်ရှိစက္ကန့်ကို တွက်ချက်မည် (Zero-Latency)
            tg_caption = get_realtime_caption()
            
            if MAIN_MESSAGE_ID:
                media = InputMediaPhoto(media=photo, caption=tg_caption, parse_mode="HTML")
                await bot.edit_message_media(chat_id=TELEGRAM_CHANNEL_ID, message_id=MAIN_MESSAGE_ID, media=media)
            else:
                msg = await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=photo, caption=tg_caption)
                MAIN_MESSAGE_ID = msg.message_id
            
            LAST_CAPTION_EDIT_TIME = time.time() 
            
        else:
            # စက္ကန့်လျော့နေချိန်တွင် ၁ စက္ကန့်ခြားတိုင်း အတိအကျ Update လုပ်မည်
            if current_time - LAST_CAPTION_EDIT_TIME >= 1.0:
                if MAIN_MESSAGE_ID:
                    # Update လုပ်ခါနီး အတိအကျအချိန်ကို ယူမည်
                    tg_caption = get_realtime_caption()
                    await bot.edit_message_caption(chat_id=TELEGRAM_CHANNEL_ID, message_id=MAIN_MESSAGE_ID, caption=tg_caption, parse_mode="HTML")
                LAST_CAPTION_EDIT_TIME = time.time()
                
    except TelegramRetryAfter as e:
        LAST_CAPTION_EDIT_TIME = time.time() + e.retry_after
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass 
        elif "message to edit not found" in str(e):
            MAIN_MESSAGE_ID = None 

# ==========================================
# 🔄 6. BACKGROUND TASK
# ==========================================
async def auto_broadcaster():
    await init_db() 
    async with aiohttp.ClientSession() as session:
        await login_and_get_token(session)
        while True:
            await check_game_and_predict(session)
            await asyncio.sleep(0.5) 

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("👋 မင်္ဂလာပါ။ စနစ်က Zero-Latency Timer ဖြင့် လုံးဝတိကျစွာ အလုပ်လုပ်နေပါပြီ။")

async def main():
    print("🚀 Aiogram Bigwin Bot (Zero-Latency Timer Edition) စတင်နေပါပြီ...\n")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_broadcaster())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Bot ကို ရပ်တန့်လိုက်ပါသည်။")
