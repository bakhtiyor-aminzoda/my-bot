from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMIN_USERNAME

def main_menu_kb() -> InlineKeyboardMarkup:
    """
    Main Menu Keyboard
    """
    kb = [
        [InlineKeyboardButton(text="🛠 Услуги", callback_data="nav_services")],
        [InlineKeyboardButton(text="ℹ️ Обо мне", callback_data="nav_about")],
        [InlineKeyboardButton(text="📩 Оставить заявку", callback_data="new_application")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def services_kb() -> InlineKeyboardMarkup:
    """
    Services Categories Keyboard
    """
    kb = [
        [InlineKeyboardButton(text="🛍 Магазины", callback_data="cat_shops")],
        [InlineKeyboardButton(text="📅 Запись клиентов", callback_data="cat_booking")],
        [InlineKeyboardButton(text="🤖 Чат-боты поддержки", callback_data="cat_support")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def service_detail_kb(service_id: str) -> InlineKeyboardMarkup:
    """
    Service Detail Keyboard (Order specific service or go back)
    """
    kb = [
        [InlineKeyboardButton(text="✅ Заказать это решение", callback_data=f"order_{service_id}")],
        [InlineKeyboardButton(text="🔙 Назад к услугам", callback_data="nav_back_services")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def post_submit_kb() -> InlineKeyboardMarkup:
    """
    Post-submit flow keyboard
    """
    kb = [
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="nav_back_main")],
        [InlineKeyboardButton(text="📩 Оставить ещё одну заявку", callback_data="new_application")],
        [InlineKeyboardButton(text="✉️ Связаться напрямую", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
