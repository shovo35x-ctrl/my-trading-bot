import requests
import time
import schedule
import threading
import sqlite3
import re
import os
from flask import Flask

# মডুলার আর্কিটেকচার থেকে আল্ট্রা লেভেলের দুটি ইঞ্জিন ইমপোর্ট
from features.whale_analysis import fetch_whale_institutional_data
from features.order_flow import analyze_order_flow_exhaustion

app = Flask('')

@app.route('/')
def home():
    return "🔥 Institutional Ultra Pro Max AI Trading Engine is 100% Operational!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== সিকিউরড কনফিগারেশন ====================
TOKEN = "8808545994:AAG8fmbjQEKlENq2BYrk2SVCVM1wu9eWuEk"
USER_CHAT_ID = None 
COINGLASS_API_KEY = "OPTIONAL_KEY_HERE"  # আপনার কি থাকলে বসাবেন, না থাকলে বট অটো ব্যাকআপে চলবে
# ==========================================================

def init_db():
    conn = sqlite3.connect('trading_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT,
            direction TEXT,
            entry_price TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    conn.close()

def is_duplicate_trade(pair, current_price):
    try:
        conn = sqlite3.connect('trading_memory.db')
        cursor = conn.cursor()
        ten_mins_ago = time.time() - 600
        cursor.execute('SELECT entry_price FROM signals WHERE pair=? AND timestamp > ?', (str(pair), ten_mins_ago))
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            old_p = float(re.sub(r"[^\d\.]", "", str(row)))
            curr_p = float(re.sub(r"[^\d\.]", "", str(current_price)))
            if abs(old_p - curr_p) / old_p < 0.0008: # হাইপার স্কাল্পিং ফিল্টার
                return True
    except:
        pass
    return False

def save_signal(pair, direction, entry_price):
    try:
        conn = sqlite3.connect('trading_memory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO signals (pair, direction, entry_price, timestamp) VALUES (?, ?, ?, ?)', 
                       (str(pair), str(direction), str(entry_price), time.time()))
        conn.commit()
        conn.close()
    except:
        pass

def get_telegram_chat_id():
    if USER_CHAT_ID: return USER_CHAT_ID
    try:
        res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=10).json()
        if res.get("result"):
            return res["result"][-1]["message"]["chat"]["id"]
    except: pass
    return None

def send_institutional_alert(pair, direction, entry, tp, sl, reason):
    chat_id = get_telegram_chat_id()
    if not chat_id: return
    
    status_emoji = "🟢 INSTITUTIONAL LONG (BUY)" if direction == "BUY" else "🚨 INSTITUTIONAL SHORT (SELL)"
    
    message = (
        f"👑 *ULTRA LEVEL INSTITUTIONAL SIGNAL* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 *Asset/Pair:* {pair} (Crypto/Gold Feed)\n"
        f"📈 *Position:* {status_emoji}\n"
        f"🎯 *Entry Price:* {entry}\n"
        f"💰 *Take Profit:* {tp}\n"
        f"🛑 *Stop Loss:* {sl}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Orderbook Matrix:* {reason}\n"
        f"🤖 *System Status:* 100% Verified Trade Alignment"
    )
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"टেলিগ্রাম সেন্ড এরর: {e}")

def run_institutional_engine():
    print(f"\n🔄 [{time.strftime('%X')}] স্ক্যানিং ইনস্টিটিউশনাল ওর্ডার বুক ও লিকুইডেশন ডাটা...")
    try:
        # ক্রিপ্টো এবং মেটাল ট্র্যাকিং এর জন্য গ্লোবাল ওয়াচলিস্ট
        watch_list = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        for symbol in watch_list:
            # কারেন্ট প্রাইজ ফিড নেওয়া
            ticker_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            try:
                current_price = float(requests.get(ticker_url, timeout=10).json()['price'])
            except: continue
            
            condition, reason_msg = fetch_whale_institutional_data(symbol, COINGLASS_API_KEY)
            
            if not condition:
                condition, reason_msg = analyze_order_flow_exhaustion(symbol, COINGLASS_API_KEY)
                
            if not condition:
                print(f" 🔍 {symbol}: মার্কেট ভলিউম ব্যালেন্সড। নো প্রাতিষ্ঠানিক মুভমেন্ট।")
                continue
                
            direction = "BUY" if "BUY" in condition else "SELL"
            
            # আল্ট্রা প্রফেশনাল স্কাল্পিং রেশিও (RR - 1:2)
            if direction == "BUY":
                tp = current_price * 1.0030  
                sl = current_price * 0.9985  
            else:
                tp = current_price * 0.9970
                sl = current_price * 1.0015
                
            entry_str = f"${current_price:,.2f}"
            tp_str = f"${tp:,.2f}"
            sl_str = f"${sl:,.2f}"
            
            if not is_duplicate_trade(symbol, entry_str):
                save_signal(symbol, direction, entry_str)
                send_institutional_alert(symbol, direction, entry_str, tp_str, sl_str, reason_msg)
                print(f"🔥 [SIGNAL SENT] {symbol} প্রাতিষ্ঠানিক সিগন্যাল টেলিগ্রামে পাঠানো হয়েছে!")
                break
    except Exception as e:
        print(f"⚠️ ইঞ্জিন এক্সেপশন অ্যালার্ট: {e}")

# প্রতি ১ মিনিটে লাইভ ডাটা রিফ্রেশ ও স্ক্যানিং
schedule.every(1).minutes.do(run_institutional_engine)

if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔥 [SYSTEM LIVE] ULTRA PRO MAX INSTITUTIONAL BOT IS RUNNING...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    init_db()
    run_institutional_engine()
    
    def start_loop():
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    t = threading.Thread(target=start_loop, daemon=True)
    t.start()
    run_web_server()