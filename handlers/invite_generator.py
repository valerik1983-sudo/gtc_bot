from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database import get_user
from config import MAIN_BOT_USERNAME
from states import InviteState

import qrcode
import os
import re

router = Router()

# Список доступных источников
SOURCES = {
    "flyer": "📄 Листовка",
    "direct": "🤝 Личное приглашение",
    "ad": "📢 Реклама"
}


@router.message(F.text == "📝 Генератор приглашений")
async def invite_generator(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Приглашение на встречу", callback_data="invite_meeting")],
        [InlineKeyboardButton(text="🤖 Приглашение в Telegram бот", callback_data="invite_bot")],
        [InlineKeyboardButton(text="🌿 О продуктах для здоровья", callback_data="invite_health")],
        [InlineKeyboardButton(text="🦴 При боли в суставах", callback_data="invite_joints")],
        [InlineKeyboardButton(text="⚡ При отсутствии энергии", callback_data="invite_energy")],
        [InlineKeyboardButton(text="💊 При других болях", callback_data="invite_pain")],
        [InlineKeyboardButton(text="🎓 Доход для студентов", callback_data="invite_student")],
        [InlineKeyboardButton(text="👴 Общение и заработок для взрослых", callback_data="invite_elder")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_team_menu")]
    ])

    await message.answer(
        "📝 **Генератор приглашений**\n\n"
        "Выберите тип приглашения:\n\n"
        "📌 После выбора типа укажите источник, чтобы я сгенерировал ссылку с нужным параметром.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ---------- Обработчик выбора типа (переход к выбору источника) ----------
@router.callback_query(lambda c: c.data.startswith("invite_") and not c.data.startswith("invite_source_"))
async def invite_type_selected(callback: CallbackQuery, state: FSMContext):
    invite_type = callback.data.replace("invite_", "")
    await state.update_data(invite_type=invite_type)
    await state.set_state(InviteState.waiting_source)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"invite_source_{invite_type}_{key}")]
        for key, label in SOURCES.items()
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_invite_generator")
    ])

    await callback.message.edit_text(
        "📌 Выберите источник, откуда человек узнает о вас:",
        reply_markup=keyboard
    )
    await callback.answer()


# ---------- Обработчик выбора источника ----------
@router.callback_query(StateFilter(InviteState.waiting_source), lambda c: c.data.startswith("invite_source_"))
async def invite_source_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")  # invite_source_{type}_{source_key}
    invite_type = parts[2]
    source_key = parts[3]
    source_label = SOURCES.get(source_key, "direct")

    user = get_user(callback.from_user.id)
    user_name = user.get("fio", "Партнёр") if user else "Партнёр"

    # Формируем ссылку
    if source_key == "direct":
        link = f"https://t.me/{MAIN_BOT_USERNAME}?start={callback.from_user.id}"
    else:
        link = f"https://t.me/{MAIN_BOT_USERNAME}?start=sponsor_{callback.from_user.id}_source_{source_key}"

    # Генерируем QR-код для листовки
    qr_file = None
    if source_key == "flyer":
        qr = qrcode.make(link)
        qr_file = f"qr_{callback.from_user.id}_{source_key}.png"
        qr.save(qr_file)

    # ---------- Генерация текстов (все варианты с link) ----------
    if invite_type == "meeting":
        text1 = (f"🏢 **Приглашаю на деловую встречу!**\n\n"
                 f"Привет! Я {user_name}, партнёр Global Trend.\n"
                 f"Приглашаю тебя на встречу, где расскажу о возможностях дополнительного дохода.\n\n"
                 f"📅 Когда: [укажите дату]\n"
                 f"⏰ Во сколько: [укажите время]\n"
                 f"📍 Где: [укажите адрес или ссылку]\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Будет интересно и познавательно! Жду тебя! 🤝")
        text2 = (f"☕ **Давай встретимся!**\n\n"
                 f"Привет! Это {user_name}.\n"
                 f"Давно не виделись! Хочу рассказать тебе про интересный проект, "
                 f"который помогает людям быть здоровыми и зарабатывать.\n\n"
                 f"Встретимся за кофе, расскажу всё без обязательств.\n"
                 f"Ты ничего не теряешь, а узнать новое всегда полезно! 😊\n\n"
                 f"👉 [Подробнее]({link})")
        text3 = (f"🎤 **Приглашаю на презентацию!**\n\n"
                 f"Друзья! Я {user_name} приглашаю вас на презентацию продуктов Global Trend.\n\n"
                 f"🔹 Натуральные средства для здоровья\n"
                 f"🔹 Возможность дополнительного дохода\n"
                 f"🔹 Живое общение и знакомства\n\n"
                 f"📅 [дата]\n"
                 f"⏰ [время]\n\n"
                 f"👉 [Записаться]({link})\n\n"
                 f"Буду рад видеть каждого! 💚")
        text = (f"📋 **Выберите подходящий вариант приглашения на встречу:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "bot":
        text1 = (f"🤖 **Приглашаю в полезный Telegram бот!**\n\n"
                 f"Привет! Я {user_name}.\n"
                 f"Нашёл крутой бот, который помогает подобрать натуральные продукты для здоровья.\n\n"
                 f"📱 Просто перейди по ссылке и ответь на вопросы.\n"
                 f"Бот подберёт то, что нужно именно тебе!\n\n"
                 f"👉 [Перейти в бот]({link})")
        text2 = (f"🤖 **Привет! Посмотри, что я нашёл!**\n\n"
                 f"{user_name} рекомендует!\n\n"
                 f"Этот бот помогает:\n"
                 f"✅ Подобрать витамины и добавки\n"
                 f"✅ Узнать о натуральных продуктах\n"
                 f"✅ Получить консультацию специалиста\n\n"
                 f"Попробуй, это бесплатно и полезно! 👇\n\n"
                 f"👉 [Открыть бота]({link})")
        text3 = (f"🤖 **Коллеги, рекомендую!**\n\n"
                 f"Всем привет! Это {user_name}.\n\n"
                 f"Нашёл бот с натуральными продуктами для здоровья.\n"
                 f"У них реально качественная продукция, сам пользуюсь.\n\n"
                 f"Кому интересно - вот ссылка:\n"
                 f"👉 [Перейти]({link})\n\n"
                 f"Можете просто посмотреть, без обязательств. 😊")
        text = (f"📋 **Выберите вариант приглашения в бот:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "health":
        text1 = (f"🌿 **О качественных товарах для здоровья**\n\n"
                 f"Привет! Я {user_name}.\n\n"
                 f"Хочу поделиться продуктами Global Trend, которые помогают поддерживать здоровье.\n\n"
                 f"✅ Натуральные бальзамы и комплексы\n"
                 f"✅ Для иммунитета, энергии, красоты\n"
                 f"✅ Без химии и добавок\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Здоровье - это главное! 💚")
        text2 = (f"🌿 **Дорогие друзья!**\n\n"
                 f"Я {user_name} нашла/нашёл продукты, которые реально помогают.\n\n"
                 f"🔹 Натуральные средства\n"
                 f"🔹 Укрепляют иммунитет\n"
                 f"🔹 Поддерживают организм\n\n"
                 f"Рекомендую всем, кто заботится о здоровье.\n\n"
                 f"👉 [Посмотреть]({link})")
        text3 = (f"🌿 **Привет!**\n\n"
                 f"Ты знаешь, что я {user_name} интересуюсь здоровым образом жизни.\n"
                 f"Нашёл отличные натуральные продукты - бальзамы, витамины, комплексы.\n\n"
                 f"Качество реально хорошее, сам/сама использую.\n\n"
                 f"👉 [Подробнее здесь]({link})\n\n"
                 f"Может быть, и тебе пригодится! 😊")
        text = (f"📋 **Выберите вариант о продуктах для здоровья:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "joints":
        text1 = (f"🦴 **При болях в суставах**\n\n"
                 f"Привет! Я {user_name}.\n\n"
                 f"Знаю, что у тебя бывают боли в суставах. Я нашла/нашёл средство, которое помогает.\n\n"
                 f"🌿 Это натуральный продукт, который:\n"
                 f"✅ Снимает воспаление\n"
                 f"✅ Восстанавливает подвижность\n"
                 f"✅ Укрепляет хрящевую ткань\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Здоровье суставов - это возможность жить без боли! 🙏")
        text2 = (f"🦴 **Привет! Я нашёл решение для твоих суставов**\n\n"
                 f"{user_name} рекомендует.\n\n"
                 f"Я знаю, что ты мучаешься с суставами.\n"
                 f"Нашёл натуральный бальзам, который реально помогает - проверил на себе!\n\n"
                 f"👉 [Узнать как]({link})\n\n"
                 f"Не терпи боль, есть решение! 💪")
        text3 = (f"🦴 **Важно для суставов!**\n\n"
                 f"Друзья! Я {user_name} хочу поделиться находкой.\n\n"
                 f"Нашёл продукт, который помогает при болях в суставах.\n"
                 f"Натуральный состав, реально работает.\n\n"
                 f"👉 [Подробнее]({link})\n\n"
                 f"Поделитесь с теми, кому это может быть полезно! 🤝")
        text = (f"📋 **Выберите вариант при болях в суставах:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "energy":
        text1 = (f"⚡ **Если нет энергии**\n\n"
                 f"Привет! Я {user_name}.\n\n"
                 f"Заметил/заметила, что ты часто устаёшь и нет сил.\n"
                 f"Сама/сам через это проходила/проходил.\n\n"
                 f"Нашёл/нашла средство, которое возвращает энергию и бодрость!\n\n"
                 f"🌿 Натуральный комплекс, который:\n"
                 f"✅ Восстанавливает силы\n"
                 f"✅ Повышает тонус\n"
                 f"✅ Убирает усталость\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Хочешь жить энергично? Действуй! 💪")
        text2 = (f"⚡ **Верни энергию!**\n\n"
                 f"Привет! Это {user_name}.\n\n"
                 f"Устал/устала без сил? Знаю это состояние.\n"
                 f"Нашёл продукт, который реально заряжает энергией!\n\n"
                 f"✅ Натуральные компоненты\n"
                 f"✅ Без кофеина и стимуляторов\n"
                 f"✅ Бодрость на весь день\n\n"
                 f"👉 [Попробовать]({link})\n\n"
                 f"Жизнь должна быть энергичной! 🚀")
        text3 = (f"⚡ **Забота о твоей энергии**\n\n"
                 f"Друзья! Я {user_name} нашёл решение для тех, кто постоянно устаёт.\n\n"
                 f"🌿 Натуральный энергетический комплекс:\n"
                 f"• Повышает жизненный тонус\n"
                 f"• Улучшает работоспособность\n"
                 f"• Даёт бодрость без привыкания\n\n"
                 f"👉 [Узнать больше]({link})\n\n"
                 f"Твоя энергия - твоя жизнь! ✨")
        text = (f"📋 **Выберите вариант при отсутствии энергии:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "pain":
        text1 = (f"💊 **При болях любого характера**\n\n"
                 f"Привет! Я {user_name}.\n\n"
                 f"Знаю, что тебя беспокоят боли.\n"
                 f"Нашёл натуральные продукты, которые помогают справляться с болями разного происхождения.\n\n"
                 f"🌿 Это не лекарства, а натуральные средства, которые:\n"
                 f"✅ Снимают воспаление\n"
                 f"✅ Убирают дискомфорт\n"
                 f"✅ Восстанавливают организм\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Не терпи боль, есть решение! 🙏")
        text2 = (f"💊 **Я знаю, как тебе помочь**\n\n"
                 f"Привет! Это {user_name}.\n\n"
                 f"Я тоже мучился/мучилась с болями.\n"
                 f"Нашёл натуральные средства, которые реально убирают боль.\n\n"
                 f"✅ Без побочных эффектов\n"
                 f"✅ Натуральные компоненты\n"
                 f"✅ Результат заметен быстро\n\n"
                 f"👉 [Узнать как]({link})\n\n"
                 f"Поверь, тебе станет легче! 💚")
        text3 = (f"💊 **Важная рекомендация**\n\n"
                 f"Друзья! Я {user_name} хочу поделиться открытием.\n\n"
                 f"Нашёл натуральные продукты, которые помогают при болях:\n"
                 f"• В суставах\n"
                 f"• В мышцах\n"
                 f"• Головных болях\n"
                 f"• При воспалениях\n\n"
                 f"👉 [Подробнее]({link})\n\n"
                 f"Поделитесь с теми, кому может быть полезно! 🤝")
        text = (f"📋 **Выберите вариант при болях:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "student":
        text1 = (f"🎓 **Дополнительный доход для студентов**\n\n"
                 f"Привет! Я {user_name}.\n\n"
                 f"Знаю, как студенту трудно с деньгами.\n"
                 f"Сам/сама через это прошёл/прошла.\n\n"
                 f"Нашёл способ зарабатывать без опыта и вложений!\n\n"
                 f"✅ Работай из телефона\n"
                 f"✅ Удобное время\n"
                 f"✅ Обучение с нуля\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Первый шаг к финансовой свободе - здесь и сейчас! 💪")
        text2 = (f"🎓 **Привет, студент!**\n\n"
                 f"{user_name} рекомендует.\n\n"
                 f"Знаю, что тебе нужен дополнительный доход.\n"
                 f"Нашёл проект, где можно зарабатывать, совмещая с учёбой.\n\n"
                 f"✅ Опыт не нужен\n"
                 f"✅ Можно совмещать\n"
                 f"✅ Доход от 20000 руб/мес\n\n"
                 f"👉 [Узнать как]({link})\n\n"
                 f"Почему бы не попробовать? 😊")
        text3 = (f"🎓 **Студентам - реальный доход!**\n\n"
                 f"Друзья! Я {user_name}.\n\n"
                 f"Хочу поделиться возможностью для студентов:\n\n"
                 f"🔹 Заработок без вложений\n"
                 f"🔹 Гибкий график\n"
                 f"🔹 Помощь в обучении\n"
                 f"🔹 Постоянный доход\n\n"
                 f"👉 [Подробнее]({link})\n\n"
                 f"Зарабатывай уже сейчас! 🚀")
        text = (f"📋 **Выберите вариант приглашения для студентов:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    elif invite_type == "elder":
        text1 = (f"👴 **Общение и заработок для взрослых**\n\n"
                 f"Здравствуйте! Я {user_name}.\n\n"
                 f"Хочу поделиться возможностью для людей старшего поколения.\n\n"
                 f"🌿 Что вас ждёт:\n"
                 f"✅ Общение с интересными людьми\n"
                 f"✅ Новые знакомства\n"
                 f"✅ Дополнительный доход\n"
                 f"✅ Участие в полезном деле\n\n"
                 f"👉 [Узнать подробнее]({link})\n\n"
                 f"Жизнь только начинается! 💚")
        text2 = (f"👴 **Приглашаю в нашу команду!**\n\n"
                 f"Друзья! Это {user_name}.\n\n"
                 f"Для тех, кто хочет:\n"
                 f"✅ Общаться с людьми\n"
                 f"✅ Помогать другим\n"
                 f"✅ Получать доход\n"
                 f"✅ Быть полезным\n\n"
                 f"Мы ищем единомышленников!\n\n"
                 f"👉 [Присоединиться]({link})\n\n"
                 f"Вместе мы можем больше! 🤝")
        text3 = (f"👴 **Уважаемые друзья!**\n\n"
                 f"Я {user_name} приглашаю вас в нашу команду.\n\n"
                 f"Что мы предлагаем:\n"
                 f"🔹 Общение в дружеской атмосфере\n"
                 f"🔹 Возможность зарабатывать\n"
                 f"🔹 Помощь людям\n"
                 f"🔹 Новые цели и смыслы\n\n"
                 f"👉 [Узнать больше]({link})\n\n"
                 f"Никогда не поздно начать новую жизнь! ✨")
        text = (f"📋 **Выберите вариант для взрослого поколения:**\n\n"
                f"━━━ Вариант 1 ━━━\n{text1}\n\n"
                f"━━━ Вариант 2 ━━━\n{text2}\n\n"
                f"━━━ Вариант 3 ━━━\n{text3}")

    else:
        text = "❌ Неизвестный тип приглашения"

    # Если источник — Листовка, удаляем все markdown-ссылки из текста
    if source_key == "flyer":
        # Убираем ссылки в формате [текст](ссылка), оставляем только текст
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Также убираем лишние стрелки и пробелы, но оставляем читаемость

    # Кнопка "Назад"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к выбору", callback_data="back_to_invite_generator")]
    ])

    # Отправляем результат
    if qr_file and os.path.exists(qr_file):
        # Отправляем QR-код с подписью, затем текст без ссылок (или с ссылками, если не листовка)
        await callback.message.delete()  # удаляем старое сообщение с выбором источника
        await callback.message.answer_photo(
            FSInputFile(qr_file),
            caption="📱 **QR-код для листовки**\n\nОтсканируйте его, чтобы перейти в бот.",
            reply_markup=keyboard
        )
        # Отправляем текст приглашения (без ссылок, если листовка)
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        os.remove(qr_file)
    else:
        # Обычный текст с ссылками
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    await state.clear()
    await callback.answer()


# ---------- Кнопка "Назад" ----------
@router.callback_query(F.data == "back_to_invite_generator")
async def back_to_invite_generator(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await invite_generator(callback.message)
    await callback.answer()


@router.callback_query(F.data == "back_to_team_menu")
async def back_to_team_menu(callback: CallbackQuery):
    from keyboards import team_submenu
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "👥 Управление командой:",
        reply_markup=team_submenu
    )
    await callback.answer()