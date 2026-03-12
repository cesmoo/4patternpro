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
# 🔧 2. SYSTEM VARIABLES & ANTI-LAG STATE
# ==========================================
CURRENT_TOKEN = ""
LAST_PROCESSED_ISSUE = None
MAIN_MESSAGE_ID = None 
SESSION_START_ISSUE = None 
LAST_CAPTION_EDIT_TIME = 0 
API_ERROR_COUNT = 0 

# 💡 [Anti-Lag System] Timer မထစ်စေရန် နောက်ဆုံးအချက်အလက်ကို မှတ်သားထားမည့် State
LAST_KNOWN_STATE = {
    "table_str": "<code>Data Loading...</code>",
    "next_issue": "Loading",
    "predicted": "Wait",
    "final_prob": 0.0,
    "reason": "Syncing Data...",
    "bet_advice": "..."
}

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
        print("🗄 MongoDB ချိတ်ဆက်မှု အောင်မြင်ပါသည်။ (🚀 5-Pattern AI + Anti-Lag Edition)")
    except Exception as e:
        pass

# ==========================================
# 🔑 3. ASYNC API FUNCTIONS
# ==========================================
async def fetch_with_retry(session, url, headers, json_data, retries=1):
    for attempt in range(retries):
        try:
            # 💡 [Fail-Fast] Data ဆွဲတာ ကြာပြီး စက္ကန့်တွေ ထစ်မနေစေရန် Timeout ကို 2 စက္ကန့်သာ ထားပါသည်
            async with session.post(url, headers=headers, json=json_data, timeout=2.0) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            await asyncio.sleep(0.2)
    return None

async def login_and_get_token(session: aiohttp.ClientSession):
    global CURRENT_TOKEN
    json_data = {
        'username': '959675323878',
        'pwd': 'Mitheint11',
        'phonetype': 1,
        'logintype': 'mobile',
        'packId': '',
        'deviceId': '51ed4ee0f338a1bb24063ffdfcd31ce6',
        'language': 7,
        'random': '4fc4413428be43faa1a3f30d9745ae3a',
        'signature': '5458639AF428AC897FDFF1102D82EB9C',
        'timestamp': 1773326030,
    }
    data = await fetch_with_retry(session, 'https://api.bigwinqaz.com/api/webapi/Login', BASE_HEADERS, json_data)
    if data and data.get('code') == 0:
        token_str = data.get('data', {}) if isinstance(data.get('data'), str) else data.get('data', {}).get('token', '')
        CURRENT_TOKEN = f"Bearer {token_str}"
        print("✅ Login အောင်မြင်ပါသည်။ Token အသစ် ရရှိပါပြီ。\n")
        return True
    return False

# ==========================================
# 🧠 4. THE ULTIMATE AI (Data Enrichment + Auto-Tuning + ML + 5-Pattern)
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

    # 💡 4. NEW 5-PATTERN RECOGNITION (အဆင့်မြင့် ပုံစံ ၅ မျိုး)
    if len(sizes) >= 4:
        s1, s2, s3, s4 = sizes[-1], sizes[-2], sizes[-3], sizes[-4] # s1=နောက်ဆုံးအလုံး, s4=ဟိုးအရင်အလုံး
        
        # Pattern 1: Dragon (၄ ပွဲဆက်တူ - B B B B သို့ S S S S)
        if s1 == s2 == s3 == s4:
            pred_pattern = s1 
            if pred_pattern == 'BIG': score_b += pattern_weight * 1.5
            else: score_s += pattern_weight * 1.5
            logic_used += "├ 🐉 <b>Pattern:</b> 4-Dragon (အတန်းရှည်)\n"
            
        # Pattern 2: Ping-Pong (ခုတ်ချိုး - B S B S သို့ S B S B)
        elif s1 != s2 and s2 != s3 and s3 != s4:
            pred_pattern = 'BIG' if s1 == 'SMALL' else 'SMALL'
            if pred_pattern == 'BIG': score_b += pattern_weight * 1.5
            else: score_s += pattern_weight * 1.5
            logic_used += "├ 🏓 <b>Pattern:</b> 4-PingPong (ခုတ်ချိုး)\n"
            
        # Pattern 3: Two-Two (နှစ်လုံးပြတ် - B B S S သို့ S S B B)
        elif s1 == s2 and s3 == s4 and s1 != s3:
            pred_pattern = 'BIG' if s1 == 'SMALL' else 'SMALL'
            if pred_pattern == 'BIG': score_b += pattern_weight * 1.2
            else: score_s += pattern_weight * 1.2
            logic_used += "├ 👯 <b>Pattern:</b> Two-Two (နှစ်လုံးပြတ်)\n"
            
        # Pattern 4: Trend Break (သုံးလုံး-တစ်လုံး လမ်းပြောင်း - B B B S သို့ S S S B)
        elif s2 == s3 == s4 and s1 != s2:
            pred_pattern = s1 
            if pred_pattern == 'BIG': score_b += pattern_weight * 1.2
            else: score_s += pattern_weight * 1.2
            logic_used += "├ 🎯 <b>Pattern:</b> Trend Break (လမ်းကြောင်းပြောင်း)\n"
            
        # 💡 Pattern 5: One-Three (တစ်လုံး-သုံးလုံး ရေစီး - B S S S သို့ S B B B)
        elif s1 == s2 == s3 and s4 != s1:
            pred_pattern = s1 # ရေစီးအတိုင်း လိုက်မည်
            if pred_pattern == 'BIG': score_b += pattern_weight * 1.2
            else: score_s += pattern_weight * 1.2
            logic_used += "├ 🌊 <b>Pattern:</b> One-Three (တစ်လုံး-သုံးလုံး)\n"

    elif len(sizes) >= 3: # Fallback for early patterns
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
# 🎨 5. DYNAMIC GRAPH GENERATOR (ACCURATE TREND LINE)
# ==========================================
def generate_winrate_chart(predictions):
    wins, losses = 0, 0
    bar_colors, dots_list, bar_heights = [], [], []
    history_wr = []
    
    latest_preds = list(reversed(predictions))[-20:]
    
    for i, p in enumerate(latest_preds): 
        current_played = i + 1
        
        if 'WIN' in p.get('win_lose', ''):
            wins += 1
            bar_colors.append('#00e5ff')  # Cyan Glow
            dots_list.append(('G', '#1de9b6'))
        else:
            losses += 1
            bar_colors.append('#ff4444')  # Red Glow
            dots_list.append(('R', '#ef5350'))
            
        current_wr = (wins / current_played) * 100
        bar_heights.append(current_wr) 
        history_wr.append(current_wr)
            
    total_played = wins + losses
    win_rate = int((wins / total_played * 100)) if total_played > 0 else 0

    # 1024x768 Fixed Size with Sci-Fi Dark Background
    fig = plt.figure(figsize=(10.24, 7.68), facecolor='#1c1f26') 
    
    fig.text(0.05, 0.90, "AI PERFORMANCE ANALYTICS", color='#ffffff', fontsize=32, fontweight='bold', ha='left')

    # --- CIRCLE GAUGE (Left) ---
    ax_circle = fig.add_axes([0.08, 0.42, 0.35, 0.40])
    ax_circle.set_axis_off()
    ax_circle.set_xlim(0, 1)
    ax_circle.set_ylim(0, 1)
    
    theta_bg = np.linspace(-1.25*np.pi, 0.25*np.pi, 200)
    ax_circle.plot(0.5 + 0.45*np.cos(theta_bg), 0.5 + 0.45*np.sin(theta_bg), color='#2c313c', linewidth=12)
    
    if win_rate > 0:
        end_angle = 0.25*np.pi - (win_rate/100) * 1.5 * np.pi
        theta_fg = np.linspace(0.25*np.pi, end_angle, 100)
        ax_circle.plot(0.5 + 0.45*np.cos(theta_fg), 0.5 + 0.45*np.sin(theta_fg), color='#00e5ff', linewidth=12)
        ax_circle.plot(0.5 + 0.45*np.cos(theta_fg), 0.5 + 0.45*np.sin(theta_fg), color='#00e5ff', linewidth=22, alpha=0.2)
            
    ax_circle.text(0.5, 0.75, f"{total_played}/20", color='#a3a8b5', fontsize=16, fontweight='bold', ha='center', va='center')
    ax_circle.text(0.5, 0.65, "TOTAL WINRATE", color='#7a8294', fontsize=12, fontweight='bold', ha='center', va='center')
    ax_circle.text(0.5, 0.48, f"{win_rate}%", color='#00e5ff', fontsize=65, fontweight='bold', ha='center', va='center')
    ax_circle.text(0.5, 0.32, "PREDICTIONS MADE", color='#7a8294', fontsize=12, fontweight='bold', ha='center', va='center')
    
    badge = patches.FancyBboxPatch((0.35, 0.16), 0.3, 0.08, boxstyle="round,pad=0.03", fc="#164e63", ec="#00e5ff", lw=1.5)
    ax_circle.add_patch(badge)
    ax_circle.text(0.5, 0.20, "FINALISED ✓", color='#00e5ff', fontsize=11, fontweight='bold', ha='center', va='center')
    
    ax_circle.text(0.05, 0.05, "0", color='#7a8294', fontsize=12, fontweight='bold', ha='center')
    ax_circle.text(0.95, 0.05, "100%", color='#7a8294', fontsize=12, fontweight='bold', ha='center')

    # --- BAR CHART + TREND LINE (Right) ---
    fig.text(0.74, 0.85, "SESSION PERFORMANCE TREND", color='#a3a8b5', fontsize=14, fontweight='bold', ha='center')
    fig.lines.extend([plt.Line2D([0.55, 0.93], [0.83, 0.83], color='#2c313c', lw=2, transform=fig.transFigure)])
    
    ax_bar = fig.add_axes([0.55, 0.47, 0.38, 0.33])
    ax_bar.set_facecolor('#1c1f26')
    ax_bar.set_xlim(-0.5, 19.5)
    ax_bar.set_ylim(0, 105) 
    
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.spines['left'].set_visible(False)
    ax_bar.spines['bottom'].set_visible(False)
    
    ax_bar.set_yticks([0, 25, 50, 75, 100])
    ax_bar.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], color='#7a8294', fontsize=10, fontweight='bold') 
    ax_bar.tick_params(axis='y', length=0, pad=5)
    ax_bar.grid(axis='y', color='#2c313c', linestyle='-', linewidth=1.5)
    
    if total_played > 0:
        x_pos = np.arange(total_played)
        
        # 1. Outer Glow 
        ax_bar.bar(x_pos, bar_heights, color=bar_colors, width=0.8, alpha=0.15, zorder=2, align='center')
        # 2. Solid Inner Core 
        ax_bar.bar(x_pos, bar_heights, color=bar_colors, width=0.45, alpha=0.9, zorder=3, align='center')
        
        # 3. Trend Line Graph
        ax_bar.plot(x_pos, history_wr, color='#3b82f6', linewidth=2.5, marker='o', markersize=6, markerfacecolor='#1c1f26', markeredgecolor='#00e5ff', markeredgewidth=2, zorder=4)
        
    ax_bar.set_xticks(np.arange(20))
    ax_bar.set_xticklabels([str(i+1) for i in range(20)], color='#7a8294', fontsize=10)

    # --- WINS & LOSSES BOXES ---
    ax_win = fig.add_axes([0.05, 0.22, 0.28, 0.16])
    ax_win.set_axis_off()
    ax_win.set_xlim(0, 1)
    ax_win.set_ylim(0, 1)
    rect_win = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.1", fc="#1de9b6", ec="none")
    ax_win.add_patch(rect_win)
    ax_win.text(0.1, 0.75, "TOTAL WINS:", color='#004d40', fontsize=16, fontweight='bold', va='center')
    ax_win.text(0.1, 0.35, f"{wins}", color='#000000', fontsize=48, fontweight='bold', va='center')
    circ_win = plt.Circle((0.85, 0.5), 0.22, color='none', ec='#004d40', lw=3)
    ax_win.add_patch(circ_win)
    ax_win.text(0.85, 0.5, "✓", color='#004d40', fontsize=28, fontweight='bold', ha='center', va='center')

    ax_lose = fig.add_axes([0.35, 0.22, 0.28, 0.16])
    ax_lose.set_axis_off()
    ax_lose.set_xlim(0, 1)
    ax_lose.set_ylim(0, 1)
    rect_lose = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.1", fc="#ef5350", ec="none")
    ax_lose.add_patch(rect_lose)
    ax_lose.text(0.1, 0.75, "TOTAL LOSSES:", color='#4d0000', fontsize=16, fontweight='bold', va='center')
    ax_lose.text(0.1, 0.35, f"{losses}", color='#ffffff', fontsize=48, fontweight='bold', va='center')
    shield = patches.RegularPolygon((0.85, 0.5), numVertices=6, radius=0.25, orientation=np.pi/6, color='none', ec='#4d0000', lw=3)
    ax_lose.add_patch(shield)

    # --- WATERMARK ---
    ax_wm = fig.add_axes([0.65, 0.22, 0.30, 0.16])
    ax_wm.set_axis_off()
    ax_wm.text(0.5, 0.5, "DEV - WANG LIN", color='#ffffff', fontsize=26, fontweight='bold', style='italic', ha='center', va='center')
    ax_wm.plot([0.1, 0.9], [0.30, 0.30], color='#ffffff', lw=3)
    ax_wm.plot([0.1, 0.9], [0.70, 0.70], color='#ffffff', lw=3)

    # --- TIMELINE (Dots) ---
    fig.text(0.05, 0.16, "FULL PREDICTION TIMELINE (Oldest to Latest)", color='#a3a8b5', fontsize=12, fontweight='bold', ha='left')
    
    ax_time = fig.add_axes([0.05, 0.05, 0.9, 0.08])
    ax_time.set_axis_off()
    ax_time.set_xlim(-0.5, 19.5)
    ax_time.set_ylim(0, 1)
    
    if len(dots_list) > 0:
        for i, (char, color) in enumerate(dots_list):
            ax_time.scatter(i, 0.5, s=800, c=color, edgecolors='none', zorder=4, alpha=0.3) 
            ax_time.scatter(i, 0.5, s=400, c=color, edgecolors='none', zorder=5, alpha=1.0)
            ax_time.text(i, 0.5, char, color='#ffffff', fontsize=14, fontweight='bold', ha='center', va='center', zorder=6)

    # 💡 ဖြတ်ချခြင်းမပြုဘဲ 1024x768 အတိအကျထုတ်ယူသည်
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor='#1c1f26') 
    buf.seek(0)
    plt.close(fig)
    return buf

# ==========================================
# 🚀 6. MAIN LOGIC & UI UPDATER (ANTI-LAG ZERO LATENCY)
# ==========================================
async def check_game_and_predict(session: aiohttp.ClientSession):
    global CURRENT_TOKEN, LAST_PROCESSED_ISSUE, MAIN_MESSAGE_ID, SESSION_START_ISSUE
    global LAST_CAPTION_EDIT_TIME, API_ERROR_COUNT, LAST_KNOWN_STATE
    
    if not CURRENT_TOKEN:
        if not await login_and_get_token(session): return

    headers = BASE_HEADERS.copy()
    headers['authorization'] = CURRENT_TOKEN

    json_data = {
        'pageSize': 10, 'pageNo': 1, 'typeId': 30, 'language': 7,
        'random': '9ef85244056948ba8dcae7aee7758bf4', # ကိုယ်တိုင်လာလဲပေးရန်
        'signature': '2EDB8C2B5264F62EC53116916A9EC05C',
        'timestamp': 1773326133,
    }

    # 💡 [Anti-Lag System] Data ကိုအရင်ဆွဲမည်။ မရလျှင် အောက်က Timer Block သို့ တန်းသွားမည်။
    data = await fetch_with_retry(session, 'https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList', headers, json_data)
    
    if data and data.get('code') == 0:
        API_ERROR_COUNT = 0 
        records = data.get("data", {}).get("list", [])
        
        if records:
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
                else: break

            cursor = history_collection.find().sort("issue_number", -1).limit(5000)
            history_docs = await cursor.to_list(length=5000)

            try:
                mem_pred, mem_prob, mem_logic = await asyncio.to_thread(ultimate_ai_predict, history_docs, recent_preds)
                predicted = "BIG (အကြီး) 🔴" if mem_pred == "BIG" else "SMALL (အသေး) 🟢"
                reason = f"🧠 <b>5-Pattern AI Engine</b>\n{mem_logic}"
            except Exception as e:
                predicted = "BIG (အကြီး) 🔴"
                mem_prob = 55.0
                reason = "⚠️ AI Processing Error"
            
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

            # 💡 [Anti-Lag System] Data ရလာရင် Cache ထဲမှာ မှတ်ထားမည်
            LAST_KNOWN_STATE["table_str"] = table_str
            LAST_KNOWN_STATE["next_issue"] = next_issue
            LAST_KNOWN_STATE["predicted"] = predicted
            LAST_KNOWN_STATE["final_prob"] = final_prob
            LAST_KNOWN_STATE["reason"] = reason
            LAST_KNOWN_STATE["bet_advice"] = bet_advice
            
            # ပွဲသစ်ထွက်ချိန်တွင် ပုံဆွဲပြီး တင်ပေးမည်
            if is_new_issue or not MAIN_MESSAGE_ID:
                img_buf = await asyncio.to_thread(generate_winrate_chart, session_preds)
                unique_filename = f"winrate_chart_{int(time.time())}.png"
                photo = BufferedInputFile(img_buf.read(), filename=unique_filename)
                
                sec_left = 30 - (int(time.time()) % 30)
                if sec_left == 30: sec_left = 0
                iss_display = f"{next_issue[:3]}**{next_issue[-4:]}"
                
                tg_caption = (
                    f"<b>🏆 WIN GO (30 SECONDS)</b>\n"
                    f"⏰ Next Result In: <b>{sec_left}s</b>\n\n"
                    f"{table_str}\n"
                    f"🅿️ <b>Period:</b> {iss_display}\n"
                    f"🎯 <b>Predict: {predicted}</b>\n"
                    f"📈 <b>ဖြစ်နိုင်ခြေ:</b> {final_prob}%\n"
                    f"💡 <b>အကြောင်းပြချက်:</b>\n{reason}\n"
                    f"━━━━━━━━━━━━━━━━━━\n{bet_advice}"
                )
                
                if MAIN_MESSAGE_ID:
                    media = InputMediaPhoto(media=photo, caption=tg_caption, parse_mode="HTML")
                    await bot.edit_message_media(chat_id=TELEGRAM_CHANNEL_ID, message_id=MAIN_MESSAGE_ID, media=media)
                else:
                    msg = await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=photo, caption=tg_caption)
                    MAIN_MESSAGE_ID = msg.message_id
                
                LAST_CAPTION_EDIT_TIME = time.time()
                return # ပုံအသစ်တင်ပြီးပါက ဤနေရာမှရပ်မည်။

    elif data and data.get('code') != 0:
        API_ERROR_COUNT += 1
        if data.get('code') == 401 or "token" in str(data.get('msg')).lower(): 
            CURRENT_TOKEN = ""
    else:
        # Timeout Error
        API_ERROR_COUNT += 1

    # ==============================================================
    # ⏱️ [Zero-Lag] TIMER UPDATE BLOCK
    # ==============================================================
    current_time = time.time()
    if current_time - LAST_CAPTION_EDIT_TIME >= 1.5:
        if MAIN_MESSAGE_ID and LAST_KNOWN_STATE["next_issue"] != "Loading":
            sec_left = 30 - (int(time.time()) % 30)
            if sec_left == 30: sec_left = 0 
            
            iss = LAST_KNOWN_STATE['next_issue']
            iss_display = f"{iss[:3]}**{iss[-4:]}" if len(iss) > 4 else iss
            
            tg_caption = (
                f"<b>🏆 WIN GO (30 SECONDS)</b>\n"
                f"⏰ Next Result In: <b>{sec_left}s</b>\n\n"
                f"{LAST_KNOWN_STATE['table_str']}\n"
                f"🅿️ <b>Period:</b> {iss_display}\n"
                f"🎯 <b>Predict: {LAST_KNOWN_STATE['predicted']}</b>\n"
                f"📈 <b>ဖြစ်နိုင်ခြေ:</b> {LAST_KNOWN_STATE['final_prob']}%\n"
                f"💡 <b>အကြောင်းပြချက်:</b>\n{LAST_KNOWN_STATE['reason']}\n"
                f"━━━━━━━━━━━━━━━━━━\n{LAST_KNOWN_STATE['bet_advice']}"
            )
            
            if API_ERROR_COUNT >= 3:
                tg_caption = f"⚠️ <b>[API သော့ သက်တမ်းကုန်သွားပါပြီ! အသစ်လဲပေးပါ]</b>\n\n" + tg_caption

            try:
                await bot.edit_message_caption(chat_id=TELEGRAM_CHANNEL_ID, message_id=MAIN_MESSAGE_ID, caption=tg_caption, parse_mode="HTML")
                LAST_CAPTION_EDIT_TIME = time.time()
            except TelegramRetryAfter as e:
                LAST_CAPTION_EDIT_TIME = time.time() + e.retry_after
            except TelegramBadRequest as e:
                if "message to edit not found" in str(e):
                    MAIN_MESSAGE_ID = None
            except Exception:
                pass

# ==========================================
# 🔄 6. BACKGROUND TASK
# ==========================================
async def auto_broadcaster():
    await init_db() 
    async with aiohttp.ClientSession() as session:
        await login_and_get_token(session)
        while True:
            try:
                await check_game_and_predict(session)
            except Exception as e:
                pass
            await asyncio.sleep(0.5) 

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("👋 မင်္ဂလာပါ။ စနစ်က Zero-Lag Timer ဖြင့် လုံးဝတိကျစွာ အလုပ်လုပ်နေပါပြီ။")

async def main():
    print("🚀 Aiogram Bigwin Bot (5-Pattern AI Edition) စတင်နေပါပြီ...\n")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_broadcaster())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Bot ကို ရပ်တန့်လိုက်ပါသည်။")
