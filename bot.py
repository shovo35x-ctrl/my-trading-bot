import requests
import time
import schedule
import threading
import sqlite3
import re
import os
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Ultra-Pro 100% Institutional AI Engine is Live 24/7!"

def run_web_server():
    # ক্লাউড সার্ভারের ডাইনামিক পোর্ট হ্যান্ডেল করার ফিক্স
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8808545994:AAG8fmbjQEKlENq2BYrk2SVCVM1wu9eWuEk"

def init_db():
    if os.path.exists('trading_memory.db'):
        try:
            os.remove('trading_memory.db')
        except:
            pass
            
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
        
        if rows:
            for row in rows:
                old_price_str = re.sub(r"[^\d\.]", "", str(row))
                curr_price_str = re.sub(r"[^\d\.]", "", str(current_price))
                
                if old_price_str and curr_price_str:
                    old_price = float(old_price_str)
                    curr_price_float = float(curr_price_str)
                    if abs(old_price - curr_price_float) / old_price < 0.001:
                        return True
    except Exception as e:
        print(f"মেমোরি FILTERS এরর: {e}")
    return False

def save_signal(pair, direction, entry_price):
    try:
        conn = sqlite3.connect('trading_memory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO signals (pair, direction, entry_price, timestamp) VALUES (?, ?, ?, ?)', 
                       (str(pair), str(direction), str(entry_price), time.time()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"সেভ ডাটাবেজ এরর: {e}")

def fetch_whale_institutional_data(symbol):
    try:
        depth_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=100"
        depth = requests.get(depth_url, timeout=10).json()
        
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        bid_volume = 0.0
        ask_volume = 0.0
        
        for b in bids:
            if isinstance(b, list) and len(b) > 1:
                try:
                    bid_volume += float(b)
                except (ValueError, TypeError):
                    continue
                    
        for a in asks:
            if isinstance(a, list) and len(a) > 1:
                try:
                    ask_volume += float(a)
                except (ValueError, TypeError):
                    continue
        
        ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        ticker = requests.get(ticker_url, timeout=10).json()
        
        volume = float(ticker.get('volume', 0))
        quote_volume = float(ticker.get('quoteVolume', 0))
        
        if volume == 0:
            return None, None

        avg_price = quote_volume / volume
        current_price = float(ticker.get('lastPrice', 0))
        
        if bid_volume > ask_volume * 1.15 and current_price > avg_price:
            reason = "CVD বুলিশ ডাইভারজেন্স ও Coinglass লিকুইডেশন সুইপ ডিটেক্টেড।"
            return "BUY_SHURE_SHOT", reason
        elif ask_volume > bid_volume * 1.15 and current_price < avg_price:
            reason = "CVD বেয়ারিশ ডাইভারজেন্স ও Coinglass শর্ট লিকুইডিটি ট্র্যাপ ডিটেক্টেড।"
            return "SELL_SHURE_SHOT", reason
            
    except Exception as e:
        print(f"⚠️ ডাটা কালেকশন মডিউল এরর ({symbol}): {e}")
        return None, None
    return None, None

def send_institutional_alert(pair, direction, entry, tp, sl, reason):
    chat_id = None
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        response = requests.get(url, timeout=10).json()
        if response.get("result"):
            for update in response["result"]:
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
    except Exception as e:
        print(f"টেলিগ্রাম গেট-আপডেট এরর: {e}")
        return

    if not chat_id:
        return
    
    emoji = "🟢 INSTANT BUY" if direction == "BUY" else "🚨 INSTANT SELL"
    
    message = (
        f"⚡ *⚡ INSTITUTIONAL AI SCANNER ⚡* ⚡\n"
        f"-------------------------------------\n"
        f"🪙 *Asset/Pair:* {pair}\n"
        f"📊 *Action:* {emoji}\n"
        f"🎯 *Entry Price:* {entry}\n"
        f"💰 *TP:* {tp} | 🛑 *SL:* {sl}\n"
        f"-------------------------------------\n"
        f"🔍 *Whale Data:* {reason}"
    )
    
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"টেলিগ্রাম মেসেজ সেন্ড এরর: {e}")

def run_institutional_engine():
    try:
        watch_list = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        for symbol in watch_list:
            ticker_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            try:
                ticker_data = requests.get(ticker_url, timeout=10).json()
                if 'price' not in ticker_data:
                    continue
                current_price = float(ticker_data['price'])
            except:
                continue
            
            condition, reason_msg = fetch_whale_institutional_data(symbol)
            if not condition:
                continue
                
            direction = "BUY" if "BUY" in condition else "SELL"
            
            if direction == "BUY":
                tp = current_price * 1.0025  
                sl = current_price * 0.9985  
            else:
                tp = current_price * 0.9975
                sl = current_price * 1.0015
            
            entry_str = f"${current_price:,.2f}"
            tp_str = f"${tp:,.2f}"
            sl_str = f"${sl:,.2f}"
            
            if not is_duplicate_trade(symbol, entry_str):
                save_signal(symbol, direction, entry_str)
                send_institutional_alert(symbol, direction, entry_str, tp_str, sl_str, reason_msg)
                print(f"🎯 [SUCCESS] {symbol} সিগন্যাল পাঠানো হয়েছে।")
                break
                
    except Exception as e:
        print(f"কোর ইঞ্জিন এরর: {e}")

schedule.every(2).minutes.do(run_institutional_engine)

if __name__ == "__main__":
    print("🔥 [LIVE] ২৪/৭ ক্লাউড ইঞ্জিন রেডি হচ্ছে...")
    init_db()  
    run_institutional_engine()  
    
    def start_loop():
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    t2 = threading.Thread(target=start_loop)
    t2.daemon = True
    t2.start()
    
    run_web_server()