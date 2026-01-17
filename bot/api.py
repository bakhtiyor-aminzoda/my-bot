from aiohttp import web
from bot.database import count_users, get_recent_orders, count_orders, get_order_by_id, update_order_status as db_update_order_status

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

async def get_order_details(request):
    """
    Returns full details for a single order.
    GET /api/orders/{id}
    """
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

async def update_order_status(request):
    """
    Updates status and notifies user.
    POST /api/orders/{id}/status
    Body: {"status": "in_progress"}
    """
    order_id = int(request.match_info['id'])
    body = await request.json()
    new_status = body.get("status")
    
    if not new_status:
        return web.json_response({"error": "Status required"}, status=400)
        
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
    
    msg_text = status_msg.get(new_status, f"Статус вашего заказа обновлен: {new_status}")
    
    try:
        await bot.send_message(chat_id=user_id, text=msg_text)
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")
        
    return web.json_response({"status": "updated", "new_status": new_status})

async def health_check(request):
    """Simple health check for Render."""
    return web.Response(text="OK", status=200)
