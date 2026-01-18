import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Bot Token from @BotFather
# In production, use os.getenv("BOT_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin ID who receives the leads
# You can find your ID via bots like @userinfobot
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", 7179785109))
except (ValueError, TypeError):
    ADMIN_ID = 7179785109
    print("Warning: ADMIN_ID in .env is not a valid integer. Using default.")

# Admin Username for direct contact link (without @)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

# Google Sheets Config
GOOGLE_KEY_FILE = os.getenv("GOOGLE_KEY_FILE", "bot/credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID") 

# AI Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Webhook Config
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("WARNING: BOT_TOKEN is not set in config.py or .env")
