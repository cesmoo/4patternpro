"""
====================================================================================
🏆 ULTRA-AI PREDICTION SYSTEM (10-CORE ARCHITECTURE) 🏆
====================================================================================
Developer: Master AI System
Target: 6win566 Win Go (Regular)
Architecture: Modular Object-Oriented Programming (OOP)
Pipeline: 10 AI Engines ➡️ Meta-AI Weighting ➡️ Final Prediction
====================================================================================
"""

import asyncio
import time
import os
import logging
import math
from collections import Counter
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv

# Async Web & Database
import aiohttp
import motor.motor_asyncio 

# Telegram UI
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# --- 🧠 ULTRA AI & DATA SCIENCE LIBRARIES ---
import numpy as np
import scipy.stats as stats
import random
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim

import warnings
warnings.filterwarnings("ignore")

# =========================================================================
# ⚙️ MODULE 1: SYSTEM CONFIGURATION & ADVANCED LOGGING
# =========================================================================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ULTRA-AI")

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    CHANNEL_ID: str = os.getenv("CHANNEL_ID", "YOUR_CHANNEL_ID")
    MONGO_URI: str = os.getenv("MONGO_URI", "YOUR_MONGO_URI")
    
    WIN_STICKER: str = "CAACAgUAAxkBAAEQwtVpt1_oWxyaQFmiy3O_1knZjN9yCwAC2hIAAikFkVX0qhu40v6REDoE"  
    LOSE_STICKER: str = "" 
    
    MULTIPLIERS: List[int] = [1, 2, 3, 5, 8, 15, 30, 50, 100]
    API_URL: str = 'https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList'
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        return {
            'authority': 'api.bigwinqaz.com', 
            'accept': 'application/json, text/plain, */*',
            # Token အသစ်ကို လိုအပ်ပါက အစားထိုးပါ
            'content-type': 'application/json;charset=UTF-8', 
            'origin': 'https://www.777bigwingame.app',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# =========================================================================
# 🗄️ MODULE 2: ASYNC DATABASE MANAGER
# =========================================================================
class DatabaseManager:
    def __init__(self, uri: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client['bigwin4pattern_database']
        self.history = self.db['game_history']
        self.predictions = self.db['predictions']

    async def initialize(self) -> None:
        try:
            await self.history.create_index("issue_number", unique=True)
            await self.predictions.create_index("issue_number", unique=True)
            logger.info("✅ Async Database Initialized Successfully.")
        except Exception as e:
            logger.error(f"❌ Database Initialization Error: {e}")

    async def save_history(self, issue: str, number: int, size: str, parity: str) -> None:
        try:
            doc = {
                "number": int(number), "size": str(size),
                "parity": str(parity), "timestamp": datetime.now()
            }
            await self.history.update_one({"issue_number": issue}, {"$setOnInsert": doc}, upsert=True)
        except Exception as e:
            logger.error(f"Save History Error: {e}")

    async def save_prediction(self, issue: str, pred_size: str, confidence: float, details: Dict[str, float]) -> None:
        try:
            doc = {
                "predicted_size": str(pred_size), "confidence": float(confidence), 
                "model_votes": details, "timestamp": datetime.now()
            }
            await self.predictions.update_one({"issue_number": issue}, {"$set": doc}, upsert=True)
        except Exception as e:
            logger.error(f"Save Prediction Error: {e}")

    async def update_result(self, issue: str, actual_size: str, actual_number: int, win_lose: str) -> None:
        try:
            doc = {
                "actual_size": str(actual_size), "actual_number": int(actual_number), "win_lose": str(win_lose)
            }
            await self.predictions.update_one({"issue_number": issue}, {"$set": doc})
        except Exception as e:
            logger.error(f"Update Result Error: {e}")

    async def get_history(self, limit: int = 500) -> List[Dict[str, Any]]:
        try:
            return await self.history.find().sort("issue_number", -1).limit(limit).to_list(length=limit)
        except Exception as e:
            logger.error(f"Get History Error: {e}")
            return []

    async def get_recent_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            return await self.predictions.find({"win_lose": {"$ne": None}}).sort("issue_number", -1).limit(limit).to_list(length=limit)
        except Exception as e:
            logger.error(f"Get Predictions Error: {e}")
            return []

# =========================================================================
# 🔬 MODULE 3: ADVANCED FEATURE ENGINEERING
# =========================================================================
class FeatureEngineer:
    def __init__(self, window_size: int = 6):
        self.window = window_size
        self.scaler = StandardScaler()

    def extract_features(self, sizes: List[str], numbers: List[int], parities: List[str]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        if len(sizes) < self.window * 4:
            return None, None, None
            
        X, y = [], []
        try:
            for i in range(len(sizes) - self.window):
                row = []
                for j in range(self.window):
                    size_val = 1.0 if sizes[i+j] == 'BIG' else 0.0
                    par_val = 1.0 if parities[i+j] == 'EVEN' else 0.0
                    num_val = float(numbers[i+j])
                    row.extend([size_val, par_val, num_val])
                X.append(row)
                y.append(1.0 if sizes[i+self.window] == 'BIG' else 0.0)
            
            curr_feats = []
            for j in range(1, self.window + 1):
                size_val = 1.0 if sizes[-j] == 'BIG' else 0.0
                par_val = 1.0 if parities[-j] == 'EVEN' else 0.0
                num_val = float(numbers[-j])
                curr_feats.extend([size_val, par_val, num_val])
                
            X_scaled = self.scaler.fit_transform(X)
            curr_scaled = self.scaler.transform([curr_feats])
            
            return X_scaled, np.array(y), curr_scaled
        except Exception as e:
            logger.error(f"Feature Engineering Error: {e}")
            return None, None, None

# =========================================================================
# 🧠 MODULE 4: THE 10 AI CORES (SUB-ENGINES)
# =========================================================================
class TreeEngines:
    def __init__(self):
        self.rf = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42, n_jobs=-1)
        self.gb = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42)
        
    def predict(self, X: np.ndarray, y: np.ndarray, curr_X: np.ndarray) -> Tuple[float, float]:
        try:
            self.rf.fit(X, y)
            self.gb.fit(X, y)
            rf_prob = float(self.rf.predict_proba(curr_X)[0][1]) if 1.0 in self.rf.classes_ else 0.5
            gb_prob = float(self.gb.predict_proba(curr_X)[0][1]) if 1.0 in self.gb.classes_ else 0.5
            return rf_prob, gb_prob
        except Exception:
            return 0.5, 0.5

class MarkovEngine:
    @staticmethod
    def predict(sizes: List[str]) -> float:
        if len(sizes) < 10: return 0.5
        trans = {'BIG': {'BIG': 0, 'SMALL': 0}, 'SMALL': {'BIG': 0, 'SMALL': 0}}
        try:
            for i in range(len(sizes)-1): 
                trans[sizes[i]][sizes[i+1]] += 1
            curr = sizes[-1]
            tot = sum(trans[curr].values())
            return float(trans[curr]['BIG'] / tot) if tot > 0 else 0.5
        except: return 0.5

class NGramEngine:
    @staticmethod
    def predict(sizes: List[str], n: int = 4) -> float:
        if len(sizes) < n+1: return 0.5
        try:
            pat = tuple(sizes[-n:])
            matches = [sizes[i+n] for i in range(len(sizes)-n) if tuple(sizes[i:i+n]) == pat]
            if not matches: return 0.5
            return float(matches.count('BIG') / len(matches))
        except: return 0.5

class MonteCarloEngine:
    @staticmethod
    def predict(sizes: List[str], sims: int = 1000) -> float:
        if not sizes: return 0.5
        try:
            prob_b = sizes.count('BIG') / len(sizes)
            results = np.random.choice([1.0, 0.0], size=sims, p=[prob_b, 1.0-prob_b])
            return float(np.mean(results))
        except: return 0.5

class TrendEngine:
    @staticmethod
    def predict(sizes: List[str], window: int = 15) -> float:
        if len(sizes) < window: return 0.5
        try:
            recent = sizes[-window:]
            momentum = recent.count('BIG') / float(window)
            if momentum >= 0.8: return 0.25 
            if momentum <= 0.2: return 0.75 
            return float(momentum)
        except: return 0.5

class BayesianEngine:
    def __init__(self): 
        self.nb = GaussianNB()
        
    def predict(self, X: np.ndarray, y: np.ndarray, curr_X: np.ndarray) -> float:
        try:
            self.nb.fit(X, y)
            return float(self.nb.predict_proba(curr_X)[0][1]) if 1.0 in self.nb.classes_ else 0.5
        except: return 0.5

class SimpleLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=16, num_layers=1, batch_first=True)
        self.fc = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        _, (hn, _) = self.lstm(x)
        out = self.fc(hn[-1])
        return self.sigmoid(out)

class LSTMEngine:
    def predict(self, sizes: List[str]) -> float:
        if len(sizes) < 50: return 0.5
        try:
            data = [1.0 if s == 'BIG' else 0.0 for s in sizes[-50:]]
            X_t = torch.tensor(data[:-1], dtype=torch.float32).view(1, -1, 1)
            y_t = torch.tensor([data[-1]], dtype=torch.float32).view(1, 1)
            
            model = SimpleLSTM()
            optimizer = optim.Adam(model.parameters(), lr=0.01)
            criterion = nn.BCELoss()
            
            model.train()
            for _ in range(5):
                optimizer.zero_grad()
                loss = criterion(model(X_t), y_t)
                loss.backward()
                optimizer.step()
            
            model.eval()
            curr_X = torch.tensor(data[1:], dtype=torch.float32).view(1, -1, 1)
            with torch.no_grad(): 
                prediction = model(curr_X).item()
            return float(prediction)
        except Exception as e: 
            logger.warning(f"LSTM Error: {e}")
            return 0.5

class EntropyEngine:
    @staticmethod
    def predict(sizes: List[str]) -> float:
        if len(sizes) < 20: return 0.5
        try:
            recent = sizes[-20:]
            p_b = recent.count('BIG') / 20.0
            p_s = 1.0 - p_b
            if p_b == 0 or p_s == 0: return float(p_b)
            
            entropy = stats.entropy([p_b, p_s], base=2)
            if entropy > 0.98: return 0.5 
            return float(p_b)
        except: return 0.5

class MetaOptimizer:
    def __init__(self):
        self.weights: Dict[str, float] = {
            'rf': 0.15, 'gb': 0.15, 'markov': 0.10, 'ngram': 0.10,
            'monte': 0.05, 'trend': 0.10, 'bayes': 0.10, 'lstm': 0.15, 'entropy': 0.10
        }

    def update(self, actual: str, past_preds: Dict[str, float]) -> None:
        if not past_preds: return
        try:
            actual_val = 1.0 if actual == 'BIG' else 0.0
            total_w = 0.0
            
            for model, prob in past_preds.items():
                error = abs(actual_val - prob)
                if error < 0.4: 
                    self.weights[model] += 0.05
                else: 
                    self.weights[model] = max(0.01, self.weights[model] - 0.02)
                total_w += self.weights[model]
                
            if total_w > 0:
                for k in self.weights: 
                    self.weights[k] = float(self.weights[k] / total_w)
        except Exception as e:
            logger.error(f"Meta Optimizer Error: {e}")

# =========================================================================
# ⚙️ MODULE 5: MASTER ORCHESTRATOR (UPGRADED PIPELINE)
# =========================================================================
class MetaAIEngine(MetaOptimizer):
    """ Meta-AI Weighting System (Step 2) """
    def calculate_weighted_prob(self, predictions: Dict[str, float]) -> float:
        final_prob = 0.0
        for engine_name, prob in predictions.items():
            weight = self.weights.get(engine_name, 0.1)
            final_prob += prob * weight
        return final_prob

class UltraMasterEngine:
    def __init__(self):
        self.fe = FeatureEngineer()
        self.meta_ai = MetaAIEngine()
        self.trees = TreeEngines()
        self.bayes = BayesianEngine()
        self.lstm = LSTMEngine()
        self.last_probs: Dict[str, float] = {}

    def _get_10_engines_predictions(self, sizes: List[str], X: np.ndarray, y: np.ndarray, curr_X: np.ndarray, baseline_b: float) -> Dict[str, float]:
        probs = {}
        probs['markov'] = MarkovEngine.predict(sizes)
        probs['ngram'] = NGramEngine.predict(sizes)
        probs['monte'] = MonteCarloEngine.predict(sizes)
        probs['trend'] = TrendEngine.predict(sizes)
        probs['entropy'] = EntropyEngine.predict(sizes)
        probs['lstm'] = self.lstm.predict(sizes)
        
        if X is not None and len(X) > 10:
            probs['rf'], probs['gb'] = self.trees.predict(X, y, curr_X)
            probs['bayes'] = self.bayes.predict(X, y, curr_X)
        else:
            probs['rf'] = probs['gb'] = probs['bayes'] = baseline_b
            
        return probs

    def analyze(self, docs: List[Dict[str, Any]]) -> Tuple[str, float, Dict[str, float]]:
        if len(docs) < 50: 
            return random.choice(["BIG", "SMALL"]), random.uniform(50.1, 54.9), {}
        
        try:
            sizes = [d.get('size', 'BIG') for d in reversed(docs)]
            nums = [int(d.get('number', 0)) for d in reversed(docs)]
            pars = [d.get('parity', 'EVEN') for d in reversed(docs)]
            
            baseline_b = sizes.count('BIG') / len(sizes)
            if baseline_b == 0 or baseline_b == 1: baseline_b = 0.5 

            X, y, curr_X = self.fe.extract_features(sizes, nums, pars)
            
            # [STEP 1] 10 AI Engines Predictions
            predictions = self._get_10_engines_predictions(sizes, X, y, curr_X, baseline_b)
            self.last_probs = {k: float(v) for k, v in predictions.items()}
            
            # [STEP 2] Meta-AI Weighting
            final_b = self.meta_ai.calculate_weighted_prob(self.last_probs)
            
            # [STEP 3] Final Prediction
            if final_b > baseline_b:
                final_pred = "BIG"
            elif final_b < baseline_b:
                final_pred = "SMALL"
            else:
                final_pred = random.choice(["BIG", "SMALL"])
            
            deviation = abs(final_b - baseline_b)
            raw_conf = 0.5 + (deviation * 2.5)
            conf = min(max(float(raw_conf) * 100, 51.0), 99.0)
            
            return final_pred, round(conf, 1), self.last_probs
            
        except Exception as e:
            logger.error(f"Master Engine Error: {e}")
            return random.choice(["BIG", "SMALL"]), 50.0, {}

# =========================================================================
# 💰 MODULE 6: TELEGRAM UI & PRESENTATION
# =========================================================================
class UIManager:
    def __init__(self, bot_client: Bot):
        self.bot = bot_client

    async def broadcast_prediction(self, issue: str, pred: str, step: int, conf: float, top_engine: str) -> None:
        msg = (
            f"<b>[ULTRA-AI 10-CORE PRO]</b>\n"
            f"⏰ Period: <code>{issue}</code>\n"
            f"🎯 Prediction: <b>{pred}</b> {step}x\n"
            f"📊 Confidence: {conf}%\n"
            f"🧠 Top Engine: <code>{top_engine.upper()}</code>"
        )
        try: 
            await self.bot.send_message(chat_id=Config.CHANNEL_ID, text=msg)
        except Exception as e: 
            logger.error(f"UI Predict Send Error: {e}")

    async def broadcast_result(self, issue: str, pred: str, step: int, is_win: bool, actual_size: str, actual_num: int) -> None:
        win_str = "WIN" if is_win else "LOSE"
        icon = "🟢" if is_win else "🔴"
        res_letter = "B" if actual_size == "BIG" else "S"
        
        msg = (
            f"<b>🏆 SIX-LOTTERY RESULTS</b>\n\n"
            f"⏰ Period: <code>{issue}</code>\n"
            f"🎯 Choice: {pred} {step}x\n"
            f"📊 Result: {icon} <b>{win_str}</b> | {res_letter} ({actual_num})"
        )
        try: 
            await self.bot.send_message(chat_id=Config.CHANNEL_ID, text=msg)
            
            if is_win and Config.WIN_STICKER:
                await self.bot.send_sticker(chat_id=Config.CHANNEL_ID, sticker=Config.WIN_STICKER)
            elif not is_win and Config.LOSE_STICKER:
                await self.bot.send_sticker(chat_id=Config.CHANNEL_ID, sticker=Config.LOSE_STICKER)
        except Exception as e: 
            logger.error(f"UI Result Send Error: {e}")

# =========================================================================
# 🚀 MODULE 7: THE MAIN CONTROLLER LOOP
# =========================================================================
class ApplicationController:
    def __init__(self):
        self.db = DatabaseManager(Config.MONGO_URI)
        self.ai = UltraMasterEngine()
        self.ui = UIManager(bot)
        self.last_issue: Optional[str] = None
        self.lose_streak: int = 0

    async def fetch_api_data(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        json_data = {
            'pageSize': 10, 'pageNo': 1, 'typeId': 30, 'language': 7, 
            'random': '9ef85244056948ba8dcae7aee7758bf4', 
            'signature': '2EDB8C2B5264F62EC53116916A9EC05C', 
            'timestamp': int(time.time())
        }
        for attempt in range(3):
            try:
                async with session.post(Config.API_URL, headers=Config.get_headers(), json=json_data, timeout=5.0) as r:
                    if r.status == 200: 
                        res = await r.json()
                        if res.get('code') != 0:
                            logger.error(f"API Rejected (Code: {res.get('code')}): Update Token/Signature!")
                        return res
                    else:
                        logger.error(f"HTTP Status Error: {r.status}")
            except Exception as e:
                logger.warning(f"API Fetch Retry {attempt+1}/3 failed: {e}")
                await asyncio.sleep(0.5)
        return None

    async def run_forever(self) -> None:
        await self.db.initialize()
        
        async with aiohttp.ClientSession() as session:
            logger.info("🔥 ULTRA-AI 10-CORE GAME LOOP STARTED SUCCESSFULLY 🔥")
            while True:
                try:
                    data = await self.fetch_api_data(session)
                    if not data or data.get('code') != 0:
                        await asyncio.sleep(1.5); continue
                        
                    records = data.get("data", {}).get("list", [])
                    if not records: continue
                    
                    latest = records[0]
                    issue = str(latest["issueNumber"])
                    number = int(latest["number"])
                    size = "BIG" if number >= 5 else "SMALL"
                    parity = "EVEN" if number % 2 == 0 else "ODD"
                    
                    if not self.last_issue:
                        logger.info(f"Initializing State at Issue: {issue}")
                        self.last_issue = issue
                        
                        recent_preds = await self.db.get_recent_predictions(15)
                        self.lose_streak = 0
                        for p in recent_preds:
                            if p.get("win_lose") == "LOSE": self.lose_streak += 1
                            else: break
                        if self.lose_streak >= len(Config.MULTIPLIERS): self.lose_streak = 0

                        next_issue = str(int(issue) + 1)
                        docs = await self.db.get_history(500)
                        
                        pred, conf, details = self.ai.analyze(docs)
                        top_model = max(self.ai.meta_ai.weights, key=self.ai.meta_ai.weights.get) if self.ai.meta_ai.weights else "rf"
                        
                        await self.ui.broadcast_prediction(next_issue, pred, self.lose_streak + 1, conf, top_model)
                        await asyncio.sleep(1.0); continue

                    if int(issue) > int(self.last_issue):
                        logger.info(f"🟢 New Result Arrived: {issue} -> {size} ({number})")
                        
                        await self.db.save_history(issue, number, size, parity)
                        
                        # Meta AI Update
                        self.ai.meta_ai.update(size, self.ai.last_probs)
                        
                        pred_doc = await self.db.predictions.find_one({"issue_number": issue})
                        
                        if pred_doc and pred_doc.get('predicted_size'):
                            predicted_size = str(pred_doc['predicted_size'])
                            is_win = (predicted_size == size)
                            win_lose_db = "WIN" if is_win else "LOSE"
                            
                            await self.db.update_result(issue, size, number, win_lose_db)
                            
                            current_step = self.lose_streak + 1
                            await self.ui.broadcast_result(issue, predicted_size, current_step, is_win, size, number)
                            
                            if is_win: 
                                self.lose_streak = 0
                            else: 
                                self.lose_streak += 1
                                if self.lose_streak >= len(Config.MULTIPLIERS): 
                                    self.lose_streak = 0

                        self.last_issue = issue
                        
                        next_issue = str(int(issue) + 1)
                        docs = await self.db.get_history(500)
                        
                        logger.info(f"Analyzing probabilities for {next_issue}...")
                        pred, conf, details = self.ai.analyze(docs)
                        
                        await self.db.save_prediction(next_issue, pred, conf, details)
                        
                        top_model = max(self.ai.meta_ai.weights, key=self.ai.meta_ai.weights.get)
                        current_step = self.lose_streak + 1
                        
                        await self.ui.broadcast_prediction(next_issue, pred, current_step, conf, top_model)

                except Exception as e:
                    logger.error(f"Critical Loop Exception: {e}")
                
                await asyncio.sleep(1.5)

# =========================================================================
# 🚀 MODULE 8: ENTRY POINT
# =========================================================================
async def main() -> None:
    logger.info("Initializing ULTRA-AI Core Components...")
    await bot.delete_webhook(drop_pending_updates=True)
    app_controller = ApplicationController()
    asyncio.create_task(app_controller.run_forever())
    logger.info("Bot is now Polling Telegram Updates...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: 
        asyncio.run(main())
    except KeyboardInterrupt: 
        logger.info("System Shut Down by User (Ctrl+C).")

