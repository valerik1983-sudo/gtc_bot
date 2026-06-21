from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def consultation_keyboard(
    consultation_id,
    in_work=False
):

    keyboard = []

    if not in_work:

        keyboard.append([
            InlineKeyboardButton(
                text="✅ Взял в работу",
                callback_data=f"work_{consultation_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="💬 Написать клиенту",
            callback_data=f"msg_{consultation_id}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="📞 Связался",
            callback_data=f"call_{consultation_id}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="🎉 Стал клиентом",
            callback_data=f"client_{consultation_id}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="🤝 Стал партнером",
            callback_data=f"partner_{consultation_id}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="❌ Не отвечает",
            callback_data=f"failed_{consultation_id}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )