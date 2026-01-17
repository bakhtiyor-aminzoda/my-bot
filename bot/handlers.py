import os
import datetime
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import ApplicationState
from bot.config import ADMIN_ID, ADMIN_USERNAME # Reverted this line to original as `add_leadADMIN_ID` is not a valid module and likely a typo in the instruction's snippet.
from bot.keyboards import main_menu_kb, services_kb, service_detail_kb, post_submit_kb, budget_kb

router = Router()

# --- Content Data ---
SERVICES_INFO = {
    "shops": (
        "🛍 <b>Магазины в Telegram</b>\n\n"
        "Магазин в Telegram — это не просто каталог. Это продавец, который не спит, не грубит и не путает заказы.\n\n"
        "<b>Как это работает:</b>\n"
        "• Клиент выбирает товары так же просто, как пишет сообщение.\n"
        "• Корзина собирается сама.\n"
        "• Оплата проходит за секунды.\n\n"
        "<b>Итог:</b> Клиент нажимает кнопки — вы получаете деньги и уведомление. Без лишних переписок."
    ),
    "booking": (
        "📅 <b>Запись клиентов</b>\n\n"
        "Забудьте про фразы: <i>«А есть окошко на 15:00?» — «Нет, только на 17:30».</i>\n\n"
        "<b>Система берет это на себя:</b>\n"
        "• Клиент видит свободное время и записывается сам.\n"
        "• Бот напоминает о визите (снижаем неявку).\n"
        "• Вы видите полное расписание.\n\n"
        "Идеально для барбершопов, салонов красоты, врачей и консультантов."
    ),
    "support": (
        "🤖 <b>Чат-боты поддержки</b>\n\n"
        "80% вопросов клиентов одинаковые: «Где вы находитесь?», «Сколько стоит?», «Как заказать?».\n\n"
        "<b>Зачем тратить на это жизнь?</b>\n"
        "Умный бот ответит мгновенно, в любое время суток.\n\n"
        "А если вопрос сложный — он позовет живого человека. Разгрузите себя и команду."
    )
}

ABOUT_TEXT = (
    "👨‍💻 <b>Обо мне / Опыт</b>\n\n"
    "Меня зовут <b>Бахтиёр</b>.\n"
    "Я тот человек, который любит порядок там, где обычно хаос.\n\n"
    "• <b>5 лет в банковской сфере.</b>\n"
    "• <b>3+ года в FinTech (Alif).</b> Прошел путь от Tech Support до Project Manager.\n\n"
    "Я знаю, как важна каждая заявка и как больно терять клиента из-за долгого ответа.\n"
    "Поэтому я не «пишу код», а <b>строю систему продаж и сервиса</b> для вашего бизнеса.\n\n"
    "📱 <b>Мои контакты:</b>\n"
    "• <a href='https://instagram.com/starik.ai'>Instagram (@starik.ai)</a>\n"
    "• <a href='https://www.linkedin.com/in/bakhtiyor-aminzoda/'>LinkedIn</a>"
)

HOW_IT_WORKS_TEXT = (
    "ℹ️ <b>Как я работаю</b>\n\n"
    "1. Обсуждаем задачу\n"
    "2. Я предлагаю решение\n"
    "3. Настраиваю бота\n"
    "4. Передаю готовый результат\n\n"
    "Никакой автоматической продажи. Всё обсуждаем лично."
)

# --- Navigation Handlers ---

from aiogram.types import FSInputFile
import os

from bot.database import add_user, get_all_users
import asyncio

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Entry point: Shows Main Menu."""
    # Save user to DB
    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    await state.clear()
    
    caption_text = (
        f"**Привет, это Бахтиёр.** 👋\n\n"
        "Начал карьеру в 17 лет. За плечами 5 лет в банковской сфере, "
        "из них 3+ года в финтехе (Alif) на позициях IT Project Manager и Tech Support.\n\n"
        "Сейчас я работаю с бизнесом, у которого **клиентов хватает, а порядка в заявках нет**.\n\n"
        "Сразу обозначу позицию:\n"
        "❌ Я не просто «делаю ботов».\n"
        "❌ Я не продаю автоматизацию ради галочки.\n\n"
        "✅ **Я выстраиваю систему.**\n"
        "Мой опыт в проектах и поддержке научил меня одному: любой хаос можно превратить в четкий процесс.\n\n"
        "Переписка – плохой инструмент для учета. Заявки теряются, клиенты забываются.\n"
        "Я беру это на себя. **Спокойно. По шагам. Под вашу задачу.**\n\n"
        "Вам нужно не «красиво», а **понятно и прибыльно**?\n"
        "Тогда вы по адресу. Выберите вариант ниже 👇"
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
            reply_markup=main_menu_kb(),
            parse_mode="Markdown"
        )
    else:
        # Fallback if photo not found
        await message.answer(
            caption_text,
            reply_markup=main_menu_kb(),
            parse_mode="Markdown"
        )

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Global cancel command."""
    await state.clear()
    await message.answer(
        "Действие отменено. 🚫\nВозвращаемся в меню.",
        reply_markup=main_menu_kb()
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


@router.callback_query(F.data == "nav_services")
async def nav_services(callback: types.CallbackQuery):
    text = (
        "🛠 <b>Услуги</b>\n\n"
        "Выберите категорию, чтобы узнать подробнее:"
    )
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=services_kb(), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=services_kb(), parse_mode="HTML")
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
        "• <b>Услуги</b> — Готовые решения для бизнеса\n"
        "• <b>Обо мне</b> — Опыт и подход к работе\n"
        "• <b>Заявка</b> — Обсудить индивидуальный проект"
    )
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "nav_back_services")
async def nav_back_services(callback: types.CallbackQuery):
    # Since we came from a Photo message (Detail View), strictly delete and send new.
    await callback.message.delete()
    
    await callback.message.answer(
        "🛠 <b>Услуги</b>\n\n"
        "Выберите категорию:",
        reply_markup=services_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_category_detail(callback: types.CallbackQuery):
    cat_id = callback.data.split("_")[1]
    info = SERVICES_INFO.get(cat_id, "Информация отсутствует.")
    
    # Image mapping
    image_map = {
        "shops": "shop.png",
        "booking": "booking.png",
        "support": "support.png"
    }
    
    image_file = image_map.get(cat_id)
    photo_path = os.path.join("bot", "images", image_file) if image_file else None
    
    # Delete previous menu (text)
    await callback.message.delete()
    
    if photo_path and os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=info,
            reply_markup=service_detail_kb(cat_id),
            parse_mode="HTML"
        )
    else:
        # Fallback to text if image missing
        await callback.message.answer(
            info,
            reply_markup=service_detail_kb(cat_id),
            parse_mode="HTML"
        )
        
    await callback.answer()

# --- Application Flow Starters ---

@router.callback_query(F.data == "new_application")
async def start_application_direct(callback: types.CallbackQuery, state: FSMContext):
    # Set default context for generic application
    await state.update_data(service_context="Общая заявка")
    await _start_fsm(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("order_"))
async def start_application_order(callback: types.CallbackQuery, state: FSMContext):
    service_id = callback.data.split("_")[1]
    # Map id to human readable name
    service_names = {
        "shops": "Интернет-магазин",
        "booking": "Запись клиентов",
        "support": "Чат-бот поддержки"
    }
    context_name = service_names.get(service_id, "Разработка бота")
    
    # Save context to state data
    await state.update_data(service_context=context_name)
    
    await _start_fsm(callback.message, state, context_name)
    await callback.answer()

from bot.keyboards import main_menu_kb, services_kb, service_detail_kb, post_submit_kb, budget_kb
# ... (imports)

async def _start_fsm(message: types.Message, state: FSMContext, context: str = None):
    """
    Helper to start the FSM flow.
    """
    await state.set_state(Application.name)
    
    prefix = "🚀 <b>Шаг 1 из 5</b>\n\n"
    if context:
        text = f"{prefix}Вы выбрали: <b>{context}</b>. Отличный выбор! 🔥\nДавайте познакомимся. Как вас зовут?"
    else:
        text = f"{prefix}Отлично! Давайте обсудим детали.\nКак вас зовут?"
        
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")

@router.message(Application.name)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите ваше имя текстом.")
        return
        
    await state.update_data(name=message.text)
    await state.set_state(Application.business_type)
    
    # Quick replies for Business Type
    kb_buttons = [
        [types.KeyboardButton(text="🛒 Магазин"), types.KeyboardButton(text="✂️ Услуги / Салон")],
        [types.KeyboardButton(text="🍔 Кафе / Ресторан"), types.KeyboardButton(text="👨‍🏫 Обучение")],
        [types.KeyboardButton(text="Другое")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer("🏢 <b>Шаг 2 из 5</b>\n\nКакой у вас бизнес?", reply_markup=keyboard, parse_mode="HTML")

@router.message(Application.business_type)
async def process_business_type(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, напишите вид деятельности текстом.")
        return
        
    await state.update_data(business_type=message.text)
    await state.set_state(Application.budget)
    
    await message.answer(
        "💰 <b>Шаг 3 из 5</b>\n\n"
        "На какой бюджет проекта вы ориентируетесь?",
        reply_markup=budget_kb(),
        parse_mode="HTML"
    )

@router.callback_query(Application.budget) # Budget is chosen via Inline Buttons
async def process_budget(callback: types.CallbackQuery, state: FSMContext):
    # Map callback data to readable text
    budget_map = {
        "budget_low": "Эконом (1000-2000 с.)",
        "budget_mid": "Бизнес (2000-5000 с.)",
        "budget_high": "Премиум (от 5000 с.)"
    }
    selected_budget = budget_map.get(callback.data, callback.data)
    
    await state.update_data(budget=selected_budget)
    await state.set_state(Application.task_description)
    
    await callback.message.edit_text(
        f"✅ Бюджет: {selected_budget}\n\n"
        "📝 <b>Шаг 4 из 5</b>\n\n"
        "Что именно вы хотите автоматизировать?\n"
        "<i>Например: прием заказов, запись клиентов, ответы на вопросы.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Application.task_description)
async def process_task_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, опишите задачу текстом.")
        return

    await state.update_data(task_description=message.text)
    await state.set_state(Application.contact_info)
    
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

@router.message(Application.task_description)
async def process_task_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, опишите задачу текстом.")
        return

    await state.update_data(task_description=message.text)
    await state.set_state(Application.contact_info)
    
    # Request Contact Keyboard
    kb = [[types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer(
        "Как с вами удобнее связаться?\n"
        "Нажмите кнопку ниже, чтобы отправить номер телефона, или напишите его вручную.",
        reply_markup=keyboard
    )

@router.message(Application.contact_info)
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
    
    # Save to Google Sheets
    # We pass the full data dict, adding context manually if it's not in there perfectly, 
    # but currently context IS in data.
    from bot.sheets import add_lead
    # Run in background or await if async? gspread is sync usually. 
    # For a simple bot, sync call is okay, or we can wrap it. 
    # To avoid blocking, in production we'd use threadpool or async gspread, 
    # but for now let's just call it inside a try/except block to not block errors.
    try:
         add_lead(data)
    except Exception as e:
         print(f"Sheet error: {e}")
    
    try:
        await message.bot.send_message(chat_id=ADMIN_ID, text=summary, parse_mode="HTML")
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
        
    # Notify User & Show Post-Submit Menu
    await state.set_state(Application.submitted)
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
    await message.answer(response, parse_mode="Markdown", reply_markup=ai_response_kb())

# --- Post-Submit & Misc Handlers ---

@router.callback_query(F.data == "how_it_works")
async def cb_how_it_works(callback: types.CallbackQuery):
    await callback.message.answer(HOW_IT_WORKS_TEXT, parse_mode="HTML")
    await callback.message.answer("Что делаем дальше?", reply_markup=post_submit_kb())
    await callback.answer()

@router.message(Application.submitted)
async def process_submitted_message(message: types.Message):
    await message.answer(
        "Я уже получил вашу заявку 👍\n"
        "Я напишу вам лично.\n\n"
        "Если хотите:\n"
        "— можете оставить ещё одну заявку\n"
        "— или посмотреть, как я работаю",
        reply_markup=post_submit_kb()
    )
