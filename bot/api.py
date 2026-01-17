from aiohttp import web
from bot.database import count_users, get_recent_orders, count_orders

async def get_dashboard_stats(request):
    """
    Returns JSON statistics for the Admin Dashboard.
    GET /api/stats
    """
    # 1. Real Data
    total_users = await count_users()
    total_orders = await count_orders()
    
    # Placeholder for Revenue (Assume avg deal value 2000 for demo)
    revenue = total_orders * 50 # Mock avg revenue per lead just to show number

    stats = {
        "users": total_users,
        "revenue_today": revenue,  
        "active_orders": total_orders,
        "conversion_rate": "15%" # Mock
    }
    
    return web.json_response(stats)

async def get_bookings_list(request):
    """
    Returns list of recent orders (leads).
    GET /api/bookings
    """
    orders = await get_recent_orders(limit=10)
    
    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "client": o.name or "Unknown",
            "service": o.service_context or "Service",
            "time": o.created_at.isoformat() if o.created_at else None,
            "status": o.status
        })
        
    return web.json_response(data)

async def health_check(request):
    """Simple health check for Render."""
    return web.Response(text="OK", status=200)
