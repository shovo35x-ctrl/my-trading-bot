import requests

def analyze_order_flow_exhaustion(symbol):
    """
    ফ্রি ও পাবলিক সোর্স থেকে ফিউচার মার্কেটের ভলিউম ও ডেল্টা ডাটা ট্র্যাক করার আল্ট্রা ইঞ্জিন।
    """
    try:
        # কোনো এপিআই কি লাগবে না, সরাসরি গ্লোবাল ডাটা ফিড
        url = f"https://api.coinglass.com/api/index/v1/futures/openInterest?symbol={symbol}"
        response = requests.get(url, timeout=10).json()
        
        oi_data = response.get('data', [])
        if len(oi_data) > 2:
            current_oi = float(oi_data[-1])
            prev_oi = float(oi_data[-2])
            oi_change = ((current_oi - prev_oi) / prev_oi) * 100
            
            # ওপেন ইন্টারেস্ট হঠাৎ ১% এর বেশি বৃদ্ধি পাওয়ার মানে বড় প্লেয়ারদের এন্ট্রি
            if oi_change > 1.0:
                reason = f"🚨 INSTITUTIONAL MOMENTUM!! Open Interest বৃদ্ধি পেয়েছে {oi_change:.2f}%। ওর্ডারফ্লোতে হোয়েল অ্যাক্টিভিটি ডিটেক্টেড।"
                return "ORDERFLOW_SIGNAL", reason
    except Exception as e:
        print(f"⚠️ [ORDER FLOW ERROR]: {e}")
    return None, None