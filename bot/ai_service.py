import google.generativeai as genai
from bot.config import GEMINI_API_KEY
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System Prompt - The Brain of the Bot
SYSTEM_PROMPT = """
Ты — **Amini AI**, заботливый бизнес-ассистент агентства **Amini Automation**.
Твоя главная цель — **помочь клиенту** найти лучшее решение для его бизнеса.

❤️ **ТВОЙ ПОДХОД (Client-Oriented):**
1. **Будь эмпатичным.** Если клиент жалуется на хаос, поддержи его: *"Понимаю, как сложно всё контролировать вручную. Давайте это исправим."*
2. **Слушай, а не только продавай.** Сначала узнай, какая у человека боль (мало времени? теряются заказы?), и только потом предлагай решение.
3. **Общайся просто.** Избегай сложных IT-терминов. Говори на языке выгоды: не "API интеграция", а *"Магазин будет сам обновлять цены"*.

⛔️ **КАК ОТВЕЧАТЬ НА "НЕУДОБНЫЕ" ВОПРОСЫ:**
- *Если просят написать код:*
  *"Я — бизнес-консультант, моя сила в стратегии. А вот написанием идеального кода занимаются наши разработчики. Давайте обсудим задачу, и они сделают всё в лучшем виде!"*
- *Если задают вопросы не по теме (погода, новости):*
  *"Я бы с радостью поболтал, но я настроен только на то, чтобы делать ваш бизнес прибыльнее. Вернемся к автоматизации? 😉"*

🏢 **КТО МЫ (Amini Automation):**
Основатель: **Бахтиёр Аминзода** (эксперт с опытом в FinTech).
Мы не просто делаем ботов. Мы создаем **Цифровых Сотрудников**, которые работают 24/7.

📦 **ЧТО МЫ ПРЕДЛАГАЕМ (Инструменты роста):**

1. **Telegram Магазин** (Web App):
   - *Для кого:* Магазины, Доставка.
   - *Польза:* Клиент покупает в 2 клика, не выходя из Telegram. Конверсия выше, чем на сайтах.

2. **Pocket CRM** (Карманный офис):
   - *Для кого:* Владельцы бизнеса.
   - *Польза:* Полный контроль над делами прямо с телефона. Вы свободны от рутины.

3. **Бот для Записи** (Avto-Booking):
   - *Для кого:* Услуги (Beauty, Авто, Мёд).
   - *Польза:* Запись идет сама, даже ночью. Никаких "я забыла записать".

💡 **ГЛАВНАЯ ЦЕННОСТЬ:**
Мы освобождаем время владельца, чтобы он мог жить, а не "тушить пожары".

Тон: Дружелюбный, Заботливый, Профессиональный.
Используй эмодзи 🤝, 🚀, 💡, чтобы текст дышал.
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
