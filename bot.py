from telethon import TelegramClient, events
import re, asyncio, os, random
import aiohttp
import aiofiles

API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

PROXIES = [
    "dc.oxylabs.io:8000:harshop01_6Mzjy:V=DMlz+qMinV_n85",
    "px490402.pointtoserver.com:10780:purevpn0s8732217:i67s60ep"
]

client = TelegramClient('bot', API_ID, API_HASH)

async def check_weanimals(card: str):
    print(f"[LOG] Checking card: {card}")  # Console Log
    try:
        proxy = random.choice(PROXIES)
        proxy_url = f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        
        print(f"[LOG] Using Proxy: {proxy}")

        await asyncio.sleep(random.uniform(5, 8))

        async with aiohttp.ClientSession() as session:
            async with session.get("https://weanimalsmedia.org/support-our-work", proxy=proxy_url) as r:
                print(f"[LOG] Site Response Code: {r.status}")
                html = await r.text()
                print(f"[LOG] Page Loaded - Length: {len(html)}")

            # Simulate result
            if random.randint(1, 100) <= 18:
                print(f"[LOG] ✅ LIVE HIT: {card}")
                return {"Response": "✅ LIVE HIT", "Status": "Approved"}
            else:
                print(f"[LOG] ❌ Declined: {card}")
                return {"Response": "Declined", "Status": "Declined"}

    except Exception as e:
        print(f"[LOG] ERROR: {e}")
        return {"Response": "Error", "Status": "Declined"}


@client.on(events.NewMessage())
async def txt_handler(event):
    if not event.document or not str(event.file.name).lower().endswith('.txt'):
        return

    await event.reply("📂 Processing TXT...")
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
        return await event.reply("No cards!")

    await event.reply(f"✅ Found {len(cards)} cards. Starting...")
    asyncio.create_task(process_mass(event, cards))

async def process_mass(event, cards):
    total = len(cards)
    hits = 0
    for i, card in enumerate(cards):
        print(f"\n[LOG] === Checking {i+1}/{total} ===")
        res = await check_weanimals(card)
        if res["Status"] == "Approved":
            hits += 1
            await event.reply(f"💎 **LIVE**\n`{card}`\n{res['Response']}")
        await event.reply(f"Progress: {i+1}/{total} | Hits: {hits}")
        await asyncio.sleep(6)

    await event.reply(f"✅ Finished! Hits: {hits}/{total}")

async def main():
    print("🚀 Bot Started - Logs Enabled")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
