from aiogram import Router
from aiogram import Bot
from aiogram.filters import StateFilter

from aiogram.types import (
    Message,
    CallbackQuery
)

from aiogram.fsm.context import FSMContext

from states import AdminComplaintReply

from database import (
    get_admins,
    get_last_consultation
)

from inline_keyboards import (
    complaint_keyboard
)

router = Router()

@router.message(lambda m: m.text == "❗ Мне не ответили")
async def no_answer(
    message: Message,
    bot: Bot
):

    consultation = get_last_consultation(
        message.from_user.id
    )

    if not consultation:

        await message.answer(
            "У вас пока нет заявок."
        )

        return

    admins = get_admins()

    for admin in admins:

        try:
        
            await bot.send_message(
                admin["telegram_id"],
                f"⚠️ Жалоба\n\n"
                f"Клиент:\n"
                f"{message.from_user.id}\n"           
                f"@{message.from_user.username}\n"                           
                f"{message.from_user.full_name}\n\n"
                f"Причина:\n"
                f"Не получил ответ."
            )

        except Exception as e:
            print(f"Ошибка отправки жалобы админу {admin['telegram_id']}: {e}")

    await message.answer(
        "✅ Сообщение отправлено администрации."
    )
@router.callback_query(
    lambda c:
    c.data.startswith(
        "complaint_msg_"
    )
)
async def complaint_message_start(
    callback: CallbackQuery,
    state: FSMContext
):

    client_id = int(
        callback.data.replace(
            "complaint_msg_",
            ""
        )
    )

    await state.update_data(
        client_id=client_id
    )

    await state.set_state(
        AdminComplaintReply.waiting_text
    )

    await callback.message.answer(
        "Введите сообщение клиенту:"
    )

    await callback.answer()

@router.message(
    AdminComplaintReply.waiting_text
)
async def complaint_message_send(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    client_id = data["client_id"]

    await message.bot.send_message(
        client_id,
        "📩 Сообщение от администрации\n\n"
        f"{message.text}"
    )

    await message.answer(
        "Сообщение отправлено ✅"
    )

    await state.clear()

@router.callback_query(
    lambda c:
    c.data.startswith(
        "complaint_close_"
    )
)
async def complaint_close(
    callback: CallbackQuery
):

    await callback.message.answer(
        "Жалоба закрыта ✅"
    )

    await callback.answer()
    
from database import get_consultation, get_user

@router.callback_query(lambda c: c.data.startswith("complaint_timeout_"))
async def timeout_complaint(callback: CallbackQuery, bot: Bot):
    consultation_id = int(callback.data.split("_")[2])
    consultation = get_consultation(consultation_id)
    
    if not consultation:
        await callback.answer("Заявка не найдена.")
        return
    
    # Отправляем админу (вам)
    admins = get_admins()
    
    client = get_user(consultation["client_telegram_id"])
    
    for admin in admins:
        try:
            await bot.send_message(
                admin["telegram_id"],
                f"⚠️ **ЖАЛОБА НА ОТСУТСТВИЕ ОТВЕТА**\n\n"
                f"👤 Клиент: {client['fio']}\n"
                f"🆔 Telegram ID: {client['telegram_id']}\n"
                f"📞 Телефон: {consultation['phone']}\n"
                f"📝 Тема: {consultation['topic']}\n"
                f"⏰ Создана: {consultation['created_at']}\n\n"
                f"Наставник не ответил более 3 часов.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки жалобы админу: {e}")
    
    await callback.message.edit_text(
        "✅ Жалоба отправлена администрации.\n"
        "Мы свяжемся с вами в ближайшее время."
    )
    
    await callback.answer("Жалоба отправлена")            