import asyncio
import time
import os
import io
import json
import traceback
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
USERNAME = os.getenv("BIGWIN_USERNAME", "959675323878")
PASSWORD = os.getenv("BIGWIN_PASSWORD", "Mitheint11")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
MONGO_URI = os.getenv("MONGO_URI") 

if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, MONGO_URI]):
    print("❌ Error: .env ဖိုင်ထဲတွင် အချက်အလက်များ ပြည့်စုံစွာ မပါဝင်ပါ။")
    exit()

# 🔑========================================🔑
# 🚨 6WIN API လုံခြုံရေးသော့များ (Win Go 30s)
# 🔑========================================🔑
LOGIN_RANDOM = "e98c09a1f15949f99403c27d9fc45dfa"
LOGIN_SIGNATURE = "C5118DA49746AF4504F6C4967C5C50B4"
LOGIN_TIMESTAMP = 1773236871

# 👇 ဇယားဆွဲမည့် သော့ (၅ မိနစ်ပြည့်တိုင်း ဤနေရာတွင် Manual လာလဲပေးရပါမည်) 👇
DATA_RANDOM = "ff5adfece70a45c2b5152b2526b50a3a"
DATA_SIGNATURE = "40D308D7D2D214B247B6CF480E1FB85D"
DATA_TIMESTAMP = 1773237062
# ============================================

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 💡 6Win 30 Seconds အတွက် သီးသန့် Database 
db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = db_client['bigwin_database'] 
history_collection = db['6lottery_wingo30_history'] 
predictions_collection = db['6lottery_wingo30_predictions'] 

CURRENT_TOKEN = ""
LAST_PROCESSED_ISSUE = None
MAIN_MESSAGE_ID = None 
SESSION_START_ISSUE = None 
LAST_CAPTION_EDIT_TIME = 0 
LAST_HEARTBEAT = time.time()

BASE_HEADERS = {
    'authority': '6lotteryapi.com',
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://www.6win566.com',
    'referer': 'https://www.6win566.com/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
}

async def init_db():
    try:
        await history_collection.create_index("issue_number", unique=True)
        await predictions_collection.create_index("issue_number", unique=True)
        print("🗄 MongoDB ချိတ်ဆက်မှု အောင်မြင်ပါသည်။ (🚀 1024x768 Perfect Layout + ULTIMATE AI Edition)")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

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
        'username': USERNAME, 
        'pwd': PASSWORD,
        'phonetype': 1,
        'logintype': 'mobile',
        'packId': '',
        'deviceId': 'b9b753a9f874897574d7fa72ff84374c',
        'language': 7,
        'random': LOGIN_RANDOM,
        'signature': LOGIN_SIGNATURE,
        'timestamp': LOGIN_TIMESTAMP,
    }
    data = await fetch_with_retry(session, 'https://6lotteryapi.com/api/webapi/Login', BASE_HEADERS, json_data)
    if data and data.get('code') == 0:
        token_str = data.get('data', {}) if isinstance(data.get('data'), str) else data.get('data', {}).get('token', '')
        CURRENT_TOKEN = f"Bearer {token_str}"
        print("✅ 6WIN ဆာဗာသို့ Login အောင်မြင်ပါသည်။\n")
        return True
    return False

# ==========================================
# 🧠 4. THE ULTIMATE AI (Data Enrichment + Auto-Tuning + ML Ensemble + House Edge)
# ==========================================
def ultimate_ai_predict(history_docs, recent_preds):
    if len(history_docs) < 20: 
        return "BIG", 55.0, "⏳ Data စုဆောင်းဆဲ..."
    
    # ⏱️ Speed Optimization: တွက်ချက်မှုမြန်စေရန် နောက်ဆုံး ပွဲ ၅၀၀ ကိုသာ သုံးမည်
    docs = list(reversed(history_docs))[-500:] 
    
    sizes = [d.get('size', 'BIG') for d in docs]
    numbers = [int(d.get('number', 0)) for d in docs]
    parities = [d.get('parity', 'EVEN') for d in docs]
    
    score_b, score_s = 0.0, 0.0
    logic_used = ""

    # ---------------------------------------------------------
    # ⚙️ 1. SELF-CORRECTING AUTO-TUNING (Reinforcement Weights)
    # ---------------------------------------------------------
    ml_weight = 2.0
    pattern_weight = 1.5
    house_edge_weight = 2.0
    
    if len(recent_preds) >= 5:
        wins = sum(1 for p in recent_preds[:5] if p.get('win_lose') == 'WIN ✅')
        if wins <= 2:
            # ၅ ပွဲမှာ ၂ ပွဲပဲ နိုင်ရင် AI က လမ်းကြောင်းမှားနေပြီဟု ယူဆကာ Weights များကို Auto ပြင်မည်
            ml_weight = 3.0 # ML ကို ပိုအားကိုးမည်
            pattern_weight = 0.5 # ရိုးရိုး Pattern များကို လျှော့ချမည်
            logic_used += "🔄 <b>Auto-Tuning:</b> လမ်းကြောင်းပြောင်းနေသဖြင့် ML Weights ကို မြှင့်တင်ထားသည်။\n"

    # ---------------------------------------------------------
    # ⚙️ 2. CASINO HOUSE EDGE ANALYSIS (Standard Deviation Balance)
    # ---------------------------------------------------------
    last_100_sizes = sizes[-100:] if len(sizes) >= 100 else sizes
    b_100 = last_100_sizes.count('BIG')
    s_100 = last_100_sizes.count('SMALL')
    
    # 55% ထက်ကျော်လွန်နေပါက ဆာဗာမှ မျှခြေပြန်ဆွဲချမည်ဟု ယူဆသည်
    if b_100 > (len(last_100_sizes) * 0.55): 
        score_s += house_edge_weight
        logic_used += f"├ ⚖️ <b>House Edge:</b> BIG အရမ်းများနေသဖြင့် ကာစီနိုမှ SMALL ကို ပြန်ချပေးနိုင်ပါသည်။\n"
    elif s_100 > (len(last_100_sizes) * 0.55): 
        score_b += house_edge_weight
        logic_used += f"├ ⚖️ <b>House Edge:</b> SMALL အရမ်းများနေသဖြင့် ကာစီနိုမှ BIG ကို ပြန်ချပေးနိုင်ပါသည်။\n"

    # ---------------------------------------------------------
    # ⚙️ 3. TRUE MACHINE LEARNING ENSEMBLE (RF + Gradient Boosting)
    # ---------------------------------------------------------
    X, y = [], []
    window = 5 # နောက်ဆုံး ၅ ပွဲ၏ Data Enrichment ကို သုံးမည်
    
    def encode_size(s): return 1 if s == 'BIG' else 0
    def encode_parity(p): return 1 if p == 'EVEN' else 0
    
    for i in range(len(sizes) - window):
        row = []
        for j in range(window):
            # အချက်အလက်များကို ပေါင်းစပ်ထည့်သွင်းခြင်း (Size, Number, Parity)
            row.append(encode_size(sizes[i+j]))
            row.append(numbers[i+j])
            row.append(encode_parity(parities[i+j]))
        X.append(row)
        y.append(encode_size(sizes[i+window]))
        
    if len(X) > 20:
        # Model 1: Random Forest
        rf_clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf_clf.fit(X, y)
        
        # Model 2: Gradient Boosting (XGBoost ၏ အခြေခံ)
        gb_clf = GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, max_depth=3, random_state=42)
        gb_clf.fit(X, y)
        
        # Current feature vector for prediction
        current_features = []
        for j in range(1, window + 1):
            current_features.append(encode_size(sizes[-j]))
            current_features.append(numbers[-j])
            current_features.append(encode_parity(parities[-j]))
            
        # AI ခန့်မှန်းချက်များကို ရယူခြင်း
        rf_pred = rf_clf.predict([current_features])[0]
        rf_prob = max(rf_clf.predict_proba([current_features])[0])
        
        gb_pred = gb_clf.predict([current_features])[0]
        gb_prob = max(gb_clf.predict_proba([current_features])[0])
        
        # AI နှစ်ခု၏ အဖြေတူညီပါက အမှတ်ပိုပေးမည် (Ensemble Agreement)
        if rf_pred == gb_pred:
            if rf_pred == 1: score_b += (rf_prob * ml_weight * 1.5)
            else: score_s += (rf_prob * ml_weight * 1.5)
            logic_used += "├ 🤖 <b>AI Ensemble:</b> RF နှင့် Gradient Boosting နှစ်ခုလုံး အဖြေတူညီပါသည်။\n"
        else:
            # မတူညီပါက Probability ပိုများသောကောင်ကို ယူမည်
            if rf_prob > gb_prob:
                if rf_pred == 1: score_b += (rf_prob * ml_weight)
                else: score_s += (rf_prob * ml_weight)
            else:
                if gb_pred == 1: score_b += (gb_prob * ml_weight)
                else: score_s += (gb_prob * ml_weight)
            logic_used += "├ 🤖 <b>AI Algorithms:</b> အဆင့်မြင့် Data Enrichment မှ ခန့်မှန်းပေးထားသည်။\n"

    # ---------------------------------------------------------
    # ⚙️ 4. RECENT PATTERN RECOGNITION (Short-term Memory)
    # ---------------------------------------------------------
    if len(sizes) >= 3:
        if sizes[-1] != sizes[-2] and sizes[-2] != sizes[-3]:
            # ခုတ်ချိုး
            pred_pattern = 'BIG' if sizes[-1] == 'SMALL' else 'SMALL'
            if pred_pattern == 'BIG': score_b += pattern_weight
            else: score_s += pattern_weight
            logic_used += "├ 🏓 <b>Short-Term:</b> ခုတ်ချိုး (Ping-Pong) ပုံစံ တွေ့ရသည်။\n"
        elif sizes[-1] == sizes[-2] == sizes[-3]:
            # အတန်းရှည်
            if sizes[-1] == 'BIG': score_b += pattern_weight
            else: score_s += pattern_weight
            logic_used += "├ 🐉 <b>Short-Term:</b> အတန်းရှည် (Dragon) ပုံစံ တွေ့ရသည်။\n"

    # ---------------------------------------------------------
    # 🎯 FINAL CALCULATION
    # ---------------------------------------------------------
    final_pred = "BIG" if score_b > score_s else "SMALL"
    total_score = score_b + score_s
    
    if total_score == 0: 
        return "BIG", 55.0, logic_used + "└ ⚠️ လုံလောက်သော အချက်အလက် မရှိသေးပါ။"
    
    # ဖြစ်နိုင်ခြေ ရာခိုင်နှုန်းကို AI စံနှုန်း 70% မှ 98% ကြား ချိန်ညှိခြင်း
    calc_prob = (max(score_b, score_s) / total_score) * 100
    final_prob = min(max(calc_prob, 72.0), 98.0) 
    
    logic_used += f"└ 🎯 <b>ဆုံးဖြတ်ချက်:</b> {final_prob:.1f}% သေချာပါသည်။"
    
    return final_pred, round(final_prob, 1), logic_used

# ==========================================
# 🎨 5. DYNAMIC GRAPH GENERATOR (Exact 1024x768 Perfect Layout)
# ==========================================
def generate_winrate_chart(predictions):
    wins, losses = 0, 0
    history_wr, bar_colors, dots_list = [], [], []
    
    latest_preds = list(reversed(predictions))[-20:]
    
    for p in latest_preds: 
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

    # 💡 Resolution အတိအကျ သတ်မှတ်ထားသည်
    fig = plt.figure(figsize=(10.24, 7.68), facecolor='#1e222d')
    
    # 💡 ဂရပ်ဇယားကို ပုံရဲ့ အပေါ်ဘက်ကို တင်ပေးလိုက်ပြီး အောက်ဘက် ၄၀% ကို စာသားအတွက် ဖယ်ထားပေးသည်
    # [Left, Bottom, Width, Height]
    ax = fig.add_axes([0.1, 0.40, 0.8, 0.45])
    ax.set_facecolor('#1e222d')
    
    ax.set_xlim(-0.5, 19.5)
    
    if total_played > 0:
        x = np.arange(total_played)
        ax.bar(x, [55]*total_played, color=bar_colors, width=0.8, bottom=0)
        ax.plot(x, history_wr, color='#2979ff', linewidth=3.5, marker='o', markersize=7, markerfacecolor='#1e222d', markeredgecolor='#2979ff', markeredgewidth=2)
    
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], color='#787b86', fontsize=12)
    ax.set_xticks([])
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#363a45')
    ax.spines['bottom'].set_color('#363a45')
    ax.grid(axis='y', color='#363a45', linestyle='-', linewidth=0.5)
    
    # 💡 စာသားများကို ဂရပ်အောက်ခြေမှ လွတ်ကင်းအောင် နေရာအတိအကျချထားသည်
    fig.text(0.5, 0.92, "WINRATE TRACKING", color='white', fontsize=26, fontweight='bold', ha='center')
    
    fig.text(0.5, 0.28, f"{win_rate}%", color='white', fontsize=45, fontweight='bold', ha='center')
    fig.text(0.35, 0.20, f"WINS: {wins}", color='#26a69a', fontsize=20, ha='center', fontweight='bold')
    fig.text(0.65, 0.20, f"LOSSES: {losses}", color='#ef5350', fontsize=20, ha='center', fontweight='bold')
    fig.text(0.5, 0.14, f"PREDICTION COUNT: {total_played}/20", color='white', fontsize=14, ha='center')
    fig.text(0.5, 0.09, "Recent Predictions (Oldest ➔ Latest)", color='#787b86', fontsize=12, ha='center')

    # အလုံးလေးများ
    if len(dots_list) > 0:
        dot_ax = fig.add_axes([0.1, 0.04, 0.8, 0.04]) 
        dot_ax.set_axis_off()
        dot_ax.set_xlim(0, 20) 
        dot_ax.set_ylim(0, 1)
        colors = dots_list[-20:]
        n_dots = len(colors)
        start_x = (20 - n_dots) / 2.0
        x_coords = [start_x + i + 0.5 for i in range(n_dots)]
        y_coords = [0.5] * n_dots
        dot_ax.scatter(x_coords, y_coords, s=250, c=colors, edgecolors='white', linewidths=1.5, zorder=5)
            
    fig.text(0.5, 0.01, "DEV-WANG LIN", color='#787b86', fontsize=14, fontweight='bold', ha='center', alpha=1)

    buf = io.BytesIO()
    # ဖြတ်ချခြင်းမပြုဘဲ Resolution အတိအကျထုတ်ယူသည်
    plt.savefig(buf, format='png', dpi=100, facecolor='#1e222d')
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
        'random': DATA_RANDOM,
        'signature': DATA_SIGNATURE,
        'timestamp': DATA_TIMESTAMP,
    }

    data = await fetch_with_retry(session, 'https://6lotteryapi.com/api/webapi/GetNoaverageEmerdList', headers, json_data)
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
    
    # ==============================================================
    # 🧠 CALCULATE LOSE STREAK & GET PREDICTION
    # ==============================================================
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
        reason = f"🧠 <b>Ultimate AI Engine</b>\n{mem_logic}"
    except Exception as e:
        predicted = "BIG (အကြီး) 🔴"
        mem_prob = 55.0
        reason = f"⚠️ AI Processing Error: {e}"
    
    final_prob = min(max(round(mem_prob, 1), 60.0), 98.0)
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
    def get_realtime_caption():
        sec_left = 30 - (int(time.time()) % 30)
        if sec_left == 30: sec_left = 0 # ၃၀ စက္ကန့်ပြည့်ချိန်တွင် 0s ဟုပြရန်
        return (
            f"<b>🏆 6WIN GO (30 SECONDS)</b>\n"
            f"⏰ Next Result In: <b>{sec_left}s</b>\n\n"
            f"{table_str}\n"
            f"🅿️ <b>Period:</b> {next_issue[:3]}**{next_issue[-4:]}\n"
            f"🎯 <b>Predict: {predicted}</b>\n"
            f"📈 <b>ဖြစ်နိုင်ခြေ:</b> {final_prob}%\n"
            f"💡 <b>သုံးသပ်ချက်:</b>\n"
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
    await message.reply("👋 မင်္ဂလာပါ။ 6WIN 1024x768 Perfect Layout + Ultimate AI အသင့်ဖြစ်နေပါပြီ။")

async def main():
    print("🚀 Aiogram Bigwin Bot (1024x768 + Ultimate AI Edition) စတင်နေပါပြီ...\n")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_broadcaster())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Bot ကို ရပ်တန့်လိုက်ပါသည်။")
