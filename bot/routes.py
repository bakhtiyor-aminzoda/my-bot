from aiohttp import web
from bot.api import get_dashboard_stats, get_bookings_list, health_check

def setup_routes(app: web.Application):
    """
    Registers all API and Web routes.
    """
    # API endpoints for Pocket CRM
    app.router.add_get("/api/stats", get_dashboard_stats)
    app.router.add_get("/api/bookings", get_bookings_list)
    
    # Health check (useful for Render/Uptime monitors)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    
    # Static files for Admin UI
    # We serve the 'bot/static' folder at root or /admin
    # For simplicity, let's serve /admin/ -> bot/static/admin/index.html
    app.router.add_static("/admin", path="bot/static/admin", name="admin")
