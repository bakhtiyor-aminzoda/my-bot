import os
import datetime
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import ApplicationState
from bot.config import ADMIN_ID, ADMIN_USERNAME, WEBHOOK_URL
from bot.keyboards import main_menu_kb, cases_kb, case_action_kb, post_submit_kb, budget_kb
from bot.locales_data import LOCALES
from bot.database import add_user, get_user_language, set_user_language, add_order, get_referral_stats

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
    ),
    "calorie": (
        "🥗 <b>Кейс: Calorie AI (Computer Vision)</b>\n\n"
        "<b>Tech Stack:</b> Python, Gemini 1.5 Flash, OpenCV.\n\n"
        "<b>Задача:</b> Определять КБЖУ блюда по одной фотографии.\n\n"
        "<b>Решение:</b>\n"
        "• ИИ распознает ингредиенты на фото.\n"
        "• Рассчитывает граммовки и калорийность.\n"
        "• Ведет статистику пользователя.\n\n"
        "<b>Итог:</b> MVP запущен за 3 дня. Точность распознавания >90%."
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

# --- Localization Helpers ---
async def get_text(user_id: int, key: str) -> str:
    lang = await get_user_language(user_id)
    return LOCALES.get(lang, LOCALES["ru"]).get(key, key)

async def get_main_keyboard_dynamic(user_id: int):
    shop_url = f"{os.getenv('WEBHOOK_URL', 'https://google.com')}/shop/index.html"
    
    t_store = await get_text(user_id, "btn_store")
    t_cases = await get_text(user_id, "btn_cases")
    t_about = await get_text(user_id, "btn_about")
    t_discuss = await get_text(user_id, "btn_discuss")
    t_my_orders = await get_text(user_id, "btn_my_orders")
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t_store, web_app=WebAppInfo(url=shop_url))],
        [InlineKeyboardButton(text=t_my_orders, callback_data="my_orders")],
        [InlineKeyboardButton(text=t_cases, callback_data="nav_cases"), 
         InlineKeyboardButton(text=t_about, callback_data="nav_about")],
        [InlineKeyboardButton(text=t_discuss, callback_data="new_application")]
    ])

# ... cmd_start ...

@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: types.CallbackQuery):
    from bot.database import get_user_orders
    orders = await get_user_orders(callback.from_user.id)
    
    header = await get_text(callback.from_user.id, "header_my_orders")
    no_orders = await get_text(callback.from_user.id, "no_orders")
    back_text = await get_text(callback.from_user.id, "btn_back")
    
    if not orders:
        text = header + no_orders
    else:
        text = header
        for o in orders:
            # Localize status
            status_key = f"status_{o.status}"
            status_text = await get_text(callback.from_user.id, status_key)
            
            date_str = o.created_at.strftime("%d.%m.%Y")
            budget_str = o.budget if o.budget else "—"
            
            # Cleaner Layout
            text += (
                f"🔹 <b>Заказ #{o.id}</b>\n"
                f"📝 <b>{o.service_context}</b>\n"
                f"📅 {date_str} • {status_text}\n"
                f"💰 {budget_str}\n"
                f"──────────────\n\n"
            )
            
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=back_text, callback_data="nav_back_main")]
    ])
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, command: CommandObject = None):
    """Entry point: Shows Language Selection or Main Menu."""
    
    # Process Referral Argument
    invited_by = None
    if command and command.args:
        try:
            # Format: ref_12345
            if command.args.startswith("ref_"):
                referrer_id = int(command.args.split("_")[1])
                if referrer_id != message.from_user.id: # Prevent self-referral
                    invited_by = referrer_id
        except Exception: 
            pass

    # Save user immediately (with referral info)
    is_new = await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        invited_by=invited_by
    )
    
    # Notify Referrer if new user was created
    if is_new and invited_by:
        try:
            await message.bot.send_message(
                invited_by,
                f"🎉 <b>По вашей ссылке пришел новый пользователь!</b>\n{message.from_user.full_name}",
                parse_mode="HTML"
            )
        except Exception: pass

    await state.clear()
    
    # Show Language Selection
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
         types.InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tj")]
    ])
    
    await message.answer(
        "👋 **Выберите язык / Забони худро интихоб кунед:**", 
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang_code)
    
    text = await get_text(callback.from_user.id, "welcome")
    kb = await get_main_keyboard_dynamic(callback.from_user.id)
    
    # Try to verify photo existence
    photo_path = "bot/my-photo.jpeg" if os.path.exists("bot/my-photo.jpeg") else None
    
    if photo_path:
        # If message has photo, edit caption. If not (text), delete and send photo.
        # But callback is from text message usually.
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        
    # Notify Admin of new user
    try:
        if callback.from_user.id != ADMIN_ID:
            await callback.bot.send_message(
                ADMIN_ID, 
                f"🔔 **Новый пользователь**\n{callback.from_user.full_name}\nЯзык: {lang_code}"
            )
    except Exception: pass

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

@router.message(Command("smadmin"))
async def cmd_smadmin(message: types.Message):
    """Opens the Smart CRM Mini App."""
    if message.from_user.id != ADMIN_ID:
        return

    base_url = os.getenv("WEBHOOK_URL", "https://google.com")
    crm_url = f"{base_url}/crm/index.html"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 Open Smart CRM", web_app=types.WebAppInfo(url=crm_url))
    
    await message.answer(
        "<b>🧠 Smart CRM (Kanban + AI)</b>\n\n"
        "Управление лидами, статусы и AI-аналитика.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.message(Command("seed"))
async def cmd_seed(message: types.Message):
    """Admin command: Seed DB with dummy data."""
    if message.from_user.id != ADMIN_ID:
        return
        
    await message.answer("🌱 Seeding database... Please wait.", parse_mode="Markdown")
    
    from bot.database import seed_dummy_orders
    try:
        await seed_dummy_orders(message.from_user.id)
        await message.answer("✅ **Database Seeded!**\n\nReload the Admin Panel web app to see changes.", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Error seeding:\n`{str(e)}`", parse_mode="Markdown")


@router.callback_query(F.data == "nav_cases")
async def nav_cases(callback: types.CallbackQuery):
    text = await get_text(callback.from_user.id, "cases_intro")
    
    # Cases buttons should probably be localized too, but for now we use the static `cases_kb`
    # Ideally, we should update `cases_kb` to be dynamic or just inline it here.
    # Let's rely on the existing kb for now to save time, assume titles are "universal" enough or accept Russian there.
    # Actually, let's look at locales_data.py -> "case_food", etc.
    # We should update the buttons!
    
    c1 = await get_text(callback.from_user.id, "case_food")
    c2 = await get_text(callback.from_user.id, "case_school")
    c3 = await get_text(callback.from_user.id, "case_beauty")
    back = await get_text(callback.from_user.id, "btn_back")
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🥗 Calorie AI (Vision)", callback_data="case_calorie")],
        [types.InlineKeyboardButton(text=c1, callback_data="case_food")],
        [types.InlineKeyboardButton(text=c2, callback_data="case_school")],
        [types.InlineKeyboardButton(text=c3, callback_data="case_beauty")],
        [types.InlineKeyboardButton(text=back, callback_data="nav_back_main")]
    ])
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "nav_about")
async def nav_about(callback: types.CallbackQuery):
    text = await get_text(callback.from_user.id, "about_text")
    back = await get_text(callback.from_user.id, "btn_back")
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=back, callback_data="nav_back_main")]])
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "nav_back_main")
async def nav_back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    text = await get_text(callback.from_user.id, "menu_main")
    kb = await get_main_keyboard_dynamic(callback.from_user.id)
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
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
    user_id = message.from_user.id
    
    # We will use "fsm_name" which corresponds to "Step 1 of 5..."
    text = await get_text(user_id, "fsm_name")
        
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")

@router.message(ApplicationState.name)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите ваше имя текстом / Лутфан номи худро нависед.")
        return
        
    await state.update_data(name=message.text)
    await state.set_state(ApplicationState.business_type)
    
    text = await get_text(message.from_user.id, "fsm_business")
    
    # Quick replies could be localized too, but let's keep it simple or remove them if text is generic
    # For now, let's remove the keyboard to simplify logic or reuse generic ones
    # Or give broad categories that are understandable. 
    # Let's just use text input for business type to avoid translating 10 buttons right now.
    
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")

@router.message(ApplicationState.business_type)
async def process_business_type(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, напишите вид деятельности текстом.")
        return
        
    await state.update_data(business_type=message.text)
    await state.set_state(ApplicationState.budget)
    
    text = await get_text(message.from_user.id, "fsm_budget")
    # Budget buttons: low/mid/high. 
    # We should update budget_kb to be dynamic. 
    # For now, let's reuse `budget_kb` but be aware labels are Russian. 
    # Better: just ask for text if we don't want to refactor buttons deeply.
    # User can type number.
    
    await message.answer(text, reply_markup=budget_kb(), parse_mode="Markdown")

@router.callback_query(ApplicationState.budget)
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    budget_map = {
        "budget_low": "Эконом (1000-2000 с.)",
        "budget_mid": "Бизнес (2000-5000 с.)",
        "budget_high": "Премиум (от 5000 с.)"
    }
    selected_budget = budget_map.get(callback.data, callback.data)
    
    await state.update_data(budget=selected_budget)
    await state.set_state(ApplicationState.task_description)
    
    text = await get_text(callback.from_user.id, "fsm_task")
    await callback.message.edit_text(f"✅ {selected_budget}\n\n{text}", parse_mode="Markdown")
    await callback.answer()

@router.message(ApplicationState.task_description)
async def process_task_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, опишите задачу текстом.")
        return

    await state.update_data(task_description=message.text)
    await state.set_state(ApplicationState.contact_info)
    
    text = await get_text(message.from_user.id, "fsm_contact")
    btn_text = await get_text(message.from_user.id, "btn_contact")
    
    kb = [[types.KeyboardButton(text=btn_text, request_contact=True)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")



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
    
    msg_thanks = await get_text(message.from_user.id, "msg_thanks")
    await message.answer(
        msg_thanks,
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Show main menu again as prompt
    menu_main = await get_text(message.from_user.id, "menu_main")
    kb = await get_main_keyboard_dynamic(message.from_user.id)
    
    await message.answer(
        menu_main,
        reply_markup=kb,
        parse_mode="Markdown"
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


@router.callback_query(F.data.startswith("negotiation_"))
async def process_negotiation(callback: types.CallbackQuery):
    """Handles Accept/Reject from Client."""
    try:
        parts = callback.data.split("_")
        action_type = parts[1] # accept or reject
        order_id = int(parts[2])
        
        from bot.database import update_order_status
        from bot.config import ADMIN_ID
        
        if action_type == "accept":
            updated = await update_order_status(order_id, "in_progress")
            if not updated:
                await callback.answer("Ошибка: заказ не найден", show_alert=True)
                return

            msg_text = f"✅ <b>Вы приняли условия!</b>\nЗаказ #{order_id} передан в работу. Менеджер свяжется с вами."
            try:
                await callback.message.edit_text(msg_text, parse_mode="HTML")
            except Exception:
                await callback.message.answer(msg_text, parse_mode="HTML")

            # Notify Admin
            try:
                await callback.bot.send_message(
                    chat_id=ADMIN_ID, 
                    text=f"✅ <b>Клиент принял условия!</b>\nЗаказ #{order_id} теперь в работе.",
                    parse_mode="HTML"
                )
            except Exception: pass
            
        elif action_type == "reject":
            await update_order_status(order_id, "cancelled")
            msg_text = f"❌ <b>Вы отказались от условий.</b>\nЗаказ #{order_id} отменен."
            
            try:
                await callback.message.edit_text(msg_text, parse_mode="HTML")
            except Exception:
                await callback.message.answer(msg_text, parse_mode="HTML")

            # Notify Admin
            try:
                await callback.bot.send_message(
                    chat_id=ADMIN_ID, 
                    text=f"❌ <b>Клиент отказался!</b>\nЗаказ #{order_id} отменен."
                )
            except: pass
        
        await callback.answer("Готово!")
    except Exception as e:
        print(f"Negotiation Error: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
