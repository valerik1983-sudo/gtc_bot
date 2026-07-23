import logging
import re
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from services.llm_client import LLMClient
from services.knowledge_base import knowledge_base
from services.memory import memory
from services.profile_manager import profile_manager
from database import get_user
from config import AI_ENABLED

logger = logging.getLogger(__name__)

llm_client = LLMClient()

SYSTEM_PROMPT_TEMPLATE = """
Ты — AI-консультант компании. Помогай людям с вопросами о продуктах, бизнесе и общих вопросах.

ПРАВИЛА (строго соблюдай):
1. НЕ ставь диагнозы, НЕ обещай лечение. Используй формулировки: "может использоваться для поддержки", "рекомендуется как часть комплексного подхода", "может помочь улучшить".
2. НЕ придумывай факты. Используй ТОЛЬКО информацию из базы знаний.
3. Задавай уточняющие вопросы, чтобы лучше понять ситуацию.
4. Отвечай дружелюбно и поддерживающе.
5. Можешь предложить следующий шаг: пройти диагностику, посмотреть каталог, зарегистрироваться, связаться с наставником.
6. Если не знаешь ответа – скажи честно и предложи обратиться к живому наставнику.
7. Если пользователь просит личную консультацию или задаёт медицинский вопрос, предложи передать запрос наставнику.

{profile_info}

База знаний:
{knowledge}

Теперь ответь пользователю.
"""


async def handle_ai_request(message: Message, state: FSMContext):
    print(f"🔍 Using model: {llm_client.model}")
    if not AI_ENABLED:
        return

    user_id = message.from_user.id
    text = message.text
    if not text:
        return

    current_state = await state.get_state()
    if current_state is not None:
        return

    # Сохраняем сообщение
    memory.add_message(user_id, "user", text)

    # Извлечение фактов
    profile_updates = {}
    user_text = text.lower()
    age_match = re.search(r'мне\s+(\d+)\s*лет', user_text)
    if age_match:
        profile_updates["age"] = int(age_match.group(1))
    name_match = re.search(r'(?:зовут|меня зовут)\s+(\w+)', user_text)
    if name_match:
        profile_updates["name"] = name_match.group(1).capitalize()
    if profile_updates:
        profile_manager.update_profile(user_id, profile_updates)

    # Загружаем профиль
    profile = profile_manager.get_profile(user_id)
    profile_info = ""
    if profile.get("name"):
        profile_info += f"👤 Имя пользователя: {profile['name']}\n"
    if profile.get("age"):
        profile_info += f"🎂 Возраст: {profile['age']}\n"
    if profile.get("city"):
        profile_info += f"🏙️ Город: {profile['city']}\n"

    user = get_user(user_id)
    if user and user.get('sponsor_id'):
        sponsor = get_user(user['sponsor_id'])
        if sponsor:
            sponsor_name = sponsor.get('fio', 'Наставник')
            sponsor_username = sponsor.get('username')
            if sponsor_username:
                profile_info += f"👨‍🏫 Ваш наставник: {sponsor_name} (@{sponsor_username})\n"
            else:
                profile_info += f"👨‍🏫 Ваш наставник: {sponsor_name}\n"

    if profile_info:
        profile_info = f"Информация о пользователе (используй её для персонализации):\n{profile_info}"
    else:
        profile_info = ""

    # Получаем историю
    history = memory.get_history(user_id, limit=10)

    # Формируем промпт
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        profile_info=profile_info,
        knowledge=knowledge_base.search(text)
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append(msg)

    try:
        response = await llm_client.generate_response(messages)
        memory.add_message(user_id, "assistant", response)

        # ---- Проверяем, нужно ли передать наставнику ----
        forward_to_mentor = False
        if "не знаю" in response.lower() or "не могу ответить" in response.lower():
            forward_to_mentor = True
        if any(word in text.lower() for word in ["наставник", "живой человек", "поговорить с человеком"]):
            forward_to_mentor = True
            response += "\n\nЯ передам ваш вопрос наставнику. Хотите, чтобы я создал заявку на консультацию? (Ответьте «да» или «нет»)"

        # Если нужно передать наставнику, предлагаем кнопку
        if forward_to_mentor:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да, создать заявку", callback_data=f"consult_request_{user_id}")]
            ])
            await message.answer(response, reply_markup=keyboard)
        else:
            await message.answer(response)

    except Exception as e:
        logger.error(f"AI error for user {user_id}: {e}")
        await message.answer(
            "Извините, произошла ошибка. Попробуйте позже или обратитесь к наставнику."
        )