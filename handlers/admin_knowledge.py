from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database import is_admin
from services.knowledge_base import knowledge_base
from states import AdminKnowledge
import os

async def detect_intent(text: str) -> str:
    """Определяет намерение админа по тексту."""
    text_lower = text.lower()
    if any(word in text_lower for word in ["добавь продукт", "новый продукт", "добавить продукт", "хочу добавить продукт"]):
        return "add_product"
    if any(word in text_lower for word in ["добавь правило", "новое правило", "добавить правило", "хочу добавить правило"]):
        return "add_rule"
    if any(word in text_lower for word in ["обнови знания", "перезагрузи базу", "перезагрузить знания", "обновить знания"]):
        return "reload_kb"
    return None

async def start_admin_dialog(message: Message, state: FSMContext, intent: str):
    """Запускает диалог для админа в зависимости от намерения."""
    if intent == "add_product":
        await state.set_state(AdminKnowledge.waiting_product_name)
        await message.answer("Введите название продукта:")
    elif intent == "add_rule":
        await state.set_state(AdminKnowledge.waiting_rule_text)
        await message.answer("Введите текст правила:")
    elif intent == "reload_kb":
        knowledge_base.reload()
        await message.answer("✅ База знаний перезагружена.")

async def process_product_name(message: Message, state: FSMContext):
    """Обработчик для ввода названия продукта (вызывается из menu.py)."""
    await state.update_data(product_name=message.text.strip())
    await state.set_state(AdminKnowledge.waiting_product_description)
    await message.answer("Введите описание продукта:")

async def process_product_description(message: Message, state: FSMContext):
    """Обработчик для ввода описания продукта."""
    data = await state.get_data()
    name = data.get("product_name")
    description = message.text.strip()
    if not name or not description:
        await message.answer("Название и описание не могут быть пустыми. Попробуйте заново.")
        await state.clear()
        return
    filename = f"knowledge/products/{name}.txt"
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"{name}\n\n{description}")
        knowledge_base.reload()
        await message.answer(f"✅ Продукт '{name}' добавлен в базу знаний.")
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")
    await state.clear()

async def process_rule_text(message: Message, state: FSMContext):
    """Обработчик для ввода правила."""
    rule = message.text.strip()
    if not rule:
        await message.answer("Правило не может быть пустым. Попробуйте заново.")
        await state.clear()
        return
    filename = "knowledge/rules/main.txt"
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"\n{rule}")
        knowledge_base.reload()
        await message.answer(f"✅ Правило добавлено: {rule}")
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")
    await state.clear()