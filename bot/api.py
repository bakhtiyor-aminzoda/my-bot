from aiohttp import web
from bot.database import count_users, get_all_bookings
from datetime import datetime

async def get_dashboard_stats(request):
    """
    Returns JSON statistics for the Admin Dashboard.
    GET /api/stats
    """
    # 1. Real Data
    total_users = await count_users()
    bookings = await get_all_bookings()
    
    active_orders = len([b for b in bookings if b.status == 'new'])
    
    # Placeholder for Revenue (Simple logic: 1 booking = 100 somoni for demo)
    revenue = len([b for b in bookings if b.status == 'completed']) * 100

    stats = {
        "users": total_users,
        "revenue_today": revenue,  
        "active_orders": active_orders,
        "conversion_rate": "5%" # Mock
    }
    
    return web.json_response(stats)

async def get_bookings_list(request):
    """
    Returns list of bookings for the Calendar.
    GET /api/bookings
    """
    bookings = await get_all_bookings()
    
    data = []
    for b in bookings:
        data.append({
            "id": b.id,
            "client": b.client_name,
            "service": b.service_type,
            "time": b.slot_time.isoformat() if b.slot_time else None,
            "status": b.status
        })
        
    return web.json_response(data)

async def health_check(request):
    """Simple health check for Render."""
    return web.Response(text="OK", status=200)
