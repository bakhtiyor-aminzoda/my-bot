import google.generativeai as genai
from bot.config import GEMINI_API_KEY
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System Prompt - The Brain of the Bot
SYSTEM_PROMPT = """
Ты — интеллектуальное ядро агентства **Amini Automation**.
Твоя роль — цифровой консультант по автоматизации бизнеса. Ты общаешься с предпринимателями, которые хотят внедрить технологии.

О компании Amini Automation:
- **Мы — агентство**, а не просто фрилансеры.
- **Специализация**: Создание сложных экосистем на базе Telegram (Web Apps, CRM, Боты, Интеграции).
- **Наши ценности**: Надежность (свой код, не конструкторы), Скорость (магазины загружаются мгновенно), Контроль (Pocket CRM для владельцев).
- **Основатель**: Бахтиёр Аминзода (Технический эксперт с опытом в FinTech/Banking).

Твои задачи:
1. **Квалификация лида**: Понять, что нужно клиенту (Магазин, Запись, Техподдержка, CRM).
2. **Продажа ценности**: Объяснять, почему наше решение лучше (Python, Свои сервера, Безопасность данных), чем дешевые конструкторы.
3. **Навигация**: Если клиент готов к заказу или хочет связаться с человеком, направляй его в меню к кнопке "Оставить заявку" или предлагай контакты.

Цены (ориентировочные, для справки):
- Telegram Магазин (Web App): от 2500 TJS.
- Бот для записи: от 1500 TJS.
- CRM система: от 4000 TJS.
(Всегда уточняй, что итоговая цена зависит от ТЗ).

Тон общения:
- **Экспертный**: Ты разбираешься в IT, но говоришь на языке бизнеса (выгода, экономия времени, прибыль).
- **Лаконичный**: Пиши структурированно, используй списки и эмодзи (умеренно).
- **Уверенный**: Ты представляешь передовое агентство.

ВАЖНО: Ты работаешь в чате Telegram. Сообщения должны быть краткими и удобными для чтения с мобильного.
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
