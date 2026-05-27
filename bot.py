import requests
import time
import schedule
import threading
import sqlite3
import re
import os
from flask import Flask

from features.whale_analysis import fetch_whale_institutional_data
from features.order_flow import analyze_order_flow_exhaustion

app = Flask('')

@app.route('/')
def home():
    return "🔥 Ultra Pro Max AI Trading Engine is Live & Running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== আপনার সেটিংস ====================
TOKEN = "8808545994:AAG8fmbjQEKlENq2BYrk2SVCVM1wu9eWuEk"
USER_CHAT_ID = None # আপনার চ্যাট আইডি জানা না থাকলে অটো খুঁজে নেবে
# ====================================================

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
        if rows: return True
    except: pass
    return False

def save_signal(pair, direction, entry_price):
    try:
        conn = sqlite3.connect('trading_memory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO signals (pair, direction, entry_price, timestamp) VALUES (?, ?, ?, ?)', 
                       (str(pair), str(direction), str(entry_price), time.time()))
        conn.commit()
        conn.close()
    except: pass

def get_telegram_chat_id():
    if USER_CHAT_ID: return USER_CHAT_ID
    try:
        res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=10).json()
        if res.get("result"):
            return res["result"][-1]["message"]["chat"]["id"]
    except: pass
    return None

def send_instant_test_message(chat_id):
    if not chat_id: return
    msg = "🎉 *ভাই রে! আপনার আল্ট্রা লেভেলের নতুন কোডটি এখন সার্ভার থেকে সফলভাবে লাইভ হয়েছে। এখন থেকে রিয়েল-টাইম ডাটা স্ক্যান করা শুরু হলো!*"
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def send_institutional_alert(pair, direction, entry, tp, sl, reason):
    chat_id = get_telegram_chat_id()
    if not chat_id: return
    
    status_emoji = "🟢 INSTITUTIONAL LONG (BUY)" if direction == "BUY" else "🚨 INSTITUTIONAL SHORT (SELL)"
    
    message = (
        f"👑 *ULTRA LEVEL INSTITUTIONAL SIGNAL* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 *Asset/Pair:* {pair}\n"
        f"📈 *Position:* {status_emoji}\n"
        f"🎯 *Entry Price:* {entry}\n"
        f"💰 *Take Profit:* {tp}\n"
        f"🛑 *Stop Loss:* {sl}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Orderbook Matrix:* {reason}"
    )
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    except: pass

def run_institutional_engine():
    print(f"🔄 [{time.strftime('%X')}] স্ক্যানিং ওর্ডার বুক ও লিকুইডেশন ডাটা...")
    try:
        watch_list = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        for symbol in watch_list:
            ticker_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            try:
                current_price = float(requests.get(ticker_url, timeout=10).json()['price'])
            except: continue
            
            # ১. লিকুইডেশন চেক
            condition, reason_msg = fetch_whale_institutional_data(symbol)
            
            # ২. ওর্ডারফ্লো চেক
            if not condition:
                condition, reason_msg = analyze_order_flow_exhaustion(symbol)
                
            if not condition: continue
                
            direction = "BUY" if "BUY" in condition or "BULLISH" in reason_msg else "SELL"
            
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
                print(f"🔥 [SIGNAL SENT] {symbol} প্রাতিষ্ঠানিক সিগন্যাল পাঠানো হয়েছে!")
                break
    except Exception as e:
        print(f"⚠️ ইঞ্জিন এরর: {e}")

# প্রতি ২ মিনিটে লাইভ ডাটা স্ক্যান করবে
schedule.every(2).minutes.do(run_institutional_engine)

if __name__ == "__main__":
    init_db()
    
    # সাথে সাথে টেস্ট মেসেজ পাঠানো হবে
    found_id = get_telegram_chat_id()
    if found_id:
        send_instant_test_message(found_id)
        
    run_web_server()