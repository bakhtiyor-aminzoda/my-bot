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
        [InlineKeyboardButton(text="📂 Наши кейсы", callback_data="nav_cases")],
        [InlineKeyboardButton(text="ℹ️ О компании", callback_data="nav_about")],
        [InlineKeyboardButton(text="📞 Обсудить проект", callback_data="new_application")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cases_kb() -> InlineKeyboardMarkup:
    """
    Portfolio / Cases Menu
    """
    kb = [
        [InlineKeyboardButton(text="🥗 Calorie AI (Vision)", callback_data="case_calorie")],
        [InlineKeyboardButton(text="🍔 Доставка еды (Bot)", callback_data="case_food")],
        [InlineKeyboardButton(text="🎓 Онлайн-школа (LMS)", callback_data="case_school")],
        [InlineKeyboardButton(text="💅 Салон красоты (CRM)", callback_data="case_beauty")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def case_action_kb() -> InlineKeyboardMarkup:
    """
    Action buttons under a specific case
    """
    kb = [
        [InlineKeyboardButton(text="📞 Хочу так же", callback_data="new_application")],
        [InlineKeyboardButton(text="🔙 К списку кейсов", callback_data="nav_cases")]
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
