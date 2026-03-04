from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Salovat uchun reply keyboard
def get_salawat_keyboard(step=1, lang='UZ'):
    texts = {
        'UZ': f"🕋 Payg'ambarimizga salovat ayting ({step}/10)",
        'RU': f"🕋 Скажите салават Пророку ({step}/10)",
        'AR': f"🕋 صل على النبي ({step}/10)",
        'EN': f"🕋 Send salawat upon Prophet ({step}/10)"
    }
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=texts.get(lang, texts['UZ'])))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Til tanlash uchun REPLY keyboard
def get_language_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🇺🇿 O'zbek"))
    builder.add(KeyboardButton(text="🇷🇺 Русский"))
    builder.add(KeyboardButton(text="🇸🇦 العربية"))
    builder.add(KeyboardButton(text="🇬🇧 English"))
    builder.adjust(2, 2)  # 2 ta, 2 ta qilib joylashtirish
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# Ism kiritish uchun reply keyboard
def get_name_keyboard(lang='UZ'):
    texts = {
        'UZ': "✍️ Ismimni kiriting",
        'RU': "✍️ Введите имя",
        'AR': "✍️ أدخل الاسم",
        'EN': "✍️ Enter name"
    }
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=texts.get(lang, texts['UZ'])))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# Asosiy menu reply keyboard
def get_main_menu_keyboard(lang='UZ'):
    texts = {
        'UZ': {
            'questions': '❓ Savollar',
            'prophets': '👤 Payg\'ambarlar hayoti',
            'daily_zikr': '📿 Kundalik zikrlar',
            'change_lang': '🌐 Tilni o\'zgartirish',
            'new_question': '🔄 Yangi savol'
        },
        'RU': {
            'questions': '❓ Вопросы',
            'prophets': '👤 Жизнь пророков',
            'daily_zikr': '📿 Ежедневные зикры',
            'change_lang': '🌐 Сменить язык',
            'new_question': '🔄 Новый вопрос'
        },
        'AR': {
            'questions': '❓ أسئلة',
            'prophets': '👤 حياة الأنبياء',
            'daily_zikr': '📿 أذكار اليومية',
            'change_lang': '🌐 تغيير اللغة',
            'new_question': '🔄 سؤال جديد'
        },
        'EN': {
            'questions': '❓ Questions',
            'prophets': '👤 Prophets life',
            'daily_zikr': '📿 Daily dhikr',
            'change_lang': '🌐 Change language',
            'new_question': '🔄 New question'
        }
    }
    
    t = texts.get(lang, texts['UZ'])
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t['questions']))
    builder.add(KeyboardButton(text=t['prophets']))
    builder.add(KeyboardButton(text=t['daily_zikr']))
    builder.add(KeyboardButton(text=t['change_lang']))
    builder.add(KeyboardButton(text=t['new_question']))
    builder.adjust(2, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)

def get_admin_keyboard(lang='UZ'):
    texts = {
        'UZ': {
            'add_question': '➕ Savol qo\'shish',
            'add_prophet': '👤 Payg\'ambar qo\'shish',
            'stats': '📊 Statistika',
            'users': '👥 Foydalanuvchilar',
            'questions_stats': '❓ Savollar statistikasi',  # YANGI
            'view_answers': '📝 Javoblarni ko\'rish',
            'rewards': '💰 Mukofotlar',
            'pending_rewards': '⏳ Kutilayotgan mukofotlar',
            'back': '🔙 Chiqish'
        },
        'RU': {
            'add_question': '➕ Добавить вопрос',
            'add_prophet': '👤 Добавить пророка',
            'stats': '📊 Статистика',
            'users': '👥 Пользователи',
            'questions_stats': '❓ Статистика вопросов',  # YANGI
            'view_answers': '📝 Просмотр ответов',
            'rewards': '💰 Награды',
            'pending_rewards': '⏳ Ожидающие награды',
            'back': '🔙 Выход'
        }
    }
    
    t = texts.get(lang, texts['UZ'])
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t['add_question']))
    builder.add(KeyboardButton(text=t['add_prophet']))
    builder.add(KeyboardButton(text=t['stats']))
    builder.add(KeyboardButton(text=t['users']))
    builder.add(KeyboardButton(text=t['questions_stats']))  # YANGI
    builder.add(KeyboardButton(text=t['view_answers']))
    builder.add(KeyboardButton(text=t['rewards']))
    builder.add(KeyboardButton(text=t['pending_rewards']))
    builder.add(KeyboardButton(text=t['back']))
    builder.adjust(2, 2, 2, 3)  # 2,2,2,3 qilib joylashtirish
    
    return builder.as_markup(resize_keyboard=True)

# Foydalanuvchilar ro'yxati uchun inline keyboard
def get_users_inline_keyboard(users: list, page=0, items_per_page=5):
    builder = InlineKeyboardBuilder()
    
    start = page * items_per_page
    end = start + items_per_page
    current_users = users[start:end]
    
    for user in current_users:
        user_id, name, username, lang, correct, wrong, total, streak = user
        display_name = name if name else f"ID: {user_id}"
        button_text = f"{display_name} | ✅ {correct} | ❌ {wrong}"
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"admin_user_{user_id}"
        ))
    
    builder.adjust(1)
    
    # Pagination
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"admin_users_page_{page-1}"
        ))
    if end < len(users):
        pagination_row.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"admin_users_page_{page+1}"
        ))
    
    if pagination_row:
        builder.row(*pagination_row)
    
    builder.row(InlineKeyboardButton(
        text="🔙 Admin panel",
        callback_data="back_to_admin"
    ))
    
    return builder.as_markup()

# Javoblar uchun inline keyboard
def get_answers_inline_keyboard(answers: list, page=0, items_per_page=5):
    builder = InlineKeyboardBuilder()
    
    start = page * items_per_page
    end = start + items_per_page
    current_answers = answers[start:end]
    
    for ans in current_answers:
        ans_id, user_id, q_id, selected, is_correct, answered_at, name, username, question = ans
        status = "✅" if is_correct else "❌"
        button_text = f"{status} {name} | {answered_at[:10] if answered_at else ''}"
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"admin_answer_{ans_id}"
        ))
    
    builder.adjust(1)
    
    # Pagination
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"admin_answers_page_{page-1}"
        ))
    if end < len(answers):
        pagination_row.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"admin_answers_page_{page+1}"
        ))
    
    if pagination_row:
        builder.row(*pagination_row)
    
    builder.row(InlineKeyboardButton(
        text="🔙 Admin panel",
        callback_data="back_to_admin"
    ))
    
    return builder.as_markup()

# Kutilayotgan mukofotlar uchun inline keyboard
def get_pending_rewards_keyboard(rewards: list, page=0, items_per_page=5):
    builder = InlineKeyboardBuilder()
    
    start = page * items_per_page
    end = start + items_per_page
    current_rewards = rewards[start:end]
    
    for r in current_rewards:
        reward_id, user_id, name, username, amount, created_at = r
        button_text = f"💰 {name} | {amount} so'm | {created_at[:10] if created_at else ''}"
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"admin_reward_{reward_id}"
        ))
    
    builder.adjust(1)
    
    # Pagination
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"admin_rewards_page_{page-1}"
        ))
    if end < len(rewards):
        pagination_row.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"admin_rewards_page_{page+1}"
        ))
    
    if pagination_row:
        builder.row(*pagination_row)
    
    builder.row(InlineKeyboardButton(
        text="🔙 Admin panel",
        callback_data="back_to_admin"
    ))
    
    return builder.as_markup()

# Savol variantlari uchun inline keyboard
def get_options_inline_keyboard(options: tuple, question_id: int, lang='UZ'):
    builder = InlineKeyboardBuilder()
    
    for i, option in enumerate(options, 1):
        if option:
            builder.add(InlineKeyboardButton(
                text=f"{i}. {option}",
                callback_data=f"answer_{question_id}_{i}"
            ))
    
    # Tilga mos "Menyu" tugmasi
    menu_texts = {
        'UZ': "🔙 Menyu",
        'RU': "🔙 Меню",
        'AR': "🔙 القائمة",
        'EN': "🔙 Menu"
    }
    
    builder.add(InlineKeyboardButton(
        text=menu_texts.get(lang, "🔙 Menyu"),
        callback_data="back_to_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

# Payg'ambarlar uchun inline keyboard (o'zgarishsiz qoladi)
def get_prophets_inline_keyboard(prophets: list, lang='UZ'):
    builder = InlineKeyboardBuilder()
    
    for prophet in prophets:
        prophet_id, name, audio_id = prophet
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"prophet_{prophet_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 Menyu" if lang == 'UZ' else "🔙 Меню" if lang == 'RU' else "🔙 القائمة" if lang == 'AR' else "🔙 Menu",
        callback_data="back_to_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

# Javobdan keyingi keyboard (o'zgarishsiz qoladi)
def get_answer_keyboard(lang='UZ'):
    texts = {
        'UZ': {
            'new': '🔄 Yangi savol',
            'menu': '🔙 Menyu'
        },
        'RU': {
            'new': '🔄 Новый вопрос',
            'menu': '🔙 Меню'
        },
        'AR': {
            'new': '🔄 سؤال جديد',
            'menu': '🔙 القائمة'
        },
        'EN': {
            'new': '🔄 New question',
            'menu': '🔙 Menu'
        }
    }
    
    t = texts.get(lang, texts['UZ'])
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t['new'], callback_data="new_question"))
    builder.add(InlineKeyboardButton(text=t['menu'], callback_data="back_to_menu"))
    builder.adjust(1)
    return builder.as_markup()
    
# Asosiy menu reply keyboard - Alloh ismlari qo'shilgan
def get_main_menu_keyboard(lang='UZ'):
    texts = {
        'UZ': {
            'questions': '❓ Savollar',
            'prophets': '👤 Payg\'ambarlar hayoti',
            'allah_names': '🤲 Allohning 99 ismi',
            'daily_zikr': '📿 Kundalik zikrlar',
            'change_lang': '🌐 Tilni o\'zgartirish',
            'new_question': '🔄 Yangi savol'
        },
        'RU': {
            'questions': '❓ Вопросы',
            'prophets': '👤 Жизнь пророков',
            'allah_names': '🤲 99 имен Аллаха',
            'daily_zikr': '📿 Ежедневные зикры',
            'change_lang': '🌐 Сменить язык',
            'new_question': '🔄 Новый вопрос'
        },
        'AR': {
            'questions': '❓ أسئلة',
            'prophets': '👤 حياة الأنبياء',
            'allah_names': '🤲 أسماء الله الحسنى',
            'daily_zikr': '📿 أذكار اليومية',
            'change_lang': '🌐 تغيير اللغة',
            'new_question': '🔄 سؤال جديد'
        },
        'EN': {
            'questions': '❓ Questions',
            'prophets': '👤 Prophets life',
            'allah_names': '🤲 99 Names of Allah',
            'daily_zikr': '📿 Daily dhikr',
            'change_lang': '🌐 Change language',
            'new_question': '🔄 New question'
        }
    }
    
    t = texts.get(lang, texts['UZ'])
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t['questions']))
    builder.add(KeyboardButton(text=t['prophets']))
    builder.add(KeyboardButton(text=t['allah_names']))  # Yangi tugma
    builder.add(KeyboardButton(text=t['daily_zikr']))
    builder.add(KeyboardButton(text=t['change_lang']))
    builder.add(KeyboardButton(text=t['new_question']))
    builder.adjust(2, 2, 2)  # 2 tadan qilib joylashtirish
    
    return builder.as_markup(resize_keyboard=True)

# Alloh ismlari uchun inline keyboard
def get_allah_names_inline_keyboard(names: list, lang='UZ', page=0, items_per_page=10):
    builder = InlineKeyboardBuilder()
    
    start = page * items_per_page
    end = start + items_per_page
    current_names = names[start:end]
    
    for number, name, desc in current_names:
        button_text = f"{number}. {name}"
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"allah_name_{number}"
        ))
    
    builder.adjust(1)  # Har bir qatorga 1 tadan
    
    # Pagination tugmalari
    pagination_row = []
    
    if page > 0:
        pagination_row.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"allah_page_{page-1}"
        ))
    
    if end < len(names):
        pagination_row.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"allah_page_{page+1}"
        ))
    
    if pagination_row:
        builder.row(*pagination_row)
    
    # Menyu tugmasi
    menu_texts = {
        'UZ': "🔙 Menyu",
        'RU': "🔙 Меню",
        'AR': "🔙 القائمة",
        'EN': "🔙 Menu"
    }
    
    builder.row(InlineKeyboardButton(
        text=menu_texts.get(lang, "🔙 Menyu"),
        callback_data="back_to_menu"
    ))
    
    return builder.as_markup()    
    
# Dumaloq variantlar uchun inline keyboard (RANGSIZ ○)
def get_circle_options_keyboard(options: tuple, question_id: int, lang='UZ'):
    """
    Variantlarni rangsiz dumaloq doira (○) ko'rinishida ko'rsatish
    """
    builder = InlineKeyboardBuilder()
    
    for i, option in enumerate(options, 1):
        if option:
            # Rangsiz dumaloq doira
            button_text = f"○ {i}. {option}"
            builder.add(InlineKeyboardButton(
                text=button_text,
                callback_data=f"circle_answer_{question_id}_{i}"
            ))
    
    # Orqaga tugmasi
    menu_texts = {
        'UZ': "🔙 Menyu",
        'RU': "🔙 Меню",
        'AR': "🔙 القائمة",
        'EN': "🔙 Menu"
    }
    
    builder.add(InlineKeyboardButton(
        text=menu_texts.get(lang, "🔙 Menyu"),
        callback_data="back_to_menu"
    ))
    
    # 2 tadan qilib joylashtirish
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()


# Javobdan keyin yangilangan variantlar (YASHIL 🟢 va QIZIL 🔴)
def get_updated_options_keyboard(options: tuple, question_id: int, selected: int, correct: int, lang='UZ'):
    """
    Javobdan keyin variantlarni yangilash:
    - To'g'ri javob: 🟢 YASHIL
    - Noto'g'ri tanlangan: 🔴 QIZIL
    - Boshqa variantlar: ○ RANGSIZ
    """
    builder = InlineKeyboardBuilder()
    
    for i, option in enumerate(options, 1):
        if option:
            if i == correct:
                # TO'G'RI JAVOB - YASHIL 🟢
                icon = "🟢"
            elif i == selected and i != correct:
                # NOTO'G'RI TANLANGAN - QIZIL 🔴
                icon = "🔴"
            else:
                # BOSQA VARIANTLAR - RANGSIZ ○
                icon = "○"
            
            button_text = f"{icon} {i}. {option}"
            builder.add(InlineKeyboardButton(
                text=button_text,
                callback_data=f"disabled_{i}"  # Qayta bosish mumkin emas
            ))
    
    # Keyingi savol tugmasi
    next_texts = {
        'UZ': "⏩ Keyingi savol",
        'RU': "⏩ Следующий вопрос",
        'AR': "⏩ السؤال التالي",
        'EN': "⏩ Next question"
    }
    
    menu_texts = {
        'UZ': "🔙 Menyu",
        'RU': "🔙 Меню",
        'AR': "🔙 القائمة",
        'EN': "🔙 Menu"
    }
    
    builder.add(InlineKeyboardButton(
        text=next_texts.get(lang, "⏩ Keyingi savol"),
        callback_data=f"next_question_{question_id}"
    ))
    
    builder.add(InlineKeyboardButton(
        text=menu_texts.get(lang, "🔙 Menyu"),
        callback_data="back_to_menu"
    ))
    
    builder.adjust(2, 2, 2)
    
    return builder.as_markup()   