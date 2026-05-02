from telethon import TelegramClient, events
import json, os, re, asyncio, datetime, random
import aiohttp
import aiofiles

# ================== CONFIG ==================
API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

OWNER_ID = 7077294261

# ================== YOUR PROXIES ==================
PROXIES = [
    "dc.oxylabs.io:8000:harshop01_6Mzjy:V=DMlz+qMinV_n85",
    "px490402.pointtoserver.com:10780:purevpn0s8732217:i67s60ep"
]

# ================== CHECKER WITH PROXY ==================
async def check_weanimals(card: str):
    try:
        cc, mm, yy, cvv = [x.strip() for x in card.split('|')]
        if len(yy) == 2: yy = "20" + yy

        await asyncio.sleep(random.uniform(5, 8))

        # Rotate Proxy
        proxy_str = random.choice(PROXIES)
        proxy_url = f"http://{proxy_str.split(':')[2]}:{proxy_str.split(':')[3]}@{proxy_str.split(':')[0]}:{proxy_str.split(':')[1]}"

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        async with aiohttp.ClientSession() as session:
            async with session.get("https://weanimalsmedia.org/support-our-work", proxy=proxy_url, headers=headers) as r:
                html = await r.text()

            # Simulate checker for now
            if random.randint(1, 100) <= 20:
                return {"Response": "✅ LIVE HIT (Proxy)", "Status": "Approved"}
            else:
                return {"Response": "Declined", "Status": "Declined"}

    except Exception as e:
        return {"Response": "Proxy Error", "Status": "Declined"}


# ================== BOT ==================
client = TelegramClient('weanimals_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    await event.reply("**WeAnimals Media Checker with Proxy**")

@client.on(events.NewMessage())
async def txt_handler(event):
    if not event.document or not str(event.file.name).lower().endswith('.txt'):
        return

    await event.reply("📂 Processing TXT file with Proxy...")
    path = f"temp_{event.sender_id}.txt"
    await event.download_media(path)

    cards = []
    async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = await f.read()
        found = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', content)
        for c in found:
            cleaned = re.sub(r'[^0-9|]', '',
