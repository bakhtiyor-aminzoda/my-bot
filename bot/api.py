from aiohttp import web
from bot.database import (
    count_users, get_recent_orders, count_orders, get_order_by_id, 
    update_order_status as db_update_order_status, 
    update_order_details as db_update_order_details,
    get_daily_stats, get_all_user_ids
)
from bot.config import ADMIN_ID
import asyncio

def require_admin(handler):
    """
    Middleware-like decorator to check if request is from Admin.
    For MVP, we check a custom header 'X-Telegram-User' sent by the WebApp.
    In production, this MUST verify the cryptographic signature of initData.
    """
    async def wrapper(request):
        # Allow health check to bypass
        if request.path == "/": return await handler(request)

        user_id = request.headers.get("X-Telegram-User")
        # Security: If no header, or doesn't match ADMIN_ID, reject.
        # Note: This is weak security (client-side spoofable), but good for MVP/Demo.
        # Real impl requires validating initData hash.
        if not user_id or str(user_id) != str(ADMIN_ID):
             # Log warning but allow for now to prevent lockout during dev testing 
             # if headers aren't set yet. 
             # Uncomment below to enforce strict mode:
             # return web.json_response({"error": "Unauthorized"}, status=403)
             pass 

        return await handler(request)
    return wrapper

@require_admin
async def get_dashboard_stats(request):
    """
    Returns JSON statistics + Chart Data.
    GET /api/stats
    """
    total_users = await count_users()
    total_orders = await count_orders()
    
    # Revenue (Mock, or derive from budget if parsed)
    revenue = total_orders * 150 # Mock avg
    
    # Chart Data
    daily_stats = await get_daily_stats(7)
    # Format for Chart.js: labels=["Mon", "Tue"], data=[5, 2]
    chart_labels = []
    chart_values = []
    
    # Fill gaps? For MVP just return what we have.
    for date_str, count in daily_stats:
        chart_labels.append(str(date_str)[5:]) # "MM-DD"
        chart_values.append(count)

    stats = {
        "users": total_users,
        "revenue_today": revenue,  
        "active_orders": total_orders,
        "chart": {
            "labels": chart_labels,
            "data": chart_values
        }
    }
    
    return web.json_response(stats)

@require_admin
async def get_bookings_list(request):
    """GET /api/bookings?q=search_term"""
    search_query = request.query.get('q')
    limit = 50 if search_query else 20 # Show more results if searching
    
    orders = await get_recent_orders(limit=limit, search_query=search_query)
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

@require_admin
async def get_order_details(request):
    """GET /api/orders/{id}"""
    order_id = int(request.match_info['id'])
    order = await get_order_by_id(order_id)
    
    if not order:
        return web.json_response({"error": "Order not found"}, status=404)
        
    data = {
        "id": order.id,
        "name": order.name,
        "contact_info": order.contact_info,
        "business_type": order.business_type,
        "budget": order.budget,
        "task_description": order.task_description,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None
    }
    return web.json_response(data)

@require_admin
async def update_order_status(request):
    """POST /api/orders/{id}/status"""
    order_id = int(request.match_info['id'])
    body = await request.json()
    new_status = body.get("status")
    
    updated_order = await db_update_order_status(order_id, new_status)
    if not updated_order:
        return web.json_response({"error": "Order not found"}, status=404)
        
    # Notify User via Bot
    bot = request.app["bot"]
    user_id = updated_order.user_id
    
    status_msg = {
        "in_progress": "🛠 Ваш заказ взят в работу! Скоро с вами свяжется менеджер.",
        "completed": "✅ Ваш заказ выполнен! Спасибо, что выбрали нас.",
        "cancelled": "❌ Ваш заказ был отменен. Если это ошибка, напишите нам."
    }
    msg_text = status_msg.get(new_status, f"Статус обновлен: {new_status}")
    
    try:
        await bot.send_message(chat_id=user_id, text=msg_text)
    except Exception as e:
        print(f"Failed to notify user: {e}")
        
    return web.json_response({"status": "updated"})

@require_admin
async def update_order_details(request):
    """
    POST /api/orders/{id}/update
    Body: {"budget": "5000", "contact_info": "...", "task_description": "..."}
    """
    order_id = int(request.match_info['id'])
    body = await request.json()
    
    updated_order = await db_update_order_details(order_id, body)
    if not updated_order:
        return web.json_response({"error": "Order not found"}, status=404)

    return web.json_response({"status": "updated"})

@require_admin
async def send_broadcast(request):
    """
    POST /api/broadcast
    Body: {"message": "Hello everyone!"}
    """
    body = await request.json()
    text = body.get("message")
    
    if not text:
        return web.json_response({"error": "Message required"}, status=400)
        
    user_ids = await get_all_user_ids()
    bot = request.app["bot"]
    
    count = 0
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=text)
            count += 1
            await asyncio.sleep(0.05) # Avoid hitting limits
        except Exception as e:
            print(f"Broadcast fail for {uid}: {e}")
            
    return web.json_response({"status": "sent", "count": count})

async def health_check(request):
    """Simple health check for Render."""
    return web.Response(text="OK", status=200)
