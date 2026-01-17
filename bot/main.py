import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import router
from bot.routes import setup_routes

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def on_startup(app: web.Application):
    """Global startup event for both modes."""
    await init_db()
    setup_routes(app)
    logger.info("🚀 App started. Routes configured.")

async def start_polling_background(app: web.Application):
    """Background task for Polling Mode."""
    bot: Bot = app["bot"]
    dp: Dispatcher = app["dp"]
    
    logger.info("📡 Starting POLLING in background...")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))

async def configure_webhook(app: web.Application):
    """Startup action for Webhook Mode."""
    bot: Bot = app["bot"]
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        logger.info(f"🔗 Setting webhook: {webhook_url}/webhook")
        await bot.set_webhook(f"{webhook_url}/webhook")

def main():
    # Initialize Bot and Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Create Aiohttp App
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    
    # Common Startup
    app.on_startup.append(on_startup)
    
    # Determine Mode
    run_mode = os.getenv("RUN_MODE", "polling")
    
    if run_mode == "webhook":
        # --- WEBHOOK MODE (Render) ---
        webhook_url = os.getenv("WEBHOOK_URL")
        port = int(os.getenv("PORT", 8080))
        
        if not webhook_url:
            logger.error("❌ WEBHOOK_URL is missing for webhook mode!")
            return

        # 1. Register Webhook Handler (from aiogram)
        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path="/webhook")
        
        # 2. Setup App (Signals)
        setup_application(app, dp, bot=bot)
        
        # 3. Configure Hook on Startup
        app.on_startup.append(configure_webhook)
        
        logger.info(f"🌍 Starting WEBHOOK server on port {port}...")
        web.run_app(app, host="0.0.0.0", port=port)
        
    else:
        # --- POLLING MODE (Local Dev) ---
        # Even in polling, we run the Web App for the CRM API!
        logger.info("💻 Starting LOCAL server (Polling + API)...")
        
        # Start polling in background when app starts
        app.on_startup.append(start_polling_background)
        
        # Run the web server (for Admin API)
        web.run_app(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped!")
