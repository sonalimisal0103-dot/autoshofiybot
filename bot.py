from telethon import TelegramClient, events, Button
from telethon.tl.types import KeyboardButtonCallback
import requests, random, datetime, json, os, re, asyncio, time
import string
import aiohttp
import aiofiles
from urllib.parse import urlparse
import sys
import logging

logging.basicConfig(level=logging.INFO)

# ==================== PROXY CONFIG ====================
# Proxy 1: PureVPN
PROXY1 = {
    'proxy_type': 'socks5',
    'addr': 'px490402.pointtoserver.com',
    'port': 10780,
    'username': 'purevpn0s8732217',
    'password': 'i67s60ep',
    'rdns': True
}

# Proxy 2: Oxylabs
PROXY2 = {
    'proxy_type': 'socks5',
    'addr': 'dc.oxylabs.io',
    'port': 8000,
    'username': 'harshop01_6Mzjy',
    'password': 'V=DMlz+qMinV_n85',
    'rdns': True
}

# Choose Active Proxy (Change to PROXY2 if needed)
ACTIVE_PROXY = PROXY1

# ==================== CONFIG ====================
API_ID = 37235723
API_HASH = "880a876edaf529c8493b873d47821ec2"
BOT_TOKEN = "8783810252:AAEv2GtOJYG_-iBv1AMjvV8Le3kZBo9FJb0"
ADMIN_ID = [7077294261, 8496671308, 1308204344, 7856977111, 7029965057, 5295792382, 1965289355, 8467239599, 7249106493, 7292047135, 8368859527, 7582867285]
GROUP_ID = -5280674882

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

# ==================== UTILITY FUNCTIONS ====================

async def create_json_file(filename):
    if not os.path.exists(filename):
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps({}))

async def initialize_files():
    for file in [PREMIUM_FILE, FREE_FILE, SITE_FILE, KEYS_FILE, BANNED_FILE, PROXY_FILE]:
        await create_json_file(file)

async def load_json(filename):
    try:
        if not os.path.exists(filename):
            await create_json_file(filename)
        async with aiofiles.open(filename, "r") as f:
            return json.loads(await f.read())
    except:
        return {}

async def save_json(filename, data):
    try:
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(data, indent=4))
    except Exception as e:
        logging.error(f"Save error {filename}: {e}")

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

# ==================== MAIN CLIENT WITH PROXY ====================

client = TelegramClient(
    'cc_bot',
    API_ID,
    API_HASH,
    proxy=ACTIVE_PROXY,          # Proxy Added Here
    dc_id=5,                     # Force DC 5 (helps with reconnect issue)
    connection_retries=30,
    retry_delay=4,
    request_retries=10,
    flood_sleep_threshold=120
)

# ==================== YOUR EXISTING FUNCTIONS ====================
# (All your functions like process_msh_cards, etc. remain unchanged)
# ... paste all your other functions here if needed ...

async def main():
    await initialize_files()
    print("🤖 Bot Starting with Proxy...")
    try:
        await client.start(bot_token=BOT_TOKEN)
        print("✅ Bot is Running Successfully with Proxy!")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
