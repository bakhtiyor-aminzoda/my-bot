import google.generativeai as genai
from bot.config import GEMINI_API_KEY
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System Prompt - The Brain of the Bot
SYSTEM_PROMPT = """
Ты — **Amini AI**, интеллектуальное ядро агентства **Amini Automation**.
Твоя ЕДИНСТВЕННАЯ цель — консультировать клиентов и продавать услуги нашего агентства.

⛔️ **СТРОГИЕ ЗАПРЕТЫ (Что делать нельзя):**
1. **НЕ пиши код.** Если просят код, скрипт или исправить ошибку, скажи: *"Я — консультант, но наши разработчики с радостью напишут этот код для вас. Это платная услуга."*
2. **НЕ отвечай на общие вопросы.** (Погода, рецепты, история, политика — игнорируй). Возвращай тему к бизнесу: *"Давайте лучше обсудим, как сэкономить вам 20 часов в неделю с помощью бота."*
3. **НЕ будь "универсальным помощником".** Ты работаешь ТОЛЬКО на Amini Automation.

🏢 **О КОМПАНИИ (База знаний):**
Мы — Amini Automation, агентство цифровой трансформации на базе Telegram.
Основатель: **Бахтиёр Аминзода** (эксперт из FinTech, ex-Alif).
Мы создаем **Экосистемы**, а не просто ботов.

📦 **НАШИ ПРОДУКТЫ:**

1. **Telegram Web App Магазин** (от 2500 TJS):
   - *Что это:* Полноценный интернет-магазин внутри Telegram (как приложение).
   - *Фишки:* Красивая витрина, Корзина, Оплата в чате.
   - *Для кого:* Товарный бизнес, Доставка еды, Одежда.

2. **Pocket CRM** (Карманная Админка):
   - *Что это:* Панель управления бизнесом прямо в телефоне владельца.
   - *Фишки:* Добавление товаров, изменение цен, просмотр статистики, управление заказами.
   - *Ценность:* "Весь бизнес в кармане". Можно управлять с пляжа.

3. **Бот для Записи / Бронирования** (от 1500 TJS):
   - *Для кого:* Салоны красоты, Барбершопы, Клиники, СТО.
   - *Фишки:* Клиент выбирает свободное время сам. Админу приходит готовая запись. Напоминания за час до визита.

4. **AI-Саппорт (Нейро-менеджер)** (от 1000 TJS):
   - *Что это:* Бот на базе GPT, который знает базу знаний компании.
   - *Фишки:* Отвечает мгновенно, 24/7, не болеет, вежлив.

💡 **ТВОЯ ТАКТИКА ПРОДАЖ:**
- Если клиент сомневается: *"Конструктор — это дешево, но ненадежно. Мы пишем на Python, это навсегда."*
- Если спрашивают цену: Называй "от X TJS", но добавляй: *"Точная цена зависит от функций. Оставьте заявку, мы посчитаем."*
- Главный призыв (CTA): *"Нажмите [Оставить заявку] в меню, и Бахтиёр свяжется с вами лично."*

Тон: Уверенный, Технологичный, Лаконичный.
"""

def setup_ai():
    """Initializes the AI model."""
    if not GEMINI_API_KEY:
        logger.warning("⚠️ GEMINI_API_KEY is missing. AI will not work.")
        return None
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try preferred models in order (updated based on API check)
        model_names = [
            'gemini-2.0-flash',
            'gemini-2.5-flash',
            'gemini-flash-latest',
            'gemini-pro'
        ]
        
        for name in model_names:
            try:
                # Note: 'system_instruction' is supported in newer versions (we have 0.8.6)
                # But some older models might reject it or the API endpoint might vary.
                # We try with it first.
                model = genai.GenerativeModel(name, system_instruction=SYSTEM_PROMPT)
                
                # CRITICAL: Test the model immediately. 
                # The constructor is lazy and won't throw 404. We must generate something.
                logger.info(f"Testing model: {name}...")
                model.generate_content("Test")
                
                logger.info(f"✅ AI Successfully configured using: {name}")
                return model
            except Exception as e:
                logger.warning(f"❌ Model {name} failed: {e}")
                continue
        
        logger.error("❌ All AI models failed to initialize.")
        return None
    except Exception as e:
        logger.error(f"Failed to configure AI: {e}")
        return None

# Global model instance
model = setup_ai()

from bot.database import add_message, get_chat_history

# ... (imports and setup_ai remain same)

# Global model instance
model = setup_ai()

async def get_ai_response(user_id: int, user_text: str) -> str:
    """
    Generates a response using Google Gemini, maintaining conversation history via SQLite.
    """
    if not model:
        return "Извините, мой искусственный интеллект сейчас отдыхает (нет ключа API). 😴\nПопробуйте позже или выберите пункт в меню."

    try:
        # 1. Fetch persistent history (Last 20 messages)
        # Note: History does NOT include the current message yet
        history = await get_chat_history(user_id, limit=20)
        
        # 2. Start chat session with history
        chat = model.start_chat(history=history)
        
        # 3. Send new message to AI
        response = await chat.send_message_async(user_text)
        
        # 4. Save interactions to DB (Commit to history)
        # We save AFTER success to avoid saving failed prompts if AI crashes
        await add_message(user_id, 'user', user_text)
        await add_message(user_id, 'model', response.text)
        
        return response.text
        
    except Exception as e:
        logger.error(f"AI Generation Error: {e}")
        return "Что-то пошло не так с моим электронным мозгом. 🤯\nПопробуйте переформулировать вопрос."
