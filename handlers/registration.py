import asyncio
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database import add_user, get_user, get_sponsor, is_admin
from states import Registration
from keyboards import get_main_menu
from config import MAIN_BOT_TOKEN, CONSULT_BOT_USERNAME

router = Router()


@router.message(F.text == "📝 Регистрация")
async def start_registration(message: Message, state: FSMContext):
    print("🔴🔴🔴 НАЖАТА КНОПКА РЕГИСТРАЦИИ 🔴🔴🔴")  # Диагностика
    # Проверяем, не зарегистрирован ли уже пользователь
    user = get_user(message.from_user.id)
    if user:
        await message.answer("✅ Вы уже зарегистрированы!")
        return
    
    await state.set_state(Registration.fio)
    await message.answer(
        "📝 **Регистрация в системе Global Trend**\n\n"
        "Введите ваше ФИО (Имя и Фамилию):",
        parse_mode="Markdown"
    )


@router.message(Registration.fio)
async def get_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    if len(fio.split()) < 2:
        await message.answer("❌ Введите полное ФИО (Имя и Фамилию):")
        return
    
    await state.update_data(fio=fio)
    await state.set_state(Registration.birth_date)
    await message.answer("🎂 Введите вашу дату рождения (ДД.ММ.ГГГГ):")


@router.message(Registration.birth_date)
async def get_birth_date(message: Message, state: FSMContext):
    birth_date = message.text.strip()
    # Простая проверка формата
    if len(birth_date) < 8:
        await message.answer("❌ Введите дату в формате ДД.ММ.ГГГГ:")
        return
    
    await state.update_data(birth_date=birth_date)
    await state.set_state(Registration.phone)
    await message.answer("📱 Введите ваш номер телефона:")


@router.message(Registration.phone)
async def get_phone(message: Message, state: FSMContext):
    import re
    phone = re.sub(r'[^0-9+]', '', message.text)
    if len(phone) < 10:
        await message.answer("❌ Введите корректный номер телефона:")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(Registration.city)
    await message.answer("📍 Введите ваш город:")


@router.message(Registration.city)
async def get_city(message: Message, state: FSMContext):
    city = message.text.strip().title()
    await state.update_data(city=city)
    await state.set_state(Registration.gender)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]],
        resize_keyboard=True
    )
    await message.answer("👫 Выберите ваш пол:", reply_markup=keyboard)


@router.message(Registration.gender)
async def get_gender(message: Message, state: FSMContext):
    gender = message.text
    if gender not in ["Мужской", "Женский"]:
        await message.answer("❌ Выберите пол из предложенных вариантов:")
        return
    
    data = await state.get_data()

    # ===== 1. ПЫТАЕМСЯ ПОЛУЧИТЬ SPONSOR_ID ИЗ STATE =====
    sponsor_id = data.get("sponsor_id")
    
    # ===== 2. ЕСЛИ НЕТ В STATE — БЕРЁМ ИЗ TEMP_REFS =====
    if not sponsor_id:
        from database import get_temp_sponsor
        sponsor_id = get_temp_sponsor(message.from_user.id)
        print(f"🔵🔵🔵 ВЗЯЛИ SPONSOR_ID ИЗ TEMP_REFS: {sponsor_id}")
    
    '''# Получаем sponsor_id из реферальной ссылки (если есть)
    sponsor_id = None
    start_data = await state.get_data()
    if "sponsor_id" in start_data:
        sponsor_id = start_data["sponsor_id"]'''
    
    # ===== 3. СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ =====
    from database import add_user, clear_temp_sponsor
    add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        fio=data["fio"],
        birth_date=data["birth_date"],
        phone=data["phone"],
        city=data["city"],
        gender=gender,
        sponsor_id=sponsor_id
    )
    
    # ===== 4. УДАЛЯЕМ ВРЕМЕННУЮ СВЯЗЬ ПОСЛЕ РЕГИСТРАЦИИ =====
    if sponsor_id:
        clear_temp_sponsor(message.from_user.id)
    
    # Отправляем уведомление наставнику
    if sponsor_id:
        try:
            from aiogram import Bot
            from config import MAIN_BOT_TOKEN, CONSULT_BOT_USERNAME
            import asyncio
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            bot = Bot(token=MAIN_BOT_TOKEN)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="💬 Перейти в консультационный бот", 
                    url=f"https://t.me/{CONSULT_BOT_USERNAME}"
                )],
                [InlineKeyboardButton(
                    text="👥 Моя команда",
                    callback_data="my_team"
                )]
            ])
            
            message_text = (
                f"🆕 **Новый приглашённый!**\n\n"
                f"👤 **Имя:** {data['fio']}\n"
                f"📞 **Телефон:** {data['phone']}\n"
                f"🏙️ **Город:** {data['city']}\n"
                f"👫 **Пол:** {gender}\n"
                f"🎂 **Дата рождения:** {data['birth_date']}\n\n"
                f"✅ Пользователь зарегистрировался по вашей ссылке!\n\n"
                f"💡 **Важно:** Чтобы получать уведомления о консультациях, "
                f"перейдите однократно в [👉 консультационный бот](https://t.me/{CONSULT_BOT_USERNAME}?start=start)"
            )
            
            # Запускаем отправку в отдельной задаче
            asyncio.create_task(bot.send_message(
                sponsor_id,
                message_text,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            ))
        except Exception as e:
            print(f"Ошибка отправки уведомления наставнику: {e}")
    
    await state.clear()
    
    # Проверяем, нужно ли вернуться к диагностике
    data = await state.get_data()
    if data.get("pending_recommendations"):
        # Убираем флаг
        await state.update_data(pending_recommendations=False)
        # Показываем сообщение с кнопкой возврата к результату
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Посмотреть результат диагностики", callback_data="diag_back_to_result")]
        ])
        await message.answer(
            "✅ Вы успешно зарегистрировались!\n\n"
            "Теперь вы можете получить персональные рекомендации на основе диагностики.",
            reply_markup=keyboard
        )
        # Не показываем главное меню повторно, т.к. пользователь сам вернётся к диагностике
        return
    
    # Отправляем приветствие
    user = get_user(message.from_user.id)
    registered = user is not None
    has_team = False
    is_admin_user = is_admin(message.from_user.id)
    
    await message.answer(
        f"✅ **Регистрация завершена!**\n\n"
        f"Добро пожаловать, {data['fio']}!\n\n"
        f"Теперь вам доступны все возможности бота.",
        reply_markup=get_main_menu(registered, has_team, is_admin_user),
        parse_mode="Markdown"
    )


# Обработка реферальной ссылки при /start
@router.message(F.text.startswith("/start"))
async def handle_start_with_ref(message: Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) > 1:
        sponsor_id = parts[1]
        if sponsor_id.isdigit():
            await state.update_data(sponsor_id=int(sponsor_id))
    
    # Запускаем обычный start
    from main import start_command
    await start_command(message, state)