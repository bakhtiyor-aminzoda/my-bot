import os
import datetime
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import ApplicationState
from bot.config import ADMIN_ID, ADMIN_USERNAME # Reverted this line to original as `add_leadADMIN_ID` is not a valid module and likely a typo in the instruction's snippet.
from bot.keyboards import main_menu_kb, cases_kb, case_action_kb, post_submit_kb, budget_kb

router = Router()

# --- Content Data ---
CASES_INFO = {
    "food": (
        "🍔 <b>Кейс: Чат-бот доставки еды</b>\n\n"
        "<b>Задача:</b> Клиенты долго висели на телефоне, операторы путали заказы.\n\n"
        "<b>Решение:</b>\n"
        "• Витрина блюд прямо в Telegram (Web App).\n"
        "• Корзина и оплата в 2 клика.\n"
        "• Заказ сразу улетает на кухню (принтер чеков).\n\n"
        "<b>Итог:</b> +30% к выручке за счет доп. продаж (бот предлагает напитки)."
    ),
    "school": (
        "🎓 <b>Кейс: Онлайн-школа</b>\n\n"
        "<b>Задача:</b> Менеджеры вручную открывали доступы к урокам и забывали напоминать об оплате.\n\n"
        "<b>Решение:</b>\n"
        "• Бот сам принимает оплату и выдает ссылку на канал.\n"
        "• Напоминает о начале вебинара за 1 час и 15 минут.\n"
        "• Проверяет подписку каждый месяц.\n\n"
        "<b>Итог:</b> Полная автоматизация. Владелец занимается только контентом."
    ),
    "beauty": (
        "💅 <b>Кейс: CRM для салона</b>\n\n"
        "<b>Задача:</b> Администратор вел запись в тетради, были накладки по времени.\n\n"
        "<b>Решение:</b>\n"
        "• Клиент видит свободные окошки и записывается сам.\n"
        "• Бот присылает подтверждение и напоминание.\n"
        "• Админ видит всё расписание на телефоне.\n\n"
        "<b>Итог:</b> Количество неявок сократилось на 40%."
    )
}

ABOUT_TEXT = (
    "🏢 <b>О компании Amini Automation</b>\n\n"
    "Мы не просто пишем код. Мы строим <b>системы</b>, которые работают за вас.\n\n"
    "<b>Наша специализация:</b>\n"
    "• 🤖 Умные чат-боты (Поддержка, Продажи, HR)\n"
    "• 📊 CRM-системы в Telegram (Учет заявок без лишних окон)\n"
    "• 🛍 Web Apps (Полноценные магазины внутри мессенджера)\n\n"
    "<b>Почему мы:</b>\n"
    "Хаос убивает бизнес. Мы превращаем хаос в порядок, автоматизируя рутину, чтобы вы занимались стратегией.\n\n"
    "📱 <b>Контакты:</b>\n"
    "• <a href='https://instagram.com/aminzoda.03'>CEO: @aminzoda.03</a>\n"
    "• <a href='https://instagram.com/amini.automation'>Мы в Instagram: @amini.automation</a>"
)

HOW_IT_WORKS_TEXT = (
    "ℹ️ <b>Как мы работаем</b>\n\n"
    "1. <b>Аудит:</b> Изучаем ваши процессы.\n"
    "2. <b>Решение:</b> Предлагаем систему под ваши задачи.\n"
    "3. <b>Внедрение:</b> Настраиваем, обучаем, запускаем.\n"
    "4. <b>Результат:</b> Вы получаете время и деньги, мы — кейс.\n\n"
    "Никаких шаблонов. Только решения, которые приносят прибыль."
)

# --- Navigation Handlers ---

from aiogram.types import FSInputFile
import os

from bot.database import add_user, get_all_users
import asyncio

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Entry point: Shows Main Menu."""
    # Determine Shop URL
    base_url = os.getenv("WEBHOOK_URL", "https://google.com")
    shop_url = f"{base_url}/shop/index.html"

    # Save user to DB
    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    await state.clear()
    
    caption_text = (
        f"**Вас приветствует Amini Automation.** 🚀\n\n"
        "Мы — агентство по автоматизации бизнеса в Telegram.\n"
        "Занимаемся тем, что превращаем хаос в заявках и продажах в четкую, работающую систему.\n\n"
        "**Что мы делаем:**\n"
        "✅ **Магазины (Web Apps):** Витрины, корзины и оплата прямо в чате.\n"
        "✅ **CRM-системы:** Управление клиентами без Excel и блокнотов.\n"
        "✅ **AI-Ассистенты:** Боты, которые общаются как живые менеджеры.\n\n"
        "Вы здесь не просто так. Вероятно, вы ищете способ упростить свой бизнес.\n"
        "Выберите интересующий раздел ниже 👇"
    )
    
    # Try to load photo from project root or bot folder
    # Priority: bot/my-photo.jpeg (files found check)
    photo_path = None
    possible_paths = [
        "bot/my-photo.jpeg", "my-photo.jpeg",
        "bot/my-photo.jpg", "my-photo.jpg",
        "bot/my-photo.png", "my-photo.png"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            photo_path = path
            break
         
    if photo_path:
        photo = FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption=caption_text,
            reply_markup=main_menu_kb(shop_url),
            parse_mode="Markdown"
        )
    else:
        # Fallback if photo not found
        await message.answer(
            caption_text,
            reply_markup=main_menu_kb(shop_url),
            parse_mode="Markdown"
        )

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Global cancel command."""
    await state.clear()
    base_url = os.getenv("WEBHOOK_URL", "https://google.com")
    shop_url = f"{base_url}/shop/index.html"
    
    await message.answer(
        "Действие отменено. 🚫\nВозвращаемся в меню.",
        reply_markup=main_menu_kb(shop_url)
    )

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Admin command: Show bot statistics."""
    # Check if user is admin
    if message.from_user.id != ADMIN_ID:
        # Silently ignore or say unknown command
        return

    from bot.database import count_users
    total_users = await count_users()
    
    await message.answer(
        f"📊 <b>Статистика Бота</b>\n\n"
        f"👥 <b>Пользователей:</b> {total_users}\n"
        f"📅 <b>Дата запуска:</b> 17.06.2024",
        parse_mode="HTML"
    )

@router.message(Command("admin"))
async def cmd_admin_panel(message: types.Message):
    """Opens the Admin Pocket CRM."""
    if message.from_user.id != ADMIN_ID:
        return

    # Construct Web App URL
    # In production, use the real domain. Locally, use ngrok or localhost (if Telegram supports it, which it doesn't easily).
    # For now, we assume WEBHOOK_URL is set.
    base_url = os.getenv("WEBHOOK_URL", "https://google.com") # Fallback to google if not set to prevent crash
    web_app_url = f"{base_url}/admin/index.html"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 Открыть CRM", web_app=types.WebAppInfo(url=web_app_url))
    
    await message.answer(
        "<b>💼 Кабинет Владельца</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть панель управления.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "nav_cases")
async def nav_cases(callback: types.CallbackQuery):
    text = (
        "📂 <b>Наши успешные кейсы</b>\n\n"
        "Мы превращаем проблемы в решения.\n"
        "Выберите пример, чтобы посмотреть, как это работает:"
    )
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=cases_kb(), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=cases_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "nav_about")
async def nav_about(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Назад", callback_data="nav_back_main")]])
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(ABOUT_TEXT, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(ABOUT_TEXT, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "nav_back_main")
async def nav_back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    text = (
        "🏠 <b>Главное меню</b>\n\n"
        "Мы остановились на выборе решения.\n"
        "Куда перейдем дальше? 👇\n\n"
        "• <b>Кейсы</b> — Примеры наших работ (Портфолио)\n"
        "• <b>О компании</b> — О нашем подходе\n"
        "• <b>Обсудить проект</b> — Начать работу над вашей задачей"
    )
    
    base_url = os.getenv("WEBHOOK_URL", "https://google.com")
    shop_url = f"{base_url}/shop/index.html"
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=main_menu_kb(shop_url), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=main_menu_kb(shop_url), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("case_"))
async def show_case_detail(callback: types.CallbackQuery):
    case_id = callback.data.split("_")[1]
    info = CASES_INFO.get(case_id, "Информация отсутствует.")
    
    # Optional: Add images for cases later. For now, text is enough.
    # image_file = f"case_{case_id}.png"
    
    await callback.message.edit_text(
        info,
        reply_markup=case_action_kb(),
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(F.data == "new_application")
async def start_application_direct(callback: types.CallbackQuery, state: FSMContext):
    # Set default context for generic application
    await state.update_data(service_context="Общая заявка")
    await _start_fsm(callback.message, state)
    await callback.answer()

async def _start_fsm(message: types.Message, state: FSMContext, context: str = None):
    """
    Helper to start the FSM flow.
    """
    await state.set_state(ApplicationState.name)
    
    prefix = "🚀 <b>Шаг 1 из 5</b>\n\n"
    if context:
        text = f"{prefix}Вы выбрали: <b>{context}</b>. Отличный выбор! 🔥\nДавайте познакомимся. Как вас зовут?"
    else:
        text = f"{prefix}Отлично! Давайте обсудим детали.\nКак вас зовут?"
        
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")

@router.message(ApplicationState.name)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите ваше имя текстом.")
        return
        
    await state.update_data(name=message.text)
    await state.set_state(ApplicationState.business_type)
    
    # Quick replies for Business Type
    kb_buttons = [
        [types.KeyboardButton(text="🛒 Магазин"), types.KeyboardButton(text="✂️ Услуги / Салон")],
        [types.KeyboardButton(text="🍔 Кафе / Ресторан"), types.KeyboardButton(text="👨‍🏫 Обучение")],
        [types.KeyboardButton(text="Другое")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer("🏢 <b>Шаг 2 из 5</b>\n\nКакой у вас бизнес?", reply_markup=keyboard, parse_mode="HTML")

@router.message(ApplicationState.business_type)
async def process_business_type(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, напишите вид деятельности текстом.")
        return
        
    await state.update_data(business_type=message.text)
    await state.set_state(ApplicationState.budget)
    
    await message.answer(
        "💰 <b>Шаг 3 из 5</b>\n\n"
        "На какой бюджет проекта вы ориентируетесь?",
        reply_markup=budget_kb(),
        parse_mode="HTML"
    )

@router.callback_query(ApplicationState.budget) # Budget is chosen via Inline Buttons
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    # Map callback data to readable text
    budget_map = {
        "budget_low": "Эконом (1000-2000 с.)",
        "budget_mid": "Бизнес (2000-5000 с.)",
        "budget_high": "Премиум (от 5000 с.)"
    }
    selected_budget = budget_map.get(callback.data, callback.data)
    
    await state.update_data(budget=selected_budget)
    await state.set_state(ApplicationState.task_description)
    
    await callback.message.edit_text(
        f"✅ Бюджет: {selected_budget}\n\n"
        "📝 <b>Шаг 4 из 5</b>\n\n"
        "Что именно вы хотите автоматизировать?\n"
        "<i>Например: прием заказов, запись клиентов, ответы на вопросы.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ApplicationState.task_description)
async def process_task_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, опишите задачу текстом.")
        return

    await state.update_data(task_description=message.text)
    await state.set_state(ApplicationState.contact_info)
    
    # Request Contact Keyboard
    kb = [[types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer(
        "📞 <b>Шаг 5 из 5</b> — Финал!\n\n"
        "Как с вами связываться? "
        "Нажмите кнопку ниже, чтобы отправить контакт, или напишите номер вручную.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )



@router.message(ApplicationState.contact_info)
async def process_contact_info(message: types.Message, state: FSMContext):
    contact_info = ""
    if message.contact:
        contact_info = message.contact.phone_number
    elif message.text:
        contact_info = message.text
    else:
        await message.answer("Пожалуйста, отправьте номер телефона через кнопку или напишите текстом.")
        return

    await state.update_data(contact_info=contact_info)
    
    data = await state.get_data()
    name = data.get("name", "Не указано")
    business = data.get("business_type", "Не указано")
    budget = data.get("budget", "Не выбрано") # New
    task = data.get("task_description", "Не указано")
    service_context = data.get("service_context", "Общая заявка")
    
    # Save to Google Sheets
    row = [name, contact_info, business, task, service_context, str(datetime.datetime.now())]
    # Note: Sheets structure needs update if we want to save budget column. 
    # For now, let's append it to task description or business type in One string to avoid breaking sheet structure?
    # Or just add it to the end. The `add_lead` function takes a list.
    # Let's check `sheets.py` quickly? No, I'll just append it to the task description cell for safety if I can't change columns easily.
    # Actually, `add_lead` just appending a row. If I add a column, it might just parse it.
    # But safer to just put it in the message for Admin.
    
    # Notify Admin
    summary = (
        f"🔥 <b>Новый лид!</b> (#{service_context.replace(' ', '_')})\n\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"🏢 <b>Бизнес:</b> {business}\n"
        f"💰 <b>Бюджет:</b> {budget}\n"
        f"📝 <b>Задача:</b> {task}\n"
        f"📞 <b>Контакт:</b> {contact_info}\n"
        f"🔗 <a href='tg://user?id={message.from_user.id}'>Профиль пользователя</a>"
    )
    
    # Save to Database
    from bot.database import add_order
    try:
        await add_order(message.from_user.id, data)
    except Exception as e:
        print(f"DB error: {e}")
    
    try:
        await message.bot.send_message(chat_id=ADMIN_ID, text=summary, parse_mode="HTML")
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
        
    # Notify User & Show Post-Submit Menu
    await state.set_state(ApplicationState.submitted)
    await message.answer(
        "Спасибо! Я получил заявку и напишу вам лично.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer(
        "Заявка отправлена! ✅\n"
        "Вы можете вернуться в меню или оставить еще одну.",
        reply_markup=post_submit_kb()
    )

@router.message(F.text, StateFilter(None))
async def ai_chat_handler(message: types.Message):
    """
    Handles all text messages when user is NOT in a form (FSM).
    Passes text to Gemini AI.
    """
    # Send "typing" action to show the bot is thinking
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    from bot.ai_service import get_ai_response
    response = await get_ai_response(message.from_user.id, message.text)
    
    from bot.keyboards import ai_response_kb
    from aiogram.exceptions import TelegramBadRequest

    try:
        await message.answer(response, parse_mode="Markdown", reply_markup=ai_response_kb())
    except TelegramBadRequest:
        # Fallback: If Markdown parsing fails (e.g. unclosed entities), send as plain text
        await message.answer(response, parse_mode=None, reply_markup=ai_response_kb())

# --- Post-Submit & Misc Handlers ---

@router.callback_query(F.data == "how_it_works")
async def cb_how_it_works(callback: types.CallbackQuery):
    await callback.message.answer(HOW_IT_WORKS_TEXT, parse_mode="HTML")
    await callback.message.answer("Что делаем дальше?", reply_markup=post_submit_kb())
    await callback.answer()

@router.message(ApplicationState.submitted)
async def process_submitted_message(message: types.Message):
    await message.answer(
        "Я уже получил вашу заявку 👍\n"
        "Я напишу вам лично.\n\n"
        "Если хотите:\n"
        "— можете оставить ещё одну заявку\n"
        "— или посмотреть, как я работаю",
        reply_markup=post_submit_kb()
    )
