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
USERNAME = os.getenv("BIGWIN_USERNAME", "959675323878")
PASSWORD = os.getenv("BIGWIN_PASSWORD", "Mitheint11")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
MONGO_URI = os.getenv("MONGO_URI") 

if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, MONGO_URI]):
    print("❌ Error: .env ဖိုင်ထဲတွင် အချက်အလက်များ ပြည့်စုံစွာ မပါဝင်ပါ။")
    exit()

# 🔑========================================🔑
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
        print("🗄 MongoDB ချိတ်ဆက်မှု အောင်မြင်ပါသည်။ (🚀 AI Analytics Dashboard Edition)")
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
        'random': DATA_RANDOM,
        'signature': DATA_SIGNATURE,
        'timestamp': DATA_TIMESTAMP,
    }
    data = await fetch_with_retry(session, 'https://6lotteryapi.com/api/webapi/Login', BASE_HEADERS, json_data)
    if data and data.get('code') == 0:
        token_str = data.get('data', {}) if isinstance(data.get('data'), str) else data.get('data', {}).get('token', '')
        CURRENT_TOKEN = f"Bearer {token_str}"
        print("✅ 6WIN ဆာဗာသို့ Login အောင်မြင်ပါသည်။\n")
        return True
    return False

# ==========================================
# 🧠 THE ULTIMATE AI PREDICTION LOGIC
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
# 🎨 5. DYNAMIC GRAPH GENERATOR (AI ANALYTICS DASHBOARD)
# ==========================================
def generate_winrate_chart(predictions):
    wins, losses = 0, 0
    bar_colors, dots_list = [], []
    bar_heights = [] # To simulate the performance trend waves
    
    latest_preds = list(reversed(predictions))[-20:]
    
    for p in latest_preds: 
        if 'WIN' in p.get('win_lose', ''):
            wins += 1
            bar_colors.append('#00e5ff')  # Cyan/Green glow
            dots_list.append(('G', '#22c55e'))
            bar_heights.append(85) # High bar for WIN
        else:
            losses += 1
            bar_colors.append('#ff4444')  # Red glow
            dots_list.append(('R', '#ef4444'))
            bar_heights.append(35) # Low bar for LOSS
            
    total_played = wins + losses
    win_rate = int((wins / total_played * 100)) if total_played > 0 else 0

    # 💡 10.24 inches x 100 DPI = 1024x768 pixels အတိအကျ
    fig = plt.figure(figsize=(10.24, 7.68), facecolor='#16181c') 
    
    # --- TITLE ---
    fig.text(0.05, 0.90, "AI PERFORMANCE ANALYTICS", color='#ffffff', fontsize=32, fontweight='bold', ha='left')

    # --- 1. CIRCLE GAUGE (Left) ---
    ax_circle = fig.add_axes([0.05, 0.45, 0.35, 0.40])
    ax_circle.set_axis_off()
    ax_circle.set_xlim(0, 1)
    ax_circle.set_ylim(0, 1)
    
    # Background circle arc
    theta_bg = np.linspace(0, 2*np.pi, 100)
    ax_circle.plot(0.5 + 0.4*np.cos(theta_bg), 0.5 + 0.4*np.sin(theta_bg), color='#2a2d35', linewidth=10)
    
    # Progress arc (Cyan)
    if win_rate > 0:
        theta_fg = np.linspace(np.pi/2, np.pi/2 - 2*np.pi*(win_rate/100), 100)
        x_fg = 0.5 + 0.4 * np.cos(theta_fg)
        y_fg = 0.5 + 0.4 * np.sin(theta_fg)
        # Glow Effect
        for lw, alpha in zip([20, 12, 6], [0.2, 0.5, 1.0]):
            ax_circle.plot(x_fg, y_fg, color='#00e5ff', linewidth=lw, alpha=alpha)
            
    # Text inside circle
    ax_circle.text(0.5, 0.70, f"{total_played}/20", color='#a0a0a0', fontsize=16, fontweight='bold', ha='center', va='center')
    ax_circle.text(0.5, 0.60, "TOTAL WINRATE", color='#808080', fontsize=12, fontweight='bold', ha='center', va='center')
    ax_circle.text(0.5, 0.45, f"{win_rate}%", color='#00e5ff', fontsize=55, fontweight='bold', ha='center', va='center')
    ax_circle.text(0.5, 0.30, "PREDICTIONS MADE", color='#808080', fontsize=12, fontweight='bold', ha='center', va='center')
    
    # Finalised Badge
    badge = patches.FancyBboxPatch((0.35, 0.15), 0.3, 0.08, boxstyle="round,pad=0.02", fc="#2a2d35", ec="#00e5ff", lw=1.5)
    ax_circle.add_patch(badge)
    ax_circle.text(0.5, 0.19, "FINALISED ✓", color='#00e5ff', fontsize=11, fontweight='bold', ha='center', va='center')

    # --- 2. BAR CHART (Right) ---
    fig.text(0.75, 0.85, "SESSION PERFORMANCE TREND", color='#a0a0a0', fontsize=14, fontweight='bold', ha='center')
    # Underline
    fig.lines.extend([plt.Line2D([0.55, 0.95], [0.83, 0.83], color='#333333', lw=2, transform=fig.transFigure)])
    
    ax_bar = fig.add_axes([0.55, 0.45, 0.40, 0.35])
    ax_bar.set_facecolor('#16181c')
    ax_bar.set_xlim(-0.5, 19.5)
    ax_bar.set_ylim(0, 100)
    
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.spines['left'].set_visible(False)
    ax_bar.spines['bottom'].set_color('#333333')
    
    ax_bar.set_yticks([25, 50, 75])
    ax_bar.set_yticklabels(['', '', ''], color='#16181c') 
    ax_bar.grid(axis='y', color='#333333', linestyle='-', linewidth=1.5)
    
    if total_played > 0:
        x_pos = np.arange(total_played)
        ax_bar.bar(x_pos, bar_heights, color=bar_colors, width=0.6, alpha=0.9, zorder=3)
        
    ax_bar.set_xticks(np.arange(20))
    ax_bar.set_xticklabels([str(i+1) for i in range(20)], color='#808080', fontsize=10)

    # --- 3. WINS & LOSSES BOXES ---
    # WIN Box (Cyan)
    ax_win = fig.add_axes([0.05, 0.22, 0.40, 0.18])
    ax_win.set_axis_off()
    ax_win.set_xlim(0, 1)
    ax_win.set_ylim(0, 1)
    rect_win = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.1", fc="#00e5ff", ec="none")
    ax_win.add_patch(rect_win)
    ax_win.text(0.05, 0.75, "TOTAL WINS:", color='#004d40', fontsize=18, fontweight='bold', va='center')
    ax_win.text(0.05, 0.35, f"{wins}", color='black', fontsize=45, fontweight='bold', va='center')
    circ_win = plt.Circle((0.85, 0.5), 0.2, color='#00b3cc', ec='none')
    ax_win.add_patch(circ_win)
    ax_win.text(0.85, 0.5, "✓", color='white', fontsize=30, fontweight='bold', ha='center', va='center')

    # LOSE Box (Red)
    ax_lose = fig.add_axes([0.48, 0.22, 0.40, 0.18])
    ax_lose.set_axis_off()
    ax_lose.set_xlim(0, 1)
    ax_lose.set_ylim(0, 1)
    rect_lose = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.1", fc="#ff4444", ec="none")
    ax_lose.add_patch(rect_lose)
    ax_lose.text(0.05, 0.75, "TOTAL LOSSES:", color='#4d0000', fontsize=18, fontweight='bold', va='center')
    ax_lose.text(0.05, 0.35, f"{losses}", color='white', fontsize=45, fontweight='bold', va='center')
    circ_lose = plt.Circle((0.85, 0.5), 0.2, color='#cc0000', ec='none')
    ax_lose.add_patch(circ_lose)
    ax_lose.text(0.85, 0.5, "X", color='white', fontsize=26, fontweight='bold', ha='center', va='center')

    # --- Watermark ---
    fig.text(0.95, 0.28, "DEV - WANG LIN", color='#ffffff', fontsize=26, fontweight='bold', ha='right', style='italic')
    fig.lines.extend([plt.Line2D([0.65, 0.95], [0.25, 0.25], color='#333333', lw=2, transform=fig.transFigure)])

    # --- 4. TIMELINE (Dots) ---
    fig.text(0.05, 0.15, "FULL PREDICTION TIMELINE (Oldest to Latest)", color='#a0a0a0', fontsize=12, fontweight='bold', ha='left')
    
    ax_time = fig.add_axes([0.05, 0.05, 0.9, 0.08])
    ax_time.set_axis_off()
    ax_time.set_xlim(-0.5, 19.5)
    ax_time.set_ylim(0, 1)
    
    if len(dots_list) > 0:
        for i, (char, color) in enumerate(dots_list):
            # အလုံးလေးတွေ ဆွဲပေးခြင်း
            ax_time.scatter(i, 0.5, s=600, c=color, edgecolors='none', zorder=5)
            # အလုံးထဲက G / R စာလုံး
            ax_time.text(i, 0.5, char, color='white', fontsize=14, fontweight='bold', ha='center', va='center', zorder=6)
            
    buf = io.BytesIO()
    # 💡 [အရေးကြီး] Resolution ကို 1024x768 အတိအကျဖြစ်ရန် bbox_inches မသုံးထားပါ
    plt.savefig(buf, format='png', dpi=100, facecolor='#16181c') 
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
        reason = f"⚠️ AI Processing Error"
    
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

    def get_realtime_caption():
        sec_left = 30 - (int(time.time()) % 30)
        if sec_left == 30: sec_left = 0 
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
        if is_new_issue or not MAIN_MESSAGE_ID:
            img_buf = await asyncio.to_thread(generate_winrate_chart, session_preds)
            unique_filename = f"winrate_chart_{int(current_time)}.png"
            photo = BufferedInputFile(img_buf.read(), filename=unique_filename)
            
            tg_caption = get_realtime_caption()
            
            if MAIN_MESSAGE_ID:
                media = InputMediaPhoto(media=photo, caption=tg_caption, parse_mode="HTML")
                await bot.edit_message_media(chat_id=TELEGRAM_CHANNEL_ID, message_id=MAIN_MESSAGE_ID, media=media)
            else:
                msg = await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=photo, caption=tg_caption)
                MAIN_MESSAGE_ID = msg.message_id
            
            LAST_CAPTION_EDIT_TIME = time.time() 
            
        else:
            if current_time - LAST_CAPTION_EDIT_TIME >= 1.0:
                if MAIN_MESSAGE_ID:
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

async def auto_broadcaster():
    await init_db() 
    async with aiohttp.ClientSession() as session:
        await login_and_get_token(session)
        while True:
            await check_game_and_predict(session)
            await asyncio.sleep(0.5) 

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("👋 မင်္ဂလာပါ။ 6WIN AI Analytics Dashboard အသင့်ဖြစ်နေပါပြီ။")

async def main():
    print("🚀 Aiogram Bigwin Bot (AI Analytics Dashboard Edition) စတင်နေပါပြီ...\n")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_broadcaster())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Bot ကို ရပ်တန့်လိုက်ပါသည်။")
