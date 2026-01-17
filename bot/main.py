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

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def on_startup_webhook(app):
    await init_db()
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        bot = app["bot"]
        await bot.set_webhook(f"{webhook_url}/webhook")

def main():
    # Initialize Bot and Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    run_mode = os.getenv("RUN_MODE", "polling")
    
    if run_mode == "webhook":
        # Webhook mode for Render
        webhook_url = os.getenv("WEBHOOK_URL")
        port = int(os.getenv("PORT", 8080))
        
        if not webhook_url:
            print("ERROR: WEBHOOK_URL env var is required for webhook mode")
            return
            
        print(f"Starting in WEBHOOK mode on port {port}...")
        
        # Create aiohttp app
        app = web.Application()
        app["bot"] = bot # Store bot in app for startup handler
        
        # Create request handler
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        # Register webhook handler
        webhook_requests_handler.register(app, path="/webhook")
        
        # Setup application
        setup_application(app, dp, bot=bot)
        
        # Run app
        # On startup, set webhook AND init DB
        app.on_startup.append(on_startup_webhook)
        
        web.run_app(app, host="0.0.0.0", port=port)
        
    else:
        # Polling mode for local dev
        print("Starting in POLLING mode...")
        async def run_polling():
            await init_db() # Init DB
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
            
        asyncio.run(run_polling())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped!")
