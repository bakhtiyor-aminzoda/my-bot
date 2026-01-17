import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Bot Token from @BotFather
# In production, use os.getenv("BOT_TOKEN")
# For demo purposes, you can also paste it here directly, but strictly recommended to use .env
BOT_TOKEN = os.getenv("BOT_TOKEN", "8478672514:AAGupR9_ymf7YARUhcMgnKq31ES_84hC9HE")

# Admin ID who receives the leads
# You can find your ID via bots like @userinfobot
ADMIN_ID = os.getenv("ADMIN_ID", 7179785109)

# Admin Username for direct contact link (without @)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

# Google Sheets Config
GOOGLE_KEY_FILE = os.getenv("GOOGLE_KEY_FILE", "bot/credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1o__PnwD7IE60SchAz4eV1PEAhBG5rbeJ_SAlC0Gg9zs") 

if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("WARNING: BOT_TOKEN is not set in config.py or .env")
