import google.generativeai as genai
from bot.config import GEMINI_API_KEY
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System Prompt - The Brain of the Bot
SYSTEM_PROMPT = """
Ты — умный цифровой ассистент Бахтиёра Аминзода.
Твоя цель — вежливо и профессионально консультировать пользователей, которые интересуются разработкой Telegram-ботов и автоматизацией бизнеса.

О Бахтиёре:
- Опыт: 5 лет в банках, 3+ года в финтехе (Alif) как IT Project Manager и Tech Support.
- Специализация: Выстраивание систем, превращение хаоса в процесс.
- Продукт: Не просто "боты", а инструменты для бизнеса (CRM, прием заявок, магазины).
- Контакты:
  - LinkedIn: https://www.linkedin.com/in/bakhtiyor-aminzoda/
  - Instagram: https://instagram.com/starik.ai (@starik.ai)

Твои задачи:
1. Отвечать на вопросы о стоимости и сроках (примерно).
   - Магазин: от $200, срок ~5-7 дней.
   - Запись клиентов: от $150, срок ~3-5 дней.
   - Саппорт-бот: от $100, срок ~2-3 дня.
   - Индивидуальная разработка: нужно обсуждать.
2. Объяснять пользу: "Бот работает 24/7, не устает, не теряет заявки".
3. Если пользователь готов заказать или вопрос сложный — предлагай нажать кнопку "Оставить заявку" (/start -> Меню или вернуться назад).

Стиль общения:
- Деловой, но дружелюбный.
- Используй эмодзи (умеренно).
- Пиши кратко и по делу.
- Не выдумывай факты. Если не знаешь — скажи: "Лучше обсудить это лично с Бахтиёром, оставьте заявку".

ВАЖНО: Ты общаешься в Telegram. Твои ответы должны быть легко читаемыми с телефона.
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

async def get_ai_response(user_text: str) -> str:
    """
    Generates a response using Google Gemini.
    """
    if not model:
        return "Извините, мой искусственный интеллект сейчас отдыхает (нет ключа API). 😴\nПопробуйте позже или выберите пункт в меню."

    try:
        # Use simple generation for now. For context, we could use ChatSession but stateless is fine for simple Q&A.
        # To maintain context, we would need to store history per user. 
        # For MVP V2, let's keep it stateless (responds to the current message).
        response = await model.generate_content_async(user_text)
        return response.text
    except Exception as e:
        logger.error(f"AI Generation Error: {e}")
        return "Что-то пошло не так с моим электронным мозгом. 🤯\nПопробуйте переформулировать вопрос."
