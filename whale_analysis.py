import requests

def fetch_whale_institutional_data(symbol):
    """
    পাবলিক সোর্স থেকে রিয়েল-টাইম লিকুইডেশন হিটম্যাপ ও ভলিউম ডেটা ট্র্যাকিং।
    """
    try:
        # সম্পূর্ণ ওপেন এবং ফ্রি লিকুইডেশন ডাটা সোর্স
        url = "https://api.coinglass.com/api/index/v1/liq/v2/home"
        response = requests.get(url, timeout=10).json()
        
        for item in response.get('data', {}).get('list', []):
            if item.get('symbol', '').upper() == symbol.upper():
                shorts = float(item.get('shortVolUsd', 0))
                longs = float(item.get('longVolUsd', 0))
                
                # যদি একদিকের লিকুইডেশন অন্যদিকের চেয়ে দ্বিগুণ হয়ে যায় (লিকুইডেশন সুইপ)
                if longs > shorts * 1.8 and longs > 100000:
                    reason = f"🔥 LONG LIQUIDATION SWEEP!! ${longs:,.2f} লং পজিশন ধুয়ে মুছে সাফ। হোয়েলরা সস্তায় বাই করছে।"
                    return "BUY_SHURE_SHOT", reason
                elif shorts > longs * 1.8 and shorts > 100000:
                    reason = f"🚨 SHORT LIQUIDATION TRAP!! ${shorts:,.2f} শর্ট পজিশন লিকুইডেট। মার্কেট রিভার্সাল পসিবল।"
                    return "SELL_SHURE_SHOT", reason
    except Exception as e:
        print(f"⚠️ [WHALE ENGINE ERROR]: {e}")
    return None, None