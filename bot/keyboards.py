from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import ADMIN_USERNAME

def main_menu_kb(webapp_url: str = None) -> InlineKeyboardMarkup:
    """
    Main Menu Keyboard
    """
    kb = []
    if webapp_url:
        kb.append([InlineKeyboardButton(text="🚀 Магазин услуг", web_app=WebAppInfo(url=webapp_url))])
    
    kb.extend([
        [InlineKeyboardButton(text="🛠 Услуги (Текст)", callback_data="nav_services")],
        [InlineKeyboardButton(text="ℹ️ Обо мне", callback_data="nav_about")],
        [InlineKeyboardButton(text="📩 Оставить заявку", callback_data="new_application")]
    ])
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

def ai_response_kb() -> InlineKeyboardMarkup: # Added type hint for consistency
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Оставить заявку", callback_data="new_application") # Changed callback_data to match existing "new_application"
    kb.button(text="🏠 Главное меню", callback_data="nav_back_main")
    kb.adjust(1)
    return kb.as_markup()

def budget_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📉 Эконом (1000-2000 с.)", callback_data="budget_low")
    kb.button(text="📈 Бизнес (2000-5000 с.)", callback_data="budget_mid")
    kb.button(text="💎 Премиум (от 5000 с.)", callback_data="budget_high")
    kb.adjust(1)
    return kb.as_markup()
