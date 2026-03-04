import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, Update
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
import sys
from datetime import datetime
from googletrans import Translator
from flask import Flask, request, jsonify, Request  # Request qo'shildi!
import threading

from database import Database
from keyboards import *
from keep_alive import keep_alive

# Translator
translator = Translator()

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')

# Admin ID larni parse qilish
ADMIN_IDS = []
if ADMIN_IDS_STR:
    for id_str in ADMIN_IDS_STR.split(','):
        try:
            if id_str.strip().isdigit():
                ADMIN_IDS.append(int(id_str.strip()))
        except:
            pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize database
db = Database()

# States
class RegisterState(StatesGroup):
    waiting_for_name = State()

# Admin States
class AddQuestion(StatesGroup):
    waiting_for_question_uz = State()
    waiting_for_options_uz = State()
    waiting_for_correct = State()
    waiting_for_confirmation = State()

class AddProphet(StatesGroup):
    waiting_for_name_uz = State()
    waiting_for_audio = State()
    
# Yangi state (mavjud state lar yoniga)
class RewardState(StatesGroup):
    waiting_for_card = State()
    confirm_card = State()  

# 20 ta savol uchun matn
REWARD_MESSAGE = """
🎁 **MAXSUS MUKOFOT DASTURI** 🎁

💰 Agar siz ketma-ket 20 ta savolga TO'G'RI javob bersangiz:
**200 000 so'm** mukofot pulini yutib olasiz!

✅ Qoidalar:
• 20 ta savolning barchasiga to'g'ri javob berish kerak
• Bitta ham xato qilish mumkin emas
• Xato qilsangiz, qaytadan boshlaysiz

🚀 Omad! Ilmingiz ziyoda bo'lsin!
"""    

# Dictionary to store user data
user_sessions = {}
salawat_count = {}

# Salovat matnlari
SALAWAT_TEXT = "🤲 {}-salovat:\nاللَّهُمَّ صَلِّ عَلَى سَيِّدِنَا مُحَمَّدٍ\n\nAllohumma solli 'ala sayyidina Muhammad"
SALAWAT_TEXTS = [SALAWAT_TEXT.format(i) for i in range(1, 11)]

# Til kodlari
LANGUAGES = {
    'UZ': 'uzbek',
    'RU': 'russian',
    'AR': 'arabic',
    'EN': 'english'
}

# ============================================
# ADMIN PANEL - ASOSIY HANDLERLAR
# ============================================

@dp.message(lambda msg: msg.text == "👥 Foydalanuvchilar" and is_admin(msg.from_user.id))
async def admin_users_list(message: Message, state: FSMContext):
    """Barcha foydalanuvchilar ro'yxati"""
    await state.clear()
    users = db.get_all_users_stats()
    
    if not users:
        await message.answer("📭 Hozircha foydalanuvchilar yo'q")
        return
    
    await message.answer(
        f"👥 **Foydalanuvchilar** ({len(users)} ta)",
        reply_markup=get_users_inline_keyboard(users)
    )

@dp.message(lambda msg: msg.text == "📝 Javoblarni ko'rish" and is_admin(msg.from_user.id))
async def admin_answers_list(message: Message, state: FSMContext):
    """Barcha javoblar ro'yxati"""
    await state.clear()
    answers = db.get_user_answers(limit=100)
    
    if not answers:
        await message.answer("📭 Hozircha javoblar yo'q")
        return
    
    await message.answer(
        f"📝 **Oxirgi javoblar** ({len(answers)} ta)",
        reply_markup=get_answers_inline_keyboard(answers)
    )

@dp.message(lambda msg: msg.text == "💰 Mukofotlar" and is_admin(msg.from_user.id))
async def admin_rewards_menu(message: Message, state: FSMContext):
    """Mukofotlar menyusi"""
    await state.clear()
    
    text = (
        "💰 **MUKOFOTLAR BO'LIMI**\n\n"
        "• ⏳ Kutilayotgan mukofotlar\n"
        "• ✅ To'langan mukofotlar\n"
        "• 📊 Mukofot statistikasi"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Kutilayotganlar", callback_data="admin_rewards_pending")],
        [InlineKeyboardButton(text="✅ To'langanlar", callback_data="admin_rewards_paid")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_rewards_stats")],
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="back_to_admin")]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@dp.message(lambda msg: msg.text == "⏳ Kutilayotgan mukofotlar" and is_admin(msg.from_user.id))
async def admin_pending_rewards(message: Message, state: FSMContext):
    """Kutilayotgan mukofotlar"""
    await state.clear()
    rewards = db.get_pending_rewards()
    
    if not rewards:
        await message.answer("📭 Hozircha kutilayotgan mukofotlar yo'q")
        return
    
    await message.answer(
        f"⏳ **Kutilayotgan mukofotlar** ({len(rewards)} ta)",
        reply_markup=get_pending_rewards_keyboard(rewards)
    )

@dp.message(lambda msg: msg.text == "📊 Statistika" and is_admin(msg.from_user.id))
async def show_stats(message: Message, state: FSMContext):
    """Statistika ko'rish"""
    await state.clear()
    
    try:
        total_users = db.get_total_users()
        today_users = db.get_today_users()
        total_questions = db.get_question_count()
        questions_stats = db.get_questions_stats()
        
        db.cursor.execute('SELECT COUNT(*) FROM prophets')
        total_prophets = db.cursor.fetchone()[0]
        
        stats_text = (
            f"📊 **BOT STATISTIKASI**\n\n"
            f"👥 Jami foydalanuvchilar: {total_users}\n"
            f"📅 Bugun qo'shilganlar: {today_users}\n"
            f"❓ Jami savollar: {total_questions}\n"
            f"   🇺🇿 O'zbek: {questions_stats['UZ']}\n"
            f"   🇷🇺 Rus: {questions_stats['RU']}\n"
            f"   🇸🇦 Arab: {questions_stats['AR']}\n"
            f"   🇬🇧 Ingliz: {questions_stats['EN']}\n"
            f"👤 Payg'ambarlar: {total_prophets}\n"
        )
        
        await message.answer(stats_text, reply_markup=get_admin_keyboard('UZ'))
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer(f"❌ Xatolik: {e}")

@dp.message(lambda msg: msg.text == "➕ Savol qo'shish" and is_admin(msg.from_user.id))
async def add_question_start(message: Message, state: FSMContext):
    """Savol qo'shish boshlash"""
    await state.clear()
    await message.answer(
        "📝 Yangi savol qo'shish\n\n"
        "Savol matnini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddQuestion.waiting_for_question_uz)

@dp.message(lambda msg: msg.text == "👤 Payg'ambar qo'shish" and is_admin(msg.from_user.id))
async def add_prophet_start(message: Message, state: FSMContext):
    """Payg'ambar qo'shish boshlash"""
    await state.clear()
    await message.answer(
        "👤 Yangi payg'ambar qo'shish\n\n"
        "Payg'ambar nomini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddProphet.waiting_for_name_uz)

@dp.message(lambda msg: msg.text == "🔙 Chiqish" and is_admin(msg.from_user.id))
async def admin_exit(message: Message, state: FSMContext):
    """Admin panelidan chiqish"""
    await state.clear()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu_keyboard('UZ')
    )


# ============================================
# ADMIN - FOYDALANUVCHILAR
# ============================================

@dp.callback_query(F.data.startswith('admin_user_'))
async def admin_user_detail(callback: CallbackQuery):
    """Foydalanuvchi haqida batafsil"""
    try:
        data_parts = callback.data.split('_')
        
        # data_parts: ['admin', 'user', 'ID'] yoki ['admin', 'user', 'answers', 'ID']
        if len(data_parts) == 3:
            # Oddiy user detail: admin_user_123456
            user_id = int(data_parts[2])
        elif len(data_parts) == 4 and data_parts[2] == 'answers':
            # User answers: admin_user_answers_123456
            user_id = int(data_parts[3])
            await admin_user_answers(callback, user_id)
            return
        elif len(data_parts) == 4 and data_parts[2] == 'rewards':
            # User rewards: admin_user_rewards_123456
            user_id = int(data_parts[3])
            await admin_user_rewards(callback, user_id)
            return
        else:
            await callback.answer("Noto'g'ri so'rov")
            return
        
        # Foydalanuvchi ma'lumotlari
        db.cursor.execute('''
            SELECT first_name, username, language, registered_at 
            FROM users WHERE user_id = ?
        ''', (user_id,))
        user = db.cursor.fetchone()
        
        # Statistika
        db.cursor.execute('''
            SELECT correct_count, wrong_count, total_questions, best_streak
            FROM user_stats WHERE user_id = ?
        ''', (user_id,))
        stats = db.cursor.fetchone()
        
        if not user:
            await callback.answer("Foydalanuvchi topilmadi")
            return
        
        name, username, lang, reg_date = user
        correct = stats[0] if stats else 0
        wrong = stats[1] if stats else 0
        total = stats[2] if stats else 0
        streak = stats[3] if stats else 0
        
        # Reg_date ni formatlash
        reg_date_str = reg_date[:10] if reg_date else "Noma'lum"
        
        # Oxirgi javoblar
        db.cursor.execute('''
            SELECT q.question_uz, ua.selected_option, ua.is_correct, ua.answered_at
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.user_id = ?
            ORDER BY ua.answered_at DESC LIMIT 5
        ''', (user_id,))
        last_answers = db.cursor.fetchall()
        
        # Matnni qurish
        text_parts = []
        text_parts.append("👤 **Foydalanuvchi ma'lumotlari**\n")
        text_parts.append(f"🆔 ID: `{user_id}`\n")
        text_parts.append(f"📝 Ism: {name}\n")
        text_parts.append(f"🌐 Username: @{username if username else 'yoq'}\n")
        text_parts.append(f"🗣 Til: {lang}\n")
        text_parts.append(f"📅 Ro'yxat: {reg_date_str}\n")
        text_parts.append("\n📊 **Statistika**\n")
        text_parts.append(f"✅ To'g'ri: {correct}\n")
        text_parts.append(f"❌ Noto'g'ri: {wrong}\n")
        text_parts.append(f"📝 Jami: {total}\n")
        text_parts.append(f"🏆 Eng yaxshi: {streak}\n")
        
        if last_answers:
            text_parts.append("\n📋 **Oxirgi 5 ta javob:**\n")
            for i, ans in enumerate(last_answers, 1):
                q_text, selected, is_correct, ans_time = ans
                status = "✅" if is_correct else "❌"
                ans_time_str = ans_time[:16] if ans_time else ""
                text_parts.append(f"{i}. {status} {q_text[:30]}... ({ans_time_str})\n")
        
        text = "".join(text_parts)
        
        # Inline keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Barcha javoblar", callback_data=f"admin_user_answers_{user_id}")],
            [InlineKeyboardButton(text="💰 Mukofotlar tarixi", callback_data=f"admin_user_rewards_{user_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_users_back")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        print(f"Xatolik: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("Xatolik yuz berdi")


# ============================================
# ADMIN - FOYDALANUVCHI JAVOBLARI (TO'G'RI)
# ============================================

async def admin_user_answers(callback: CallbackQuery, user_id: int):
    """Foydalanuvchining barcha javoblarini ko'rsatish (2 parametr)"""
    try:
        answers = db.get_user_answers(user_id, limit=50)
        
        if not answers:
            await callback.message.edit_text("📭 Javoblar yo'q")
            return
        
        text = f"📝 **Foydalanuvchi javoblari** (ID: {user_id})\n\n"
        for i, ans in enumerate(answers[:10], 1):
            # answers strukturasi: (id, user_id, question_id, selected_option, is_correct, answered_at, first_name, username, question_uz)
            q_id = ans[2]
            is_correct = ans[4]
            ans_time = ans[5]
            question = ans[8]
            
            status = "✅" if is_correct else "❌"
            ans_time_str = ans_time[:16] if ans_time else ""
            text += f"{i}. {status} Savol {q_id}: {question[:40]}... ({ans_time_str})\n"
        
        if len(answers) > 10:
            text += f"\n... va yana {len(answers)-10} ta javob"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin_user_{user_id}")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        print(f"Xatolik: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(f"❌ Xatolik: {e}")
        await callback.answer()


# ============================================
# ADMIN - FOYDALANUVCHI MUKOFOTLARI (TO'G'RI)
# ============================================

async def admin_user_rewards(callback: CallbackQuery, user_id: int):
    """Foydalanuvchining mukofotlarini ko'rsatish (2 parametr)"""
    try:
        # rewards jadvalida qanday ustunlar borligini tekshirish
        db.cursor.execute("PRAGMA table_info(rewards)")
        columns = [col[1] for col in db.cursor.fetchall()]
        print(f"📊 rewards jadvali ustunlari: {columns}")
        
        # 'created_at' ustuni yo'q, shuning uchun 'id' yoki boshqa ustunni ishlatamiz
        query = '''
            SELECT id, amount, status, paid_at
            FROM rewards WHERE user_id = ? ORDER BY id DESC
        '''
        
        db.cursor.execute(query, (user_id,))
        rewards = db.cursor.fetchall()
        
        if not rewards:
            await callback.message.edit_text("💰 Mukofotlar yo'q")
            return
        
        text = f"💰 **Foydalanuvchi mukofotlari** (ID: {user_id})\n\n"
        for r in rewards:
            if len(r) >= 3:
                r_id = r[0]
                amount = r[1]
                status = r[2]
                paid_at = r[3] if len(r) > 3 else None
                
                status_icon = "⏳" if status == 'pending' else "✅" if status == 'paid' else "❌"
                paid_str = f" - To'langan: {paid_at[:10]}" if paid_at and status == 'paid' else ""
                text += f"{status_icon} {amount} so'm{paid_str}\n"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin_user_{user_id}")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        print(f"Xatolik: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(f"❌ Xatolik: {e}")
        await callback.answer()


@dp.callback_query(F.data == "admin_users_back")
async def admin_users_back(callback: CallbackQuery):
    """Foydalanuvchilar ro'yxatiga qaytish"""
    users = db.get_all_users_stats()
    await callback.message.edit_text(
        f"👥 **Foydalanuvchilar** ({len(users)} ta)",
        reply_markup=get_users_inline_keyboard(users)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith('admin_users_page_'))
async def admin_users_page(callback: CallbackQuery):
    """Foydalanuvchilar ro'yxati sahifalash"""
    page = int(callback.data.split('_')[3])
    users = db.get_all_users_stats()
    await callback.message.edit_reply_markup(
        reply_markup=get_users_inline_keyboard(users, page)
    )
    await callback.answer()

# Admin check
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def translate_text_sync(text: str, target_lang: str) -> str:
    """Matnni kerakli tilga tarjima qilish (sinxron)"""
    try:
        if not text or text.strip() == "":
            return text
        
        if target_lang == 'UZ':
            return text
            
        lang_map = {
            'RU': 'ru',
            'AR': 'ar', 
            'EN': 'en'
        }
        dest = lang_map.get(target_lang)
        
        if not dest:
            return text
        
        print(f"🔄 Tarjima: '{text[:30]}...' -> {target_lang} ({dest})")
        
        # Sinxron tarjima
        translator = Translator()
        result = translator.translate(text, dest=dest)
        
        if hasattr(result, 'text'):
            translated = result.text
            print(f"✅ Natija: '{translated[:30]}...'")
            return translated
        else:
            print(f"⚠️ Tarjima natijasi text attribute ga ega emas: {type(result)}")
            return str(result)
            
    except Exception as e:
        print(f"❌ Tarjima xatoligi: {e}")
        import traceback
        traceback.print_exc()
        return text

# Tarjima funksiyasi - TO'LIQ ISHLAYDIAGAN VERSIYA
async def translate_text(text: str, target_lang: str) -> str:
    """Matnni kerakli tilga tarjima qilish"""
    try:
        # Agar matn bo'sh bo'lsa
        if not text or text.strip() == "":
            return text
        
        # O'zbek tili uchun tarjima qilmaymiz (asl matn)
        if target_lang == 'UZ':
            return text
            
        # Google Translate kodlariga moslashtirish
        lang_map = {
            'RU': 'ru',
            'AR': 'ar',
            'EN': 'en'
        }
        dest = lang_map.get(target_lang)
        
        if not dest:
            return text
        
        print(f"🔄 Tarjima qilinmoqda: '{text[:30]}...' ({target_lang})")
        
        # Tarjima qilish
        result = translator.translate(text, dest=dest)
        
        # Tarjima natijasini olish
        if hasattr(result, 'text'):
            translated = result.text
        else:
            translated = str(result)
        
        print(f"✅ Tarjima natijasi: '{translated[:30]}...'")
        return translated
            
    except Exception as e:
        print(f"❌ Tarjima xatoligi: {e}")
        return text

# Start handler
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    first_name = message.from_user.first_name or "No name"
    
    # Admin check
    if is_admin(user_id):
        await message.answer(
            "👋 Assalomu Alaykum Admin!\n\n"
            "Admin panel:",
            reply_markup=get_admin_keyboard('UZ')
        )
        return
    
    # Add user to database
    is_new = db.add_user(user_id, username, first_name)
    
    # Notify admin about new user
    if is_new:
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🆕 Yangi foydalanuvchi!\n"
                    f"ID: {user_id}\n"
                    f"Ism: {first_name}\n"
                    f"Username: @{username}"
                )
            except:
                pass
    
    # Foydalanuvchi ma'lumotlarini yaratish
    if user_id not in user_sessions:
        user_sessions[user_id] = {'name': '', 'lang': 'UZ'}
    
    # Agar foydalanuvchi avval ro'yxatdan o'tgan bo'lsa
    if user_sessions[user_id].get('name'):
        lang = user_sessions[user_id].get('lang', 'UZ')
        name = user_sessions[user_id]['name']
        
        welcome_text = await translate_text(f"Assalomu Aleykum {name}!\n\nXush kelibsiz!", lang)
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        # Yangi foydalanuvchi
        salawat_count[user_id] = 1
        
        welcome_text = (
            "🤲 Assalomu Aleykum!\n\n"
            "Rasululloh ﷺ ga salovat aytish bilan boshlaymiz.\n"
            "Har bir salovatdan keyin baraka olib, keyingi bosqichga o'tasiz."
        )
        
        await message.answer(welcome_text)
        await asyncio.sleep(1)
        await message.answer(
            SALAWAT_TEXTS[0],
            reply_markup=get_salawat_keyboard(1, 'UZ')
        )

# Salovat tugmasi bosilganda
@dp.message(lambda msg: msg.text and "salovat ayting" in msg.text.lower())
async def salavat_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    current_count = salawat_count.get(user_id, 1)
    
    await message.answer("✅ Qabul bo'lsin!")
    await asyncio.sleep(1)
    
    next_count = current_count + 1
    
    if next_count <= 10:
        salawat_count[user_id] = next_count
        await message.answer(
            SALAWAT_TEXTS[next_count - 1],
            reply_markup=get_salawat_keyboard(next_count, 'UZ')
        )
    else:
        salawat_count[user_id] = 0
        await message.answer(
            "✨ Barakalla! 10 ta salovat aytdingiz.\n\n"
            "Endi o'zingizni tanishtirish uchun tilni tanlang:",
            reply_markup=get_language_reply_keyboard()
        )

# Til tanlash handler
@dp.message(lambda msg: msg.text in ["🇺🇿 O'zbek", "🇷🇺 Русский", "🇸🇦 العربية", "🇬🇧 English"])
async def handle_language_selection(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    text = message.text
    
    lang_map = {
        "🇺🇿 O'zbek": 'UZ',
        "🇷🇺 Русский": 'RU',
        "🇸🇦 العربية": 'AR',
        "🇬🇧 English": 'EN'
    }
    lang = lang_map.get(text, 'UZ')
    
    print(f"🌐 Til tanlandi: {lang} (user_id: {user_id})")
    
    # BAZAGA SAQLASH
    db.set_user_language(user_id, lang)
    
    # SESSION NI YANGILASH
    if user_id not in user_sessions:
        user_sessions[user_id] = {'name': '', 'lang': lang, 'seen_questions': []}
    else:
        user_sessions[user_id]['lang'] = lang
    
    # Ism bor-yo'qligini tekshirish
    db.cursor.execute('SELECT first_name FROM users WHERE user_id = ?', (user_id,))
    result = db.cursor.fetchone()
    
    if result and result[0]:
        # Ism bor - menyuga o'tish
        name = result[0]
        welcome_text = await translate_text(f"Assalomu Aleykum {name}!\n\nTil muvaffaqiyatli o'zgartirildi.", lang)
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        # Ism yo'q - ism so'rash
        name_prompt = await translate_text("Ismingizni kiriting:", lang)
        await message.answer(name_prompt)
        await state.set_state(RegisterState.waiting_for_name)

# Ism kiritish handler
@dp.message(RegisterState.waiting_for_name)
async def handle_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        await state.clear()
        return
    
    name = message.text.strip()
    
    if not name:
        await message.answer("Iltimos ismingizni kiriting:")
        return
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    user_sessions[user_id]['name'] = name
    db.update_user_name(user_id, name)
    
    await state.clear()
    
    welcome_text = await translate_text(
        f"Assalomu Aleykum {name}!\n\nIslomiy Savol Javoblar botiga xush kelibsiz!", 
        lang
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(lang)
    )

# ADMIN FUNKSIYALARI - SAVOL QO'SHISH
@dp.message(lambda msg: msg.text == "➕ Savol qo'shish" and is_admin(msg.from_user.id))
async def add_question_start(message: Message, state: FSMContext):
    await message.answer(
        "📝 Yangi savol qo'shish\n\n"
        "Savol matnini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddQuestion.waiting_for_question_uz)

@dp.message(AddQuestion.waiting_for_question_uz)
async def process_question_uz(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    await state.update_data(question_uz=message.text)
    
    await message.answer(
        "✅ Savol qabul qilindi!\n\n"
        "Endi 3 ta JAVOB variantini kiriting (har bir qatorda bittadan):\n"
        "Misol:\n"
        "Variant 1\n"
        "Variant 2\n"
        "Variant 3"
    )
    await state.set_state(AddQuestion.waiting_for_options_uz)

@dp.message(AddQuestion.waiting_for_options_uz)
async def process_options_uz(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    options = message.text.strip().split('\n')
    
    if len(options) != 3:
        await message.answer("❌ Iltimos, 3 ta variantni har bir qatorda bittadan kiriting!")
        return
    
    option1 = options[0].strip()
    option2 = options[1].strip()
    option3 = options[2].strip()
    
    if not option1 or not option2 or not option3:
        await message.answer("❌ Variantlar bo'sh bo'lmasligi kerak!")
        return
    
    await state.update_data(
        option1_uz=option1,
        option2_uz=option2,
        option3_uz=option3
    )
    
    await message.answer(
        "✅ Variantlar qabul qilindi!\n\n"
        "To'g'ri javob raqamini kiriting (1, 2 yoki 3):"
    )
    await state.set_state(AddQuestion.waiting_for_correct)

@dp.message(AddQuestion.waiting_for_correct)
async def process_correct(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    if message.text not in ['1', '2', '3']:
        await message.answer("❌ Iltimos, 1, 2 yoki 3 raqamlaridan birini kiriting!")
        return
    
    await state.update_data(correct=int(message.text))
    data = await state.get_data()
    
    preview = (
        f"📋 Savol tayyor!\n\n"
        f"❓ Savol: {data['question_uz']}\n\n"
        f"1️⃣ {data['option1_uz']}\n"
        f"2️⃣ {data['option2_uz']}\n"
        f"3️⃣ {data['option3_uz']}\n\n"
        f"✅ To'g'ri javob: {data['correct']}\n\n"
        f"Saqlash uchun \"✅ Saqlash\" tugmasini bosing."
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Saqlash", callback_data="admin_confirm_save")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel_save")]
    ])
    
    await message.answer(preview, reply_markup=keyboard)
    await state.set_state(AddQuestion.waiting_for_confirmation)

@dp.callback_query(F.data == "admin_confirm_save")
async def confirm_save(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz!")
        return
    
    await callback.message.edit_text("⏳ Tarjima qilinmoqda...")
    
    data = await state.get_data()
    
    try:
        print("=" * 50)
        print("🔤 TARJIMA JARAYONI BOSHLANDI")
        print("=" * 50)
        
        # Asl matnlar
        question_uz = data['question_uz']
        option1_uz = data['option1_uz']
        option2_uz = data['option2_uz']
        option3_uz = data['option3_uz']
        
        print(f"📝 Asl matn (O'zbek): {question_uz}")
        
        loop = asyncio.get_event_loop()
        
        # Rus tiliga tarjima
        question_ru = await loop.run_in_executor(None, translate_text_sync, question_uz, 'RU')
        option1_ru = await loop.run_in_executor(None, translate_text_sync, option1_uz, 'RU')
        option2_ru = await loop.run_in_executor(None, translate_text_sync, option2_uz, 'RU')
        option3_ru = await loop.run_in_executor(None, translate_text_sync, option3_uz, 'RU')
        
        # Arab tiliga tarjima - BU TO'G'RI ISHLASHI KERAK
        question_ar = await loop.run_in_executor(None, translate_text_sync, question_uz, 'AR')
        option1_ar = await loop.run_in_executor(None, translate_text_sync, option1_uz, 'AR')
        option2_ar = await loop.run_in_executor(None, translate_text_sync, option2_uz, 'AR')
        option3_ar = await loop.run_in_executor(None, translate_text_sync, option3_uz, 'AR')
        
        # Ingliz tiliga tarjima
        question_en = await loop.run_in_executor(None, translate_text_sync, question_uz, 'EN')
        option1_en = await loop.run_in_executor(None, translate_text_sync, option1_uz, 'EN')
        option2_en = await loop.run_in_executor(None, translate_text_sync, option2_uz, 'EN')
        option3_en = await loop.run_in_executor(None, translate_text_sync, option3_uz, 'EN')
        
        # TARJIMA NATIJALARINI TEKSHIRISH
        print(f"🇸🇦 Arabcha tarjima: {question_ar}")
        print(f"🇷🇺 Ruscha tarjima: {question_ru}")
        print(f"🇬🇧 Inglizcha tarjima: {question_en}")
        
        # Database ga saqlash
        question_data = (
            question_uz, question_ru, question_ar, question_en,
            option1_uz, option1_ru, option1_ar, option1_en,
            option2_uz, option2_ru, option2_ar, option2_en,
            option3_uz, option3_ru, option3_ar, option3_en,
            data['correct'], datetime.now(), callback.from_user.id
        )
        
        print("✅ Ma'lumotlar bazaga saqlanmoqda...")
        print(f"📦 O'zbek: {question_uz}")
        print(f"📦 Arab: {question_ar}")
        print(f"📦 Rus: {question_ru}")
        print(f"📦 Ingliz: {question_en}")
        
        question_id = db.add_question(question_data)
        
        if question_id:
            await callback.message.edit_text(
                f"✅ Savol muvaffaqiyatli qo'shildi! (ID: {question_id})\n\n"
                f"🇺🇿 O'zbek: {question_uz}\n"
                f"🇸🇦 Arab: {question_ar}\n"
                f"🇷🇺 Rus: {question_ru}\n"
                f"🇬🇧 Ingliz: {question_en}"
            )
            
            await callback.message.answer(
                "Admin panel:",
                reply_markup=get_admin_keyboard('UZ')
            )
        else:
            await callback.message.edit_text("❌ Saqlashda xatolik yuz berdi!")
        
    except Exception as e:
        logger.error(f"Error saving question: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(f"❌ Xatolik: {str(e)}")
    
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "admin_cancel_save")
async def cancel_save(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz!")
        return
    
    await callback.message.edit_text("❌ Bekor qilindi.")
    await state.clear()
    await callback.message.answer(
        "Admin panel:",
        reply_markup=get_admin_keyboard('UZ')
    )
    await callback.answer()

async def show_stats(message: Message):
    try:
        total_users = db.get_total_users()
        today_users = db.get_today_users()
        total_questions = db.get_question_count()
        questions_stats = db.get_questions_stats()
        inactive_count = db.get_inactive_questions_count()
        
        db.cursor.execute('SELECT COUNT(*) FROM prophets')
        total_prophets = db.cursor.fetchone()[0]
        
        stats_text = (
            f"📊 **BOT STATISTIKASI**\n\n"
            f"👥 Jami foydalanuvchilar: {total_users}\n"
            f"📅 Bugun qo'shilganlar: {today_users}\n"
            f"❓ Jami savollar: {total_questions}\n"
            f"   ✅ Faol: {total_questions - inactive_count}\n"
            f"   ❌ Faol emas: {inactive_count}\n"
            f"   🇺🇿 O'zbek: {questions_stats['UZ']}\n"
            f"   🇷🇺 Rus: {questions_stats['RU']}\n"
            f"   🇸🇦 Arab: {questions_stats['AR']}\n"
            f"   🇬🇧 Ingliz: {questions_stats['EN']}\n"
            f"👤 Payg'ambarlar: {total_prophets}\n"
        )
        
        # Batafsil statistika tugmasi
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Batafsil savol statistikasi", callback_data="admin_questions_stats")]
        ])
        
        await message.answer(stats_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer(f"❌ Xatolik: {e}")


@dp.callback_query(F.data == "admin_questions_stats")
async def goto_questions_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    
    await callback.message.delete()
    await show_questions_stats(callback.message)
    await callback.answer()

# ADMIN PAYG'AMBAR QO'SHISH
@dp.message(lambda msg: msg.text == "👤 Payg'ambar qo'shish" and is_admin(msg.from_user.id))
async def add_prophet_start(message: Message, state: FSMContext):
    await message.answer(
        "👤 Yangi payg'ambar qo'shish\n\n"
        "Payg'ambar nomini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddProphet.waiting_for_name_uz)

@dp.message(AddProphet.waiting_for_name_uz)
async def process_prophet_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    name = message.text.strip()
    if not name:
        await message.answer("❌ Nom bo'sh bo'lmasligi kerak!")
        return
    
    await state.update_data(name_uz=name)
    
    await message.answer(
        "✅ Nom qabul qilindi!\n\n"
        "Endi payg'ambar haqidagi AUDIO faylni yuboring:"
    )
    await state.set_state(AddProphet.waiting_for_audio)

@dp.message(AddProphet.waiting_for_audio)
async def process_prophet_audio(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    if not message.audio:
        await message.answer("❌ Iltimos, audio fayl yuboring!")
        return
    
    data = await state.get_data()
    
    try:
        # Barcha tillarga tarjima qilish
        name_ru = await translate_text(data['name_uz'], 'RU')
        name_ar = await translate_text(data['name_uz'], 'AR')
        name_en = await translate_text(data['name_uz'], 'EN')
        
        # Database ga saqlash
        prophet_id = db.add_prophet(data['name_uz'], name_ru, name_ar, name_en, message.audio.file_id)
        
        success_text = (
            f"✅ Payg'ambar muvaffaqiyatli qo'shildi! (ID: {prophet_id})\n\n"
            f"📝 O'zbekcha: {data['name_uz']}\n"
            f"🇷🇺 Ruscha: {name_ru}\n"
            f"🇸🇦 Arabcha: {name_ar}\n"
            f"🇬🇧 Inglizcha: {name_en}"
        )
        
        await message.answer(success_text)
        await message.answer(
            "Admin panel:",
            reply_markup=get_admin_keyboard('UZ')
        )
        
    except Exception as e:
        logger.error(f"Error adding prophet: {e}")
        await message.answer(f"❌ Xatolik: {e}")
    
    await state.clear()

# ADMIN CHIQISH
@dp.message(lambda msg: msg.text == "🔙 Chiqish" and is_admin(msg.from_user.id))
async def admin_exit(message: Message):
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu_keyboard('UZ')
    )

# Tilni o'zgartirish
@dp.message(lambda msg: msg.text in ["🌐 Tilni o'zgartirish", "🌐 Сменить язык", "🌐 تغيير اللغة", "🌐 Change language"])
async def change_lang_handler(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    current_lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
    
    prompts = {
        'UZ': "Tilni tanlang:",
        'RU': "Выберите язык:",
        'AR': "اختر اللغة:",
        'EN': "Choose language:"
    }
    
    await message.answer(
        prompts.get(current_lang, prompts['UZ']),
        reply_markup=get_language_reply_keyboard()
    )

@dp.message(lambda msg: msg.text in ["❓ Savollar", "❓ Вопросы", "❓ أسئلة", "❓ Questions"])
async def questions_handler(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    # Kutish vaqtini tekshirish
    is_waiting, remaining = db.check_user_wait(user_id)
    if is_waiting:
        lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
        wait_messages = {
            'UZ': f"⏳ **{remaining} daqiqa kutishingiz kerak!**\n\nSiz noto'g'ri javob berganingiz uchun keyingi savol {remaining} daqiqadan so'ng yuboriladi.\nIltimos, sabr qiling! 🤲",
            'RU': f"⏳ **Нужно подождать {remaining} минут!**\n\nИз-за неверного ответа следующий вопрос будет доступен через {remaining} минут.\nПожалуйста, наберитесь терпения! 🤲",
            'AR': f"⏳ **عليك الانتظار {remaining} دقيقة!**\n\nبسبب إجابتك الخاطئة، سيكون السؤال التالي متاحًا بعد {remaining} دقيقة.\nيرجى التحلي بالصبر! 🤲",
            'EN': f"⏳ **{remaining} minutes wait!**\n\nDue to your wrong answer, the next question will be available in {remaining} minutes.\nPlease be patient! 🤲"
        }
        await message.answer(wait_messages.get(lang, wait_messages['UZ']))
        return
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    # Foydalanuvchi ko'rmagan va noto'g'ri javob bermagan savollarni olish
    excluded = db.get_excluded_questions(user_id)
    
    # Savol olish
    question = db.get_random_question_excluding(lang, excluded)
    
    if not question:
        no_questions = {
            'UZ': "Hozircha savollar mavjud emas.",
            'RU': "Пока нет вопросов.",
            'AR': "لا توجد أسئلة حتى الآن.",
            'EN': "No questions available yet."
        }
        await message.answer(no_questions.get(lang, no_questions['UZ']))
        return
    
    q_id, q_text, opt1, opt2, opt3, correct = question
    
    # Joriy savol ma'lumotlarini saqlash
    user_sessions[user_id]['current_question'] = {
        'id': q_id,
        'correct': correct,
        'correct_text': [opt1, opt2, opt3][correct-1],
        'options': [opt1, opt2, opt3]
    }
    
    # Savol prefiksi
    question_prefix = {'UZ': "❓ **Savol**", 'RU': "❓ **Вопрос**", 'AR': "❓ **سؤال**", 'EN': "❓ **Question**"}
    
    await message.answer(f"{question_prefix.get(lang, '❓ Savol')}:\n\n{q_text}")
    await message.answer(
        "👇 Javob variantlari:",
        reply_markup=get_circle_options_keyboard((opt1, opt2, opt3), q_id, lang)
    )
    
@dp.callback_query(F.data.startswith('circle_answer_'))
async def handle_circle_answer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # ===== DEBUG UCHUN =====
    print(f"\n🔴🔴🔴 CALLBACK KELDI: {callback.data}")
    print(f"🔴 Foydalanuvchi ID: {user_id}")
    # ======================
    
    if is_admin(user_id):
        await callback.answer()
        return
    
    # Kutish vaqtini tekshirish
    is_waiting, remaining = db.check_user_wait(user_id)
    if is_waiting:
        await callback.answer(f"⏳ {remaining} daqiqa kutishingiz kerak", show_alert=True)
        return
    
    # Javob ma'lumotlarini olish
    try:
        parts = callback.data.split('_')
        if len(parts) < 4:
            await callback.answer("Xatolik: noto'g'ri format", show_alert=True)
            return
            
        question_id = int(parts[2])
        selected = int(parts[3])
        print(f"🔴 Savol ID: {question_id}, Tanlangan: {selected}")
    except Exception as e:
        print(f"🔴 Xatolik: {e}")
        await callback.answer("Xatolik yuz berdi!", show_alert=True)
        return
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        print(f"🔴 User sessions topilmadi: {user_id}")
        await callback.answer("Sessiya topilmadi! Iltimos, qaytadan boshlang.", show_alert=True)
        return
    
    if 'current_question' not in user_sessions[user_id]:
        print(f"🔴 current_question topilmadi: {user_id}")
        await callback.answer("Joriy savol topilmadi!", show_alert=True)
        return
    
    current_q = user_sessions[user_id]['current_question']
    correct = current_q.get('correct', 0)
    options = current_q.get('options', [])
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    print(f"🔴 To'g'ri javob: {correct}, Tanlangan: {selected}")
    
    is_correct = (selected == correct)
    
    # ===== TUZATILGAN QISM (backslash muammosi hal qilindi) =====
    if is_correct:
        result_text = "✅ To'g'ri"
    else:
        result_text = "❌ Noto'g'ri"
    print(f"🔴 Natija: {result_text}")
    # ===========================================================
    
    # Javobni bazaga saqlash
    db.save_answer(user_id, question_id, selected, is_correct)
    db.update_user_stats(user_id, is_correct)
    
    # 20 ta savol sessiyasini tekshirish
    active_session = db.get_active_session(user_id)
    session_id = None
    
    if active_session:
        session_id = active_session[0]
    
    if is_correct:
        # ===== TO'G'RI JAVOB =====
        print(f"🔴 TO'G'RI JAVOB!")
        
        if not active_session:
            session_id = db.start_20_questions_session(user_id)
            if session_id:
                db.save_question_answer(user_id, session_id, question_id, selected, True)
        else:
            db.save_question_answer(user_id, session_id, question_id, selected, True)
        
        # Joriy xabarni yangilash (variantlar bilan)
        try:
            await callback.message.edit_text(
                f"✅ **To'g'ri javob!**\n\n👇 Natijalar:",
                reply_markup=get_updated_options_keyboard(options, question_id, selected, correct, lang)
            )
            print(f"🔴 Xabar muvaffaqiyatli yangilandi")
        except Exception as e:
            print(f"🔴 Xabarni yangilashda xatolik: {e}")
        
        # KEYINGI SAVOLNI AVTOMATIK YUBORISH (1.5 soniya kutib)
        await asyncio.sleep(1.5)
        await send_next_question(callback.message, user_id, lang)
        
    else:
        # ===== NOTO'G'RI JAVOB =====
        print(f"🔴 NOTO'G'RI JAVOB!")
        
        if active_session:
            db.save_question_answer(user_id, session_id, question_id, selected, False)
            db.complete_session(session_id, user_id, success=False)
        
        # Noto'g'ri javob berilgan savolni saqlash (qayta chiqmasligi uchun)
        db.save_wrong_question(user_id, question_id)
        
        # 15 daqiqa kutish vaqti
        db.set_user_wait(user_id, minutes=15)
        
        # Joriy xabarni yangilash (variantlar bilan)
        try:
            await callback.message.edit_text(
                f"❌ **Noto'g'ri javob!**\n\n✅ **To'g'ri javob:** {options[correct-1]}\n\n👇 Natijalar:",
                reply_markup=get_updated_options_keyboard(options, question_id, selected, correct, lang)
            )
            print(f"🔴 Xabar muvaffaqiyatli yangilandi")
        except Exception as e:
            print(f"🔴 Xabarni yangilashda xatolik: {e}")
        
        # Kutish vaqti xabari
        wait_msg = {
            'UZ': "⏳ **15 daqiqa kutishingiz kerak!**\n\nSiz noto'g'ri javob berganingiz uchun keyingi savol 15 daqiqadan so'ng yuboriladi.\nIltimos, sabr qiling! 🤲",
            'RU': "⏳ **Нужно подождать 15 минут!**\n\nИз-за неверного ответа следующий вопрос будет доступен через 15 минут.\nПожалуйста, наберитесь терпения! 🤲",
            'AR': "⏳ **عليك الانتظار 15 دقيقة!**\n\nبسبب إجابتك الخاطئة، سيكون السؤال التالي متاحًا بعد 15 دقيقة.\nيرجى التحلي بالصبر! 🤲",
            'EN': "⏳ **15 minutes wait!**\n\nDue to your wrong answer, the next question will be available in 15 minutes.\nPlease be patient! 🤲"
        }
        
        await callback.message.answer(wait_msg.get(lang, wait_msg['UZ']))
        
        # 15 daqiqadan so'ng avtomatik yangi savol yuborish
        asyncio.create_task(delayed_next_question(callback.message, user_id, lang, 15 * 60))
    
    await callback.answer()
    print(f"🔴 Handler tugadi")


async def send_next_question(message: Message, user_id: int, lang: str):
    """Yangi savol yuborish"""
    print(f"🔵 Yangi savol yuborilmoqda: user={user_id}, lang={lang}")
    
    # Foydalanuvchi ko'rmagan va noto'g'ri javob bermagan savollarni olish
    excluded = db.get_excluded_questions(user_id)
    print(f"🔵 Excluded savollar: {excluded}")
    
    # Yangi savol olish
    new_question = db.get_random_question_excluding(lang, excluded)
    
    if not new_question:
        print(f"🔵 Savollar tugagan!")
        all_done_messages = {
            'UZ': "🎉 **Tabriklaymiz!**\n\nSiz barcha savollarni yakunladingiz!",
            'RU': "🎉 **Поздравляем!**\n\nВы завершили все вопросы!",
            'AR': "🎉 **تهانينا!**\n\nلقد أكملت جميع الأسئلة!",
            'EN': "🎉 **Congratulations!**\n\nYou have completed all questions!"
        }
        await message.answer(all_done_messages.get(lang, all_done_messages['UZ']),
                            reply_markup=get_main_menu_keyboard(lang))
        return
    
    q_id, q_text, opt1, opt2, opt3, correct = new_question
    print(f"🔵 Yangi savol ID: {q_id}")
    
    # Joriy savol ma'lumotlarini saqlash
    user_sessions[user_id]['current_question'] = {
        'id': q_id,
        'correct': correct,
        'correct_text': [opt1, opt2, opt3][correct-1],
        'options': [opt1, opt2, opt3]
    }
    
    # Savol prefiksi
    question_prefix = {'UZ': "❓ **Savol**", 'RU': "❓ **Вопрос**", 'AR': "❓ **سؤال**", 'EN': "❓ **Question**"}
    
    await message.answer(f"{question_prefix.get(lang, '❓ Savol')}:\n\n{q_text}")
    await message.answer(
        "👇 Javob variantlari:",
        reply_markup=get_circle_options_keyboard((opt1, opt2, opt3), q_id, lang)
    )
    print(f"🔵 Yangi savol yuborildi")


async def delayed_next_question(message: Message, user_id: int, lang: str, delay_seconds: int):
    """Kutish vaqtidan keyin yangi savol yuborish"""
    print(f"🟡 {delay_seconds} sekund kutish boshlandi...")
    await asyncio.sleep(delay_seconds)
    print(f"🟡 Kutish tugadi, yangi savol tekshirilmoqda...")
    
    # Kutish vaqti tugaganligini tekshirish
    is_waiting, _ = db.check_user_wait(user_id)
    if not is_waiting:
        print(f"🟡 Yangi savol yuborilmoqda...")
        await send_next_question(message, user_id, lang)
    else:
        print(f"🟡 Hali kutish vaqti tugamagan")


# Keyingi savol handler
@dp.callback_query(F.data.startswith('next_question_'))
async def next_question_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    parts = callback.data.split('_')
    question_id = int(parts[2])
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        await callback.answer("Xatolik yuz berdi!")
        return
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    seen_questions = user_sessions[user_id].get('questions_seen', [])
    
    # Yangi savol olish
    new_question = db.get_random_question_excluding(lang, seen_questions)
    
    if not new_question:
        all_done_messages = {
            'UZ': "🎉 Tabriklaymiz! Siz barcha savollarni yakunladingiz!",
            'RU': "🎉 Поздравляем! Вы завершили все вопросы!",
            'AR': "🎉 مبروك! لقد أكملت جميع الأسئلة!",
            'EN': "🎉 Congratulations! You have completed all questions!"
        }
        await callback.message.answer(
            all_done_messages.get(lang, all_done_messages['UZ']),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await callback.answer()
        return
    
    q_id, q_text, opt1, opt2, opt3, correct = new_question
    
    # Yangi savolni ko'rilganlar ro'yxatiga qo'shish
    if q_id not in seen_questions:
        user_sessions[user_id]['questions_seen'].append(q_id)
    
    # Joriy savol ma'lumotlarini saqlash
    correct_answer_text = [opt1, opt2, opt3][correct-1]
    
    user_sessions[user_id]['current_question'] = {
        'id': q_id,
        'correct': correct,
        'correct_text': correct_answer_text,
        'options': [opt1, opt2, opt3],
        'source': 'questions'
    }
    
    # Savol prefiksi
    question_prefix = {
        'UZ': "❓ Savol",
        'RU': "❓ Вопрос",
        'AR': "❓ سؤال",
        'EN': "❓ Question"
    }
    
    # Yangi xabar yuborish
    await callback.message.answer(
        f"{question_prefix.get(lang, '❓ Savol')}:\n\n{q_text}"
    )
    
    await callback.message.answer(
        "👇 Javob variantlari:",
        reply_markup=get_circle_options_keyboard((opt1, opt2, opt3), q_id, lang)
    )
    
    await callback.answer()    
    
@dp.message(lambda msg: msg.text in ["❓ Savollar statistikasi", "❓ Статистика вопросов"] and is_admin(msg.from_user.id))
async def show_questions_stats(message: Message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Statistikani olish
    stats = db.get_questions_detailed_stats()
    admin_questions = db.get_questions_by_admin(user_id)
    inactive_count = db.get_inactive_questions_count()
    
    # Tilni aniqlash (admin uchun)
    lang = 'UZ'  # yoki db dan olish mumkin
    
    # Statistik matn
    if lang == 'UZ':
        text = (
            "📊 **SAVOLLAR STATISTIKASI** 📊\n\n"
            f"📌 **Jami savollar:** {stats['total']} ta\n"
            f"✅ **Faol savollar:** {stats['active']} ta\n"
            f"❌ **Faol emas:** {inactive_count} ta\n"
            f"👤 **Siz qo'shgan:** {admin_questions} ta\n\n"
            "🌐 **Tillarga bo'lingan:**\n"
            f"   🇺🇿 O'zbek: {stats['lang_UZ']} ta\n"
            f"   🇷🇺 Rus: {stats['lang_RU']} ta\n"
            f"   🇸🇦 Arab: {stats['lang_AR']} ta\n"
            f"   🇬🇧 Ingliz: {stats['lang_EN']} ta\n"
        )
    else:
        text = (
            "📊 **СТАТИСТИКА ВОПРОСОВ** 📊\n\n"
            f"📌 **Всего вопросов:** {stats['total']}\n"
            f"✅ **Активных:** {stats['active']}\n"
            f"❌ **Неактивных:** {inactive_count}\n"
            f"👤 **Добавлено вами:** {admin_questions}\n\n"
            "🌐 **По языкам:**\n"
            f"   🇺🇿 Узбекский: {stats['lang_UZ']}\n"
            f"   🇷🇺 Русский: {stats['lang_RU']}\n"
            f"   🇸🇦 Арабский: {stats['lang_AR']}\n"
            f"   🇬🇧 Английский: {stats['lang_EN']}\n"
        )
    
    # Oxirgi savollar
    if stats['recent']:
        if lang == 'UZ':
            text += "\n📋 **Oxirgi qo'shilgan savollar:**\n"
        else:
            text += "\n📋 **Последние добавленные вопросы:**\n"
        
        for i, q in enumerate(stats['recent'][:5], 1):
            q_id, q_text, created_at, is_active = q
            status = "✅" if is_active else "❌"
            date_str = created_at[:16] if created_at else "Noma'lum"
            text += f"{i}. {status} ID {q_id}: {q_text[:40]}... ({date_str})\n"
    
    # Oylik statistika
    if stats['monthly']:
        if lang == 'UZ':
            text += "\n📅 **Oylik statistika:**\n"
        else:
            text += "\n📅 **Месячная статистика:**\n"
        
        for month, count in stats['monthly']:
            text += f"   {month}: {count} ta\n"
    
    # Inline keyboard (faollashtirish/o'chirish uchun)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_refresh_stats")],
        [InlineKeyboardButton(text="📥 Excel yuklash", callback_data="admin_export_questions")],
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="back_to_admin")]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "admin_refresh_stats")
async def refresh_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    
    await callback.message.delete()
    await show_questions_stats(callback.message)
    await callback.answer()


@dp.callback_query(F.data == "admin_export_questions")
async def export_questions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    
    # Excel fayl yaratish (soddaroq variant - CSV)
    import csv
    import io
    from datetime import datetime
    
    db.cursor.execute('''
        SELECT id, question_uz, question_ru, question_ar, question_en,
               correct_option, created_at, is_active
        FROM questions
        ORDER BY id DESC
    ''')
    
    questions = db.cursor.fetchall()
    
    # CSV fayl yaratish
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Savol (UZ)', 'Savol (RU)', 'Savol (AR)', 'Savol (EN)', 
                     'To\'g\'ri javob', 'Qo\'shilgan vaqt', 'Faol'])
    
    for q in questions:
        writer.writerow(q)
    
    csv_data = output.getvalue().encode('utf-8')
    
    # Faylni yuborish
    from aiogram.types import InputFile
    from aiogram import types
    
    await callback.message.answer_document(
        types.InputFile(io.BytesIO(csv_data), filename=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"),
        caption="📥 Savollar ro'yxati"
    )
    
    await callback.answer()    
    
@dp.message()
async def handle_text_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    
    if is_admin(user_id):
        return
    
    # ===== MENYU TUGMALARINI TEKSHIRISH =====
    menu_buttons = [
        "❓ Savollar", "❓ Вопросы", "❓ أسئلة", "❓ Questions",
        "👤 Payg'ambarlar hayoti", "👤 Жизнь пророков", "👤 حياة الأنبياء", "👤 Prophets life",
        "🤲 Allohning 99 ismi", "🤲 99 имен Аллаха", "🤲 أسماء الله الحسنى", "🤲 99 Names of Allah",
        "📿 Kundalik zikrlar", "📿 Ежедневные зикры", "📿 أذكار اليومية", "📿 Daily dhikr",
        "🌐 Tilni o'zgartirish", "🌐 Сменить язык", "🌐 تغيير اللغة", "🌐 Change language",
        "🔄 Yangi savol", "🔄 Новый вопрос", "🔄 سؤال جديد", "🔄 New question"
    ]
    
    if text in menu_buttons:
        if text in ["🤲 Allohning 99 ismi", "🤲 99 имен Аллаха", "🤲 أسماء الله الحسنى", "🤲 99 Names of Allah"]:
            await allah_names_handler(message)
        elif text in ["❓ Savollar", "❓ Вопросы", "❓ أسئلة", "❓ Questions"]:
            await questions_handler(message)
        elif text in ["👤 Payg'ambarlar hayoti", "👤 Жизнь пророков", "👤 حياة الأنبياء", "👤 Prophets life"]:
            await prophets_handler(message)
        elif text in ["📿 Kundalik zikrlar", "📿 Ежедневные зикры", "📿 أذكار اليومية", "📿 Daily dhikr"]:
            await zikr_handler(message)
        elif text in ["🌐 Tilni o'zgartirish", "🌐 Сменить язык", "🌐 تغيير اللغة", "🌐 Change language"]:
            await change_lang_handler(message)
        elif text in ["🔄 Yangi savol", "🔄 Новый вопрос", "🔄 سؤال جديد", "🔄 New question"]:
            await new_question_handler(message)
        return
    
    # Agar foydalanuvchi registratsiya jarayonida bo'lsa
    current_state = await state.get_state()
    if current_state:
        return
    
    # Foydalanuvchi sessiyasini tekshirish
    if user_id not in user_sessions or 'current_question' not in user_sessions[user_id]:
        lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
        if not lang:
            lang = db.get_user_language(user_id)
        info_messages = {
            'UZ': "Iltimos, avval '❓ Savollar' tugmasini bosing.",
            'RU': "Пожалуйста, сначала нажмите '❓ Вопросы'.",
            'AR': "يرجى الضغط أولاً على '❓ أسئلة'.",
            'EN': "Please press '❓ Questions' first."
        }
        await message.answer(info_messages.get(lang, info_messages['UZ']))
        return
    
    # Kutish vaqtini tekshirish
    is_waiting, remaining = db.check_user_wait(user_id)
    if is_waiting:
        lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
        if not lang:
            lang = db.get_user_language(user_id)
        wait_messages = {
            'UZ': f"⏳ Siz xato javob berganingiz uchun {remaining} daqiqa kutishingiz kerak.",
            'RU': f"⏳ Из-за неверного ответа вам нужно подождать {remaining} минут.",
            'AR': f"⏳ بسبب إجابتك الخاطئة، عليك الانتظار لمدة {remaining} دقيقة.",
            'EN': f"⏳ Due to wrong answer, you need to wait {remaining} minutes."
        }
        await message.answer(wait_messages.get(lang, wait_messages['UZ']))
        return
    
    # Foydalanuvchi tilini olish
    db_lang = db.get_user_language(user_id)
    session_lang = user_sessions[user_id].get('lang', 'UZ')
    
    if db_lang != session_lang:
        print(f"🔄 Til yangilandi: session={session_lang} -> baza={db_lang}")
        user_sessions[user_id]['lang'] = db_lang
        lang = db_lang
    else:
        lang = session_lang
    
    # Joriy savol ma'lumotlarini olish
    current_q = user_sessions[user_id]['current_question']
    question_id = current_q['id']
    correct_text = current_q['correct_text']
    correct = current_q['correct']
    
    # Foydalanuvchi javobini tozalash
    user_answer = message.text.lower().strip()
    
    # ===== JAVOB TEKSHIRISH =====
    import re
    correct_text_clean = re.sub(r'^[\d\s.)]+', '', correct_text).lower().strip()
    
    parts = correct_text.split()
    if len(parts) > 1 and parts[0].strip().replace('.', '').isdigit():
        correct_text_without_number = ' '.join(parts[1:]).lower().strip()
    else:
        correct_text_without_number = correct_text.lower().strip()
    
    important_words = [word for word in correct_text_without_number.split() if len(word) > 3]
    
    is_correct = (
        user_answer == correct_text.lower().strip() or
        user_answer == correct_text_clean or
        user_answer == correct_text_without_number or
        user_answer in correct_text_without_number or
        correct_text_without_number in user_answer or
        (len(important_words) > 0 and all(word in user_answer for word in important_words)) or
        (len(important_words) > 0 and any(word in user_answer for word in important_words) and 
         len(user_answer) > len(important_words[0]) - 2)
    )
    
    print(f"\n🔍 JAVOB TEKSHIRISH:")
    print(f"   👤 Foydalanuvchi: '{user_answer}'")
    print(f"   ✅ To'g'ri javob: '{correct_text}'")
    print(f"   📊 Natija: {is_correct}")
    print(f"   🌐 Til: {lang}")
    
    # Javobni bazaga saqlash
    db.save_answer(user_id, question_id, 0, is_correct)
    db.update_user_stats(user_id, is_correct)
    
    # 20 ta savol sessiyasini tekshirish
    active_session = db.get_active_session(user_id)
    session_id = None
    
    if active_session:
        session_id = active_session[0]
    
    if is_correct:
        # ===== TO'G'RI JAVOB =====
        if not active_session:
            session_id = db.start_20_questions_session(user_id)
            if session_id:
                db.save_question_answer(user_id, session_id, question_id, 0, True)
                active_session = db.get_active_session(user_id)
        else:
            db.save_question_answer(user_id, session_id, question_id, 0, True)
            active_session = db.get_active_session(user_id)
        
        # ===== 20 TA SAVOLGA YETDIMI? (ANIMATSIYALI VERSIYA) =====
        if active_session and active_session[1] >= 20:
            db.complete_session(session_id, user_id, success=True)
            reward_id = db.create_reward(user_id, session_id)
            
            lang = user_sessions[user_id].get('lang', 'UZ')
            
            # Tilga mos matnlar
            fireworks_text = {
                'UZ': "🎆 **SALYUTLAR!** 🎆",
                'RU': "🎆 **ФЕЙЕРВЕРК!** 🎆",
                'AR': "🎆 **الألعاب النارية!** 🎆",
                'EN': "🎆 **FIREWORKS!** 🎆"
            }
            
            drum_text = {
                'UZ': "🥁 **BARABAN SADOLARI** 🥁",
                'RU': "🥁 **БАРАБАННАЯ ДРОБЬ** 🥁",
                'AR': "🥁 **قرع الطبول** 🥁",
                'EN': "🥁 **DRUM ROLL** 🥁"
            }
            
            # 1. SALYUTLAR ANIMATSIYASI (otilib-o'chib turadi)
            await message.answer(fireworks_text.get(lang, fireworks_text['UZ']))
            await asyncio.sleep(0.5)
            
            # Mushaklar otilishi (30 marta tez-tez)
            fireworks_frames = [
                "    🎆", "   🎆✨", "  🎆✨🌟", " 🎆✨🌟🎇", "🎆✨🌟🎇⭐",
                " ✨🌟🎇⭐💫", "  🌟🎇⭐💫", "   🎇⭐💫", "    ⭐💫", "     💫"
            ]
            
            for i in range(30):
                frame = fireworks_frames[i % len(fireworks_frames)]
                msg = await message.answer(f"`{frame}`")
                await asyncio.sleep(0.1)
                await msg.delete()
            
            # 2. BARABAN ANIMATSIYASI (tez-tez)
            await message.answer(drum_text.get(lang, drum_text['UZ']))
            await asyncio.sleep(0.3)
            
            drum_frames = ["🥁", "🥁🥁", "🥁🥁🥁", "🥁🥁🥁🥁", "🥁🥁🥁🥁🥁"]
            for i in range(20):
                frame = drum_frames[i % len(drum_frames)]
                msg = await message.answer(f"**{frame}**")
                await asyncio.sleep(0.1)
                await msg.delete()
            
            # 3. SOVG'A QUTISI (asta-sekin paydo bo'ladi)
            gift_lines = [
                "╔══════════════════════════════════════╗",
                "║           🎁 SOVG'A QUTISI 🎁        ║",
                "╠══════════════════════════════════════╣",
                "║         🎉 TABRIKLAYMIZ! 🎉          ║",
                "║    Siz 20 ta savolga to'g'ri         ║",
                "║    javob berib, 200 000 so'm         ║",
                "║    mukofotni yutib oldingiz!         ║",
                "║       💰 **200 000 SO'M** 💰         ║",
                "╚══════════════════════════════════════╝"
            ]
            
            gift_msg = ""
            for line in gift_lines:
                gift_msg += line + "\n"
                temp_msg = await message.answer(gift_msg)
                await asyncio.sleep(0.1)
                if line != gift_lines[-1]:
                    await temp_msg.delete()
            
            await asyncio.sleep(0.5)
            
            # 4. KONFETTI (aylanib tushadi)
            confetti = ["🎊", "🎈", "🎉", "✨", "⭐", "💫"]
            for i in range(30):
                c = confetti[i % len(confetti)]
                spaces = " " * (i % 10)
                msg = await message.answer(f"{spaces}{c}")
                await asyncio.sleep(0.05)
                await msg.delete()
            
            # 5. KARTA SO'RASH (sekin paydo bo'ladi)
            card_lines = [
                "💳",
                "💳 **Iltimos,**",
                "💳 **Iltimos, karta raqamingizni**",
                "💳 **Iltimos, karta raqamingizni kiriting:**",
                "💳 **Iltimos, karta raqamingizni kiriting:**\nMisol: `8600 1234 5678 9012`"
            ]
            
            for line in card_lines:
                msg = await message.answer(line)
                await asyncio.sleep(0.2)
                if line != card_lines[-1]:
                    await msg.delete()
            
            await state.set_state(RewardState.waiting_for_card)
            return
        
        # To'g'ri javob xabari
        correct_messages = {
            'UZ': "✅ To'g'ri javob!",
            'RU': "✅ Правильный ответ!",
            'AR': "✅ إجابة صحيحة!",
            'EN': "✅ Correct answer!"
        }
        
        progress = f"\n\n📊 20/20: {active_session[1]}/20 to'g'ri" if active_session else ""
        
        await message.answer(f"{correct_messages.get(lang, correct_messages['UZ'])}{progress}\n\n✨ Tabriklaymiz! ✨")
        await message.answer("🎉 ⭐️ 🌟 ✨ ⭐️ 🌟 🎉")
        
        # Admin ga xabar
        user_name = user_sessions[user_id].get('name', 'Noma\'lum')
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"📊 **Javob**\n\n👤 {user_name}\n🆔 `{user_id}`\n📝 ✅ To'g'ri\n❓ ID: {question_id}")
            except:
                pass
        
        # Yangi savol
        await asyncio.sleep(1)
        source = user_sessions[user_id]['current_question'].get('source', 'questions')
        seen_list = 'questions_seen' if source == 'questions' else 'new_questions_seen'
        
        if seen_list not in user_sessions[user_id]:
            user_sessions[user_id][seen_list] = []
        seen_questions = user_sessions[user_id][seen_list]
        
        new_question = db.get_random_question_excluding(lang, seen_questions)
        
        if new_question:
            q_id, q_text, opt1, opt2, opt3, correct = new_question
            
            if q_id not in seen_questions:
                user_sessions[user_id][seen_list].append(q_id)
            
            correct_answer_text = [opt1, opt2, opt3][correct-1]
            
            user_sessions[user_id]['current_question'] = {
                'id': q_id,
                'correct': correct,
                'correct_text': correct_answer_text,
                'options': [opt1, opt2, opt3],
                'source': source
            }
            
            active_session = db.get_active_session(user_id)
            reward_text = ""
            
            if active_session:
                correct_count = active_session[1]
                remaining = 20 - correct_count
                reward_text = f"\n\n━━━━━━━━━━━━━━━━━━━━\n🎁 **MUKOFOT DASTURI**\n✅ To'g'ri javoblar: {correct_count}/20\n⏳ Qolgan: {remaining} ta\n💰 Mukofot: 200 000 so'm\n━━━━━━━━━━━━━━━━━━━━\n"
            else:
                reward_text = f"\n\n━━━━━━━━━━━━━━━━━━━━\n🎁 **20 TA SAVOLGA TO'G'RI JAVOB BERIB**\n💰 **200 000 SO'M YUTIB OLING!**\n━━━━━━━━━━━━━━━━━━━━\n"
            
            prefix = "❓ Savol" if source == 'questions' else "🆕 Yangi savol"
            
            await message.answer(f"{prefix}:\n\n{q_text}{reward_text}\n\n📝 **Javobingizni yozib yuboring:**")
        else:
            all_done = "🎉 Tabriklaymiz! Siz barcha savollarni yakunladingiz!" if source == 'questions' else "🎉 Yangi savollar mavjud emas. Tez orada qo'shiladi!"
            await message.answer(all_done, reply_markup=get_main_menu_keyboard(lang))
    
    else:
        # ===== NOTO'G'RI JAVOB =====
        if active_session:
            db.save_question_answer(user_id, session_id, question_id, 0, False)
            db.complete_session(session_id, user_id, success=False)
        
        db.set_user_wait(user_id, minutes=30)
        
        display_correct = current_q['options'][correct-1]
        display_correct_clean = re.sub(r'^[\d\s.)]+', '', display_correct).strip()
        
        wrong_messages = {
            'UZ': f"❌ Noto'g'ri javob!\n\n✅ To'g'ri javob: {display_correct_clean}",
            'RU': f"❌ Неправильный ответ!\n\n✅ Правильный ответ: {display_correct_clean}",
            'AR': f"❌ إجابة خاطئة!\n\n✅ الإجابة الصحيحة: {display_correct_clean}",
            'EN': f"❌ Wrong answer!\n\n✅ Correct answer: {display_correct_clean}"
        }
        
        await message.answer(wrong_messages.get(lang, wrong_messages['UZ']))
        
        wait_messages = {
            'UZ': "⏳ Hurmatli foydalanuvchi!\n\nSiz xato javob berganingiz uchun keyingi savol 30 daqiqadan so'ng ochiladi.\nIltimos, sabr qiling! 🤲",
            'RU': "⏳ Уважаемый пользователь!\n\nИз-за неверного ответа следующий вопрос будет доступен через 30 минут.\nПожалуйста, наберитесь терпения! 🤲",
            'AR': "⏳ عزيزي المستخدم!\n\nنظرًا لإجابتك الخاطئة، سيكون السؤال التالي متاحًا بعد 30 دقيقة.\nيرجى التحلي بالصبر! 🤲",
            'EN': "⏳ Dear user!\n\nDue to your wrong answer, the next question will be available in 30 minutes.\nPlease be patient! 🤲"
        }
        
        await message.answer(wait_messages.get(lang, wait_messages['UZ']))
        
        user_name = user_sessions[user_id].get('name', 'Noma\'lum')
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"📊 **Javob**\n\n👤 {user_name}\n🆔 `{user_id}`\n📝 ❌ Noto'g'ri\n❓ ID: {question_id}\n⏳ 30 daqiqa")
            except:
                pass
        
        source = user_sessions[user_id]['current_question'].get('source', 'questions')
        if source == 'questions':
            user_sessions[user_id]['questions_seen'] = []
        else:
            user_sessions[user_id]['new_questions_seen'] = []
        
        user_sessions[user_id].pop('current_question', None)

# Yangi savol
@dp.callback_query(F.data == "new_question")
async def inline_new_question(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if is_admin(user_id):
        await callback.answer()
        return
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    await callback.message.delete()
    
    # Yangi savol olish
    question = db.get_random_question(lang)
    
    if not question:
        no_questions = {
            'UZ': "Hozircha savollar mavjud emas.",
            'RU': "Пока нет вопросов.",
            'AR': "لا توجد أسئلة حتى الآن.",
            'EN': "No questions available yet."
        }
        await callback.message.answer(
            no_questions.get(lang, no_questions['UZ']),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await callback.answer()
        return
    
    q_id, q_text, opt1, opt2, opt3, correct = question
    
    user_sessions[user_id]['current_question'] = {
        'id': q_id,
        'correct': correct
    }
    
    question_prefix = {
        'UZ': "❓ Savol",
        'RU': "❓ Вопрос",
        'AR': "❓ سؤال",
        'EN': "❓ Question"
    }
    
    # Savol matnini yuborish
    await callback.message.answer(
        f"{question_prefix.get(lang, '❓ Savol')}:\n\n{q_text}"
    )
    
    # Variantlarni yuborish
    await callback.message.answer(
        "👇 Javob variantlari:",
        reply_markup=get_options_inline_keyboard((opt1, opt2, opt3), q_id, lang)
    )
    
    await callback.answer()

@dp.message(lambda msg: msg.text in ["🔄 Yangi savol", "🔄 Новый вопрос", "🔄 سؤال جديد", "🔄 New question"])
async def new_question_handler(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang, 'seen_questions': []}
    
    if 'seen_questions' not in user_sessions[user_id]:
        user_sessions[user_id]['seen_questions'] = []
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    seen_questions = user_sessions[user_id].get('seen_questions', [])
    
    # Yangi savol olish (ko'rilmagan)
    question = db.get_random_question_excluding(lang, seen_questions)
    
    if not question:
        # Agar barcha savollar ko'rilgan bo'lsa
        no_questions = {
            'UZ': "Barcha savollar yakunlandi! Tez orada yangi savollar qo'shiladi.",
            'RU': "Все вопросы завершены! Скоро будут добавлены новые вопросы.",
            'AR': "تم الانتهاء من جميع الأسئلة! سيتم إضافة أسئلة جديدة قريباً.",
            'EN': "All questions completed! New questions will be added soon."
        }
        await message.answer(no_questions.get(lang, no_questions['UZ']))
        return
    
    q_id, q_text, opt1, opt2, opt3, correct = question
    
    # Savolni ko'rilganlar ro'yxatiga qo'shish
    if q_id not in seen_questions:
        user_sessions[user_id]['seen_questions'].append(q_id)
    
    # Joriy savol ma'lumotlarini saqlash
    correct_answer_text = ""
    if correct == 1:
        correct_answer_text = opt1
    elif correct == 2:
        correct_answer_text = opt2
    else:
        correct_answer_text = opt3
    
    user_sessions[user_id]['current_question'] = {
        'id': q_id,
        'correct': correct,
        'correct_text': correct_answer_text,
        'options': [opt1, opt2, opt3]
    }
    
    question_prefix = {
        'UZ': "❓ Savol",
        'RU': "❓ Вопрос",
        'AR': "❓ سؤال",
        'EN': "❓ Question"
    }
    
    # Mukofot matni
    active_session = db.get_active_session(user_id)
    reward_text = ""
    
    if active_session:
        correct_count = active_session[1]
        remaining = 20 - correct_count
        reward_text = (
            f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 **MUKOFOT DASTURI**\n"
            f"✅ To'g'ri javoblar: {correct_count}/20\n"
            f"⏳ Qolgan: {remaining} ta\n"
            f"💰 Mukofot: 200 000 so'm\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
    else:
        reward_text = (
            f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 **20 TA SAVOLGA TO'G'RI JAVOB BERIB**\n"
            f"💰 **200 000 SO'M YUTIB OLING!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
    
    # Savol matnini yuborish (mukofot matni bilan)
    await message.answer(
        f"{question_prefix.get(lang, '❓ Savol')}:\n\n{q_text}{reward_text}\n\n📝 **Javobingizni yozib yuboring:**"
    )

# Payg'ambarlar hayoti
@dp.message(lambda msg: msg.text in ["👤 Payg'ambarlar hayoti", "👤 Жизнь пророков", "👤 حياة الأنبياء", "👤 Prophets life"])
async def prophets_handler(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
    
    prophets = db.get_prophets(lang)
    
    if not prophets:
        no_prophets = {
            'UZ': "Hozircha payg'ambarlar haqida ma'lumot yo'q.",
            'RU': "Пока нет информации о пророках.",
            'AR': "لا توجد معلومات عن الأنبياء حتى الآن.",
            'EN': "No prophets information yet."
        }
        await message.answer(
            no_prophets.get(lang, no_prophets['UZ']),
            reply_markup=get_main_menu_keyboard(lang)
        )
        return
    
    prophets_title = {
        'UZ': "Payg'ambarlar hayoti:",
        'RU': "Жизнь пророков:",
        'AR': "حياة الأنبياء:",
        'EN': "Prophets life:"
    }
    
    await message.answer(
        prophets_title.get(lang, prophets_title['UZ']),
        reply_markup=get_prophets_inline_keyboard(prophets, lang)
    )

# Payg'ambar audio
@dp.callback_query(F.data.startswith('prophet_'))
async def send_prophet_audio(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if is_admin(user_id):
        await callback.answer()
        return
    
    prophet_id = int(callback.data.split('_')[1])
    audio_id = db.get_prophet_audio(prophet_id)
    
    if audio_id:
        await callback.message.answer_audio(audio_id)
    else:
        lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
        error_messages = {
            'UZ': "Audio topilmadi",
            'RU': "Аудио не найдено",
            'AR': "لم يتم العثور على الصوت",
            'EN': "Audio not found"
        }
        await callback.message.answer(error_messages.get(lang, error_messages['UZ']))
    
    await callback.answer()

# Kundalik zikrlar
@dp.message(lambda msg: msg.text in ["📿 Kundalik zikrlar", "📿 Ежедневные зикры", "📿 أذكار اليومية", "📿 Daily dhikr"])
async def zikr_handler(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
    
    zikr_texts = {
        'UZ': (
            "📿 KUNDALIK ZIKRLAR\n\n"
            "1. SubhanAllah (33 marta) - سبحان الله\n"
            "2. Alhamdulillah (33 marta) - الحمد لله\n"
            "3. Allahu Akbar (34 marta) - الله أكبر\n"
            "4. La ilaha illallah - لا إله إلا الله\n"
            "5. Astaghfirullah - أستغفر الله\n"
            "6. Salavat sharif - اللهم صل على محمد\n\n"
            "👉 Har namozdan keyin 33+33+34 = 100 ta zikr"
        ),
        'RU': (
            "📿 ЕЖЕДНЕВНЫЕ ЗИКРЫ\n\n"
            "1. SubhanAllah (33 раза) - سبحان الله\n"
            "2. Alhamdulillah (33 раза) - الحمد لله\n"
            "3. Allahu Akbar (34 раза) - الله أكبر\n"
            "4. La ilaha illallah - لا إله إلا الله\n"
            "5. Astaghfirullah - أستغفر الله\n"
            "6. Salavat sharif - اللهم صل على محمد\n\n"
            "👉 После каждого намаза 33+33+34 = 100 зикров"
        ),
        'AR': (
            "📿 الأذكار اليومية\n\n"
            "1. سبحان الله (33 مرة)\n"
            "2. الحمد لله (33 مرة)\n"
            "3. الله أكبر (34 مرة)\n"
            "4. لا إله إلا الله\n"
            "5. أستغفر الله\n"
            "6. اللهم صل على محمد\n\n"
            "👉 بعد كل صلاة 33+33+34 = 100 ذكر"
        ),
        'EN': (
            "📿 DAILY DHIKR\n\n"
            "1. SubhanAllah (33 times) - سبحان الله\n"
            "2. Alhamdulillah (33 times) - الحمد لله\n"
            "3. Allahu Akbar (34 times) - الله أكبر\n"
            "4. La ilaha illallah - لا إله إلا الله\n"
            "5. Astaghfirullah - أستغفر الله\n"
            "6. Salawat sharif - اللهم صل على محمد\n\n"
            "👉 After each prayer 33+33+34 = 100 dhikr"
        )
    }
    
    await message.answer(
        zikr_texts.get(lang, zikr_texts['UZ']),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
# Allohning 99 ismi - asosiy handler
@dp.message(lambda msg: msg.text in ["🤲 Allohning 99 ismi", "🤲 99 имен Аллаха", "🤲 أسماء الله الحسنى", "🤲 99 Names of Allah"])
async def allah_names_handler(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    # Alloh ismlarini olish
    names = db.get_allah_names(lang)
    
    if not names:
        no_names_messages = {
            'UZ': "Hozircha Allohning ismlari ro'yxati mavjud emas.",
            'RU': "Пока нет списка имен Аллаха.",
            'AR': "لا توجد قائمة أسماء الله الحسنى حتى الآن.",
            'EN': "No list of Allah's names available yet."
        }
        await message.answer(
            no_names_messages.get(lang, no_names_messages['UZ']),
            reply_markup=get_main_menu_keyboard(lang)
        )
        return
    
    title_messages = {
        'UZ': "🤲 ALLOHNING 99 GO'ZAL ISMLARI",
        'RU': "🤲 99 ПРЕКРАСНЫХ ИМЕН АЛЛАХА",
        'AR': "🤲 أَسْمَاءُ اللَّهِ الْحُسْنَى",
        'EN': "🤲 99 BEAUTIFUL NAMES OF ALLAH"
    }
    
    hadith_messages = {
        'UZ': "Nabiy Sallallohu Alayhi Vossallam: «Allohning to'qson to'qqizta ismi bor. Kim ularni yod olsa, Jannatga kiradi. Albatta, Alloh toqdir va toqni yaxshi ko'radi» dedilar.☝️😊",
        'RU': "Пророк (мир ему и благословение Аллаха) сказал: «У Аллаха девяносто девять имен. Кто выучит их, тот войдет в Рай. Поистине, Аллах нечетный и любит нечетное».",
        'AR': "قال النبي صلى الله عليه وسلم: «إن لله تسعة وتسعين اسما، من أحصاها دخل الجنة، إن الله وتر يحب الوتر».",
        'EN': "The Prophet (peace be upon him) said: \"Allah has ninety-nine names. Whoever memorizes them will enter Paradise. Indeed, Allah is Odd and loves odd numbers.\" ☝️😊"
    }
    
    xatolik_messages = {
        'UZ': "\n\nXatolarimizni Allohning O'zi kechirsin... 🤲",
        'RU': "\n\nПусть Аллах простит наши ошибки... 🤲",
        'AR': "\n\nاللهم اغفر لنا خطايانا... 🤲",
        'EN': "\n\nMay Allah forgive our mistakes... 🤲"
    }
    
    # Hadis bilan birga yuborish
    await message.answer(
        f"{title_messages.get(lang, title_messages['UZ'])}\n\n"
        f"{hadith_messages.get(lang, hadith_messages['UZ'])}"
    )
    
    # Ismlar ro'yxatini yuborish
    await message.answer(
        "👇 Ismlar ro'yxati:",
        reply_markup=get_allah_names_inline_keyboard(names, lang)
    )

# Alohida ismni ko'rish
@dp.callback_query(F.data.startswith('allah_name_'))
async def allah_name_detail(callback: CallbackQuery):
    user_id = callback.from_user.id
    number = int(callback.data.split('_')[2])
    
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    # Ism ma'lumotlarini olish
    name_data = db.get_allah_name_by_number(number, lang)
    
    if not name_data:
        await callback.answer("Ma'lumot topilmadi")
        return
    
    num, name, desc = name_data
    
    # Tilga mos matnlar - oddiy matn bilan
    if lang == 'UZ':
        text = f"🤲 {num}-ISMI SHARIF\n\n"
        text += f"📝 O'qilishi: {name}\n"
        if desc:
            text += f"📖 Ma'nosi: {desc}\n\n"
        else:
            text += "📖 Ma'nosi: Ma'lumot mavjud emas\n\n"
        text += '"Kim Allohning bu ismini yod olsa..."'
    elif lang == 'RU':
        text = f"🤲 {num}-ИМЯ АЛЛАХА\n\n"
        text += f"📝 Произношение: {name}\n"
        if desc:
            text += f"📖 Значение: {desc}\n\n"
        else:
            text += "📖 Значение: Информация отсутствует\n\n"
        text += '"Кто запомнит это имя Аллаха..."'
    elif lang == 'AR':
        text = f"🤲 الاسم {num}\n\n"
        text += f"📝 الاسم: {name}\n"
        if desc:
            text += f"📖 المعنى: {desc}\n\n"
        else:
            text += "📖 المعنى: لا توجد معلومات\n\n"
        text += '"من حفظ اسم الله هذا..."'
    else:  # EN
        text = f"🤲 {num}th NAME OF ALLAH\n\n"
        text += f"📝 Pronunciation: {name}\n"
        if desc:
            text += f"📖 Meaning: {desc}\n\n"
        else:
            text += "📖 Meaning: No information available\n\n"
        text += '"Whoever memorizes this name of Allah..."'
    
    await callback.message.edit_text(text)
    
    # Orqaga qaytish tugmasi
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    back_texts = {
        'UZ': "🔙 Ro'yxatga qaytish",
        'RU': "🔙 Вернуться к списку",
        'AR': "🔙 العودة إلى القائمة",
        'EN': "🔙 Back to list"
    }
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=back_texts.get(lang, "🔙 Back"),
            callback_data="back_to_allah_names"
        )]
    ])
    
    await callback.message.answer(
        "👇",
        reply_markup=keyboard
    )
    
    await callback.answer()

# Ro'yxatga qaytish
@dp.callback_query(F.data == "back_to_allah_names")
async def back_to_allah_names(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    names = db.get_allah_names(lang)
    
    await callback.message.delete()
    await callback.message.answer(
        "👇 Ismlar ro'yxati:",
        reply_markup=get_allah_names_inline_keyboard(names, lang)
    )
    await callback.answer()

# Pagination handler
@dp.callback_query(F.data.startswith('allah_page_'))
async def allah_names_page(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = int(callback.data.split('_')[2])
    
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    names = db.get_allah_names(lang)
    
    await callback.message.edit_text(
        "👇 Ismlar ro'yxati:",
        reply_markup=get_allah_names_inline_keyboard(names, lang, page)
    )
    await callback.answer()    

# Noma'lum xabarlar
@dp.message()
async def handle_unknown(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        return
    
    # User sessions ni tekshirish
    if user_id not in user_sessions:
        lang = db.get_user_language(user_id)
        user_sessions[user_id] = {'name': '', 'lang': lang}
    
    if salawat_count.get(user_id, 0) > 0 and salawat_count.get(user_id, 0) <= 10:
        return
    
    current_state = await state.get_state()
    if current_state == RegisterState.waiting_for_name:
        return
    
    lang = user_sessions[user_id].get('lang', 'UZ')
    
    unknown_msgs = {
        'UZ': "Iltimos menyudan foydalaning.",
        'RU': "Пожалуйста, используйте меню.",
        'AR': "الرجاء استخدام القائمة.",
        'EN': "Please use the menu."
    }
    
    await message.answer(
        unknown_msgs.get(lang, unknown_msgs['UZ']),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
# ============================================
# ADMIN PANEL - FOYDALANUVCHILAR RO'YXATI
# ============================================

@dp.message(lambda msg: msg.text == "👥 Foydalanuvchilar" and is_admin(msg.from_user.id))
async def admin_users_list(message: Message):
    """Barcha foydalanuvchilar ro'yxati"""
    users = db.get_all_users_stats()
    
    if not users:
        await message.answer("📭 Hozircha foydalanuvchilar yo'q")
        return
    
    await message.answer(
        f"👥 **Foydalanuvchilar** ({len(users)} ta)\n\n"
        f"✅ To'g'ri | ❌ Noto'g'ri | 🏆 Rekord",
        reply_markup=get_users_inline_keyboard(users)
    )

@dp.callback_query(F.data.startswith('admin_user_'))
async def admin_user_detail(callback: CallbackQuery):
    """Foydalanuvchi haqida batafsil"""
    user_id = int(callback.data.split('_')[2])
    
    # Foydalanuvchi ma'lumotlari
    db.cursor.execute('''
        SELECT first_name, username, language, registered_at 
        FROM users WHERE user_id = ?
    ''', (user_id,))
    user = db.cursor.fetchone()
    
    # Statistika
    db.cursor.execute('''
        SELECT correct_count, wrong_count, total_questions, best_streak
        FROM user_stats WHERE user_id = ?
    ''', (user_id,))
    stats = db.cursor.fetchone()
    
    if not user:
        await callback.answer("Foydalanuvchi topilmadi")
        return
    
    name, username, lang, reg_date = user
    correct = stats[0] if stats else 0
    wrong = stats[1] if stats else 0
    total = stats[2] if stats else 0
    streak = stats[3] if stats else 0
    
    # Reg_date ni formatlash
    reg_date_str = reg_date[:10] if reg_date else "Noma'lum"
    
    # Oxirgi javoblar
    db.cursor.execute('''
        SELECT q.question_uz, ua.selected_option, ua.is_correct, ua.answered_at
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ?
        ORDER BY ua.answered_at DESC LIMIT 5
    ''', (user_id,))
    last_answers = db.cursor.fetchall()
    
    # Matnni alohida qurish
    text_parts = []
    text_parts.append("👤 **Foydalanuvchi ma'lumotlari**\n")
    text_parts.append(f"🆔 ID: `{user_id}`\n")
    text_parts.append(f"📝 Ism: {name}\n")
    text_parts.append(f"🌐 Username: @{username if username else 'yoq'}\n")
    text_parts.append(f"🗣 Til: {lang}\n")
    text_parts.append(f"📅 Ro'yxat: {reg_date_str}\n")
    text_parts.append("\n📊 **Statistika**\n")
    text_parts.append(f"✅ To'g'ri: {correct}\n")
    text_parts.append(f"❌ Noto'g'ri: {wrong}\n")
    text_parts.append(f"📝 Jami: {total}\n")
    text_parts.append(f"🏆 Eng yaxshi: {streak}\n")
    
    if last_answers:
        text_parts.append("\n📋 **Oxirgi 5 ta javob:**\n")
        for i, ans in enumerate(last_answers, 1):
            q_text, selected, is_correct, ans_time = ans
            status = "✅" if is_correct else "❌"
            ans_time_str = ans_time[:16] if ans_time else ""
            text_parts.append(f"{i}. {status} {q_text[:30]}... ({ans_time_str})\n")
    
    text = "".join(text_parts)
    
    # Inline keyboard
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Barcha javoblar", callback_data=f"admin_user_answers_{user_id}")],
        [InlineKeyboardButton(text="💰 Mukofotlar tarixi", callback_data=f"admin_user_rewards_{user_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_users_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith('admin_user_answers_'))
async def admin_user_answers(callback: CallbackQuery):
    """Foydalanuvchining barcha javoblari"""
    user_id = int(callback.data.split('_')[3])
    
    answers = db.get_user_answers(user_id, limit=50)
    
    if not answers:
        await callback.message.edit_text("📭 Javoblar yo'q")
        return
    
    text = f"📝 **Foydalanuvchi javoblari** (ID: {user_id})\n\n"
    for i, ans in enumerate(answers[:10], 1):
        ans_id, _, q_id, selected, is_correct, ans_time, name, username, question = ans
        status = "✅" if is_correct else "❌"
        text += f"{i}. {status} Savol {q_id}: {question[:40]}...\n"
    
    if len(answers) > 10:
        text += f"\n... va yana {len(answers)-10} ta javob"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin_user_{user_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "admin_users_back")
async def admin_users_back(callback: CallbackQuery):
    """Foydalanuvchilar ro'yxatiga qaytish"""
    users = db.get_all_users_stats()
    await callback.message.edit_text(
        f"👥 **Foydalanuvchilar** ({len(users)} ta)",
        reply_markup=get_users_inline_keyboard(users)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith('admin_users_page_'))
async def admin_users_page(callback: CallbackQuery):
    """Foydalanuvchilar ro'yxati sahifalash"""
    page = int(callback.data.split('_')[3])
    users = db.get_all_users_stats()
    await callback.message.edit_reply_markup(
        reply_markup=get_users_inline_keyboard(users, page)
    )
    await callback.answer()


# ============================================
# ADMIN PANEL - JAVOBLARNI KO'RISH
# ============================================

@dp.message(lambda msg: msg.text == "📝 Javoblarni ko'rish" and is_admin(msg.from_user.id))
async def admin_answers_list(message: Message):
    """Barcha javoblar ro'yxati"""
    answers = db.get_user_answers(limit=100)
    
    if not answers:
        await message.answer("📭 Hozircha javoblar yo'q")
        return
    
    await message.answer(
        f"📝 **Oxirgi javoblar** ({len(answers)} ta)",
        reply_markup=get_answers_inline_keyboard(answers)
    )

@dp.callback_query(F.data.startswith('admin_answer_'))
async def admin_answer_detail(callback: CallbackQuery):
    """Javob haqida batafsil"""
    answer_id = int(callback.data.split('_')[2])
    
    db.cursor.execute('''
        SELECT ua.*, u.first_name, u.username, u.user_id, q.question_uz, q.correct_option,
               q.option1_uz, q.option2_uz, q.option3_uz
        FROM user_answers ua
        JOIN users u ON ua.user_id = u.user_id
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.id = ?
    ''', (answer_id,))
    answer = db.cursor.fetchone()
    
    if not answer:
        await callback.answer("Javob topilmadi")
        return
    
    (ans_id, user_id, q_id, selected, is_correct, ans_time,
     name, username, _, question, correct,
     opt1, opt2, opt3) = answer
    
    status = "✅ TO'G'RI" if is_correct else "❌ NOTO'G'RI"
    
    text = (
        f"📝 **JAVOB MA'LUMOTLARI**\n\n"
        f"👤 Foydalanuvchi: {name} (@{username if username else 'yoq'})\n"
        f"🆔 ID: `{user_id}`\n"
        f"📅 Vaqt: {ans_time}\n\n"
        f"❓ **Savol:**\n{question}\n\n"
        f"📋 **Variantlar:**\n"
        f"1️⃣ {opt1}\n"
        f"2️⃣ {opt2}\n"
        f"3️⃣ {opt3}\n\n"
        f"✅ To'g'ri javob: {correct}\n"
        f"👆 Tanlangan: {selected}\n"
        f"📊 Natija: {status}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Foydalanuvchi profili", callback_data=f"admin_user_{user_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_answers_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "admin_answers_back")
async def admin_answers_back(callback: CallbackQuery):
    """Javoblar ro'yxatiga qaytish"""
    answers = db.get_user_answers(limit=100)
    await callback.message.edit_text(
        f"📝 **Oxirgi javoblar** ({len(answers)} ta)",
        reply_markup=get_answers_inline_keyboard(answers)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith('admin_answers_page_'))
async def admin_answers_page(callback: CallbackQuery):
    """Javoblar ro'yxati sahifalash"""
    page = int(callback.data.split('_')[3])
    answers = db.get_user_answers(limit=100)
    await callback.message.edit_reply_markup(
        reply_markup=get_answers_inline_keyboard(answers, page)
    )
    await callback.answer()


# ============================================
# ADMIN PANEL - MUKOFOTLAR
# ============================================

@dp.message(lambda msg: msg.text == "💰 Mukofotlar" and is_admin(msg.from_user.id))
async def admin_rewards_menu(message: Message):
    """Mukofotlar menyusi"""
    text = (
        "💰 **MUKOFOTLAR BO'LIMI**\n\n"
        "• ⏳ Kutilayotgan mukofotlar\n"
        "• ✅ To'langan mukofotlar\n"
        "• 📊 Mukofot statistikasi"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Kutilayotganlar", callback_data="admin_rewards_pending")],
        [InlineKeyboardButton(text="✅ To'langanlar", callback_data="admin_rewards_paid")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_rewards_stats")],
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="back_to_admin")]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@dp.message(lambda msg: msg.text == "⏳ Kutilayotgan mukofotlar" and is_admin(msg.from_user.id))
async def admin_pending_rewards(message: Message):
    """Kutilayotgan mukofotlar"""
    rewards = db.get_pending_rewards()
    
    if not rewards:
        await message.answer("📭 Hozircha kutilayotgan mukofotlar yo'q")
        return
    
    await message.answer(
        f"⏳ **Kutilayotgan mukofotlar** ({len(rewards)} ta)",
        reply_markup=get_pending_rewards_keyboard(rewards)
    )

@dp.callback_query(F.data.startswith('admin_reward_'))
async def admin_reward_detail(callback: CallbackQuery):
    """Mukofot haqida batafsil"""
    reward_id = int(callback.data.split('_')[2])
    
    db.cursor.execute('''
        SELECT r.*, u.first_name, u.username, u.user_id, uc.card_number, uc.card_name
        FROM rewards r
        JOIN users u ON r.user_id = u.user_id
        LEFT JOIN user_cards uc ON r.user_id = uc.user_id
        WHERE r.id = ?
    ''', (reward_id,))
    reward = db.cursor.fetchone()
    
    if not reward:
        await callback.answer("Mukofot topilmadi")
        return
    
    (r_id, user_id, session_id, amount, status, paid_by, paid_at, check_photo,
     name, username, _, card_number, card_name) = reward
    
    status_text = {
        'pending': '⏳ Kutilmoqda',
        'paid': '✅ To\'langan',
        'cancelled': '❌ Bekor qilingan'
    }.get(status, status)
    
    text = (
        f"💰 **MUKOFOT MA'LUMOTLARI**\n\n"
        f"🆔 ID: {r_id}\n"
        f"👤 Foydalanuvchi: {name} (@{username if username else 'yoq'})\n"
        f"🆔 User ID: `{user_id}`\n"
        f"💵 Miqdor: {amount} so'm\n"
        f"📊 Holat: {status_text}\n"
    )
    
    if card_number:
        text += f"\n💳 Karta: {card_number}\n"
        text += f"📝 Karta egasi: {card_name}\n"
    
    if status == 'paid' and paid_by:
        db.cursor.execute('SELECT first_name FROM users WHERE user_id = ?', (paid_by,))
        admin_name = db.cursor.fetchone()
        text += f"\n👨‍💼 To'lagan: {admin_name[0] if admin_name else paid_by}\n"
        text += f"📅 To'langan vaqt: {paid_at}\n"
    
    # Inline keyboard
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    
    if status == 'pending':
        keyboard_buttons.append([
            InlineKeyboardButton(text="✅ To'landi", callback_data=f"admin_reward_pay_{r_id}")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_reward_cancel_{r_id}")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="👤 Foydalanuvchi", callback_data=f"admin_user_{user_id}")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_rewards_pending")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith('admin_reward_pay_'))
async def admin_reward_pay(callback: CallbackQuery, state: FSMContext):
    """Mukofotni to'lash"""
    reward_id = int(callback.data.split('_')[3])
    
    await callback.message.edit_text(
        "📤 Chek rasmini yuboring (skrinshot, foto):"
    )
    
    await state.update_data(reward_id=reward_id)
    await state.set_state("waiting_for_reward_check")
    await callback.answer()

# ============================================
# ADMIN - CHEK RASMINI QABUL QILISH
# ============================================

@dp.message(lambda msg: msg.photo)
async def process_reward_check(message: Message, state: FSMContext):
    """Chek rasmini qabul qilish"""
    # State ni tekshirish
    current_state = await state.get_state()
    
    if current_state != "waiting_for_reward_check":
        return  # Bu state uchun mo'ljallanmagan xabar
    
    data = await state.get_data()
    reward_id = data.get('reward_id')
    admin_id = message.from_user.id
    
    if not reward_id:
        await message.answer("❌ Xatolik: Mukofot ID si topilmadi")
        await state.clear()
        return
    
    # Rasm ID sini olish
    photo_id = message.photo[-1].file_id
    
    # Mukofotni to'langan deb belgilash
    success = db.mark_reward_paid(reward_id, admin_id, photo_id)
    
    if success:
        # Foydalanuvchiga xabar yuborish
        db.cursor.execute('SELECT user_id FROM rewards WHERE id = ?', (reward_id,))
        result = db.cursor.fetchone()
        
        if result:
            user_id = result[0]
            try:
                await bot.send_photo(
                    user_id,
                    photo_id,
                    caption=(
                        "✅ **Mukofotingiz to'landi!**\n\n"
                        "💰 200 000 so'm kartangizga tashlandi.\n"
                        "Chek rasmda ko'rsatilgan.\n\n"
                        "Barakalla! Ilmingiz ziyoda bo'lsin! 🤲"
                    )
                )
                await message.answer("✅ Mukofot to'langan deb belgilandi va foydalanuvchiga xabar yuborildi!")
            except Exception as e:
                await message.answer(f"✅ Mukofot to'landi, lekin foydalanuvchiga xabar yuborilmadi: {e}")
        else:
            await message.answer("✅ Mukofot to'langan deb belgilandi, lekin foydalanuvchi topilmadi")
    else:
        await message.answer("❌ Mukofotni to'lashda xatolik yuz berdi")
    
    await state.clear()

@dp.callback_query(F.data.startswith('admin_reward_cancel_'))
async def admin_reward_cancel(callback: CallbackQuery):
    """Mukofotni bekor qilish"""
    reward_id = int(callback.data.split('_')[3])
    
    db.cursor.execute('''
        UPDATE rewards SET status = 'cancelled' WHERE id = ?
    ''', (reward_id,))
    db.conn.commit()
    
    await callback.message.edit_text("❌ Mukofot bekor qilindi")
    await callback.answer()

@dp.callback_query(F.data == "admin_rewards_pending")
async def admin_rewards_pending(callback: CallbackQuery):
    """Kutilayotgan mukofotlar"""
    rewards = db.get_pending_rewards()
    
    if not rewards:
        await callback.message.edit_text("📭 Kutilayotgan mukofotlar yo'q")
        return
    
    await callback.message.edit_text(
        f"⏳ **Kutilayotgan mukofotlar** ({len(rewards)} ta)",
        reply_markup=get_pending_rewards_keyboard(rewards)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith('admin_rewards_page_'))
async def admin_rewards_page(callback: CallbackQuery):
    """Mukofotlar sahifalash"""
    page = int(callback.data.split('_')[3])
    rewards = db.get_pending_rewards()
    await callback.message.edit_reply_markup(
        reply_markup=get_pending_rewards_keyboard(rewards, page)
    )
    await callback.answer()


# ============================================
# FOYDALANUVCHI - KARTA RAQAMINI KIRITISH
# ============================================

# Karta raqamini qabul qilish
@dp.message(RewardState.waiting_for_card)
async def process_card_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    card_number = message.text.strip()
    
    # Foydalanuvchi tilini olish
    lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
    
    # Karta raqamini tekshirish (oddiy validation)
    # Raqamlarni tozalash
    clean_number = re.sub(r'\D', '', card_number)
    
    if len(clean_number) < 16 or len(clean_number) > 16:
        # Noto'g'ri format
        error_messages = {
            'UZ': "❌ **Xato!**\n\nIltimos, 16 xonali karta raqamini to'g'ri kiriting.\nMisol: `8600 1234 5678 9012`",
            'RU': "❌ **Ошибка!**\n\nПожалуйста, введите правильный 16-значный номер карты.\nПример: `8600 1234 5678 9012`",
            'AR': "❌ **خطأ!**\n\nالرجاء إدخال رقم بطاقة صحيح مكون من 16 رقمًا.\nمثال: `8600 1234 5678 9012`",
            'EN': "❌ **Error!**\n\nPlease enter a valid 16-digit card number.\nExample: `8600 1234 5678 9012`"
        }
        await message.answer(error_messages.get(lang, error_messages['UZ']))
        return
    
    # Karta raqamini formatlash (chiroyli ko'rinish uchun)
    formatted_card = ' '.join([clean_number[i:i+4] for i in range(0, 16, 4)])
    
    # Karta ma'lumotlarini vaqtincha saqlash
    await state.update_data(card_number=clean_number, formatted_card=formatted_card)
    
    # Karta egasining ismini so'rash
    name_messages = {
        'UZ': "💳 **Karta egasining to'liq ismini kiriting:**\n\nMisol: `ABDULLAYEV ABDULLA`",
        'RU': "💳 **Введите полное имя владельца карты:**\n\nПример: `ИВАНОВ ИВАН`",
        'AR': "💳 **أدخل الاسم الكامل لصاحب البطاقة:**\n\nمثال: `عبدالله عبدالله`",
        'EN': "💳 **Enter the full name of the card holder:**\n\nExample: `ABDULLAYEV ABDULLA`"
    }
    
    await message.answer(name_messages.get(lang, name_messages['UZ']))
    await state.set_state(RewardState.confirm_card)

# Karta egasining ismini qabul qilish
@dp.message(RewardState.confirm_card)
async def process_card_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    card_name = message.text.strip().upper()
    
    # Foydalanuvchi tilini olish
    lang = user_sessions.get(user_id, {}).get('lang', 'UZ')
    
    # Ismni tekshirish
    if len(card_name) < 5:
        error_messages = {
            'UZ': "❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:",
            'RU': "❌ Имя слишком короткое. Пожалуйста, введите полное имя:",
            'AR': "❌ الاسم قصير جدًا. الرجاء إدخال الاسم الكامل:",
            'EN': "❌ Name is too short. Please enter your full name:"
        }
        await message.answer(error_messages.get(lang, error_messages['UZ']))
        return
    
    # Oldingi ma'lumotlarni olish
    data = await state.get_data()
    card_number = data.get('card_number')
    formatted_card = data.get('formatted_card')
    
    # ===== FOYDALANUVCHIGA CHIROYLI XABAR =====
    success_messages = {
        'UZ': (
            "╔══════════════════════════════════════╗\n"
            "║     ✅ **MUVOFFAQIYATLI!** ✅       ║\n"
            "╠══════════════════════════════════════╣\n"
            "║                                      ║\n"
            "║   📝 **Karta ma'lumotlaringiz**      ║\n"
            "║   💳 Raqam: `{}`  \n"
            "║   👤 Ega: **{}**            \n"
            "║                                      ║\n"
            "║   ✅ **QABUL QILINDI!**              ║\n"
            "║                                      ║\n"
            "║   ⏳ Admin tekshiruvdan so'ng         ║\n"
            "║   💰 mukofotingiz yuboriladi!        ║\n"
            "║                                      ║\n"
            "║   📱 Kartangizdan xabardor bo'lib     ║\n"
            "║      turing!                         ║\n"
            "║                                      ║\n"
            "╚══════════════════════════════════════╝\n"
            "\n"
            "✨ **Barakalla!** ✨\n"
            "🤲 Alloh qabul qilsin!"
        ),
        'RU': (
            "╔══════════════════════════════════════╗\n"
            "║     ✅ **УСПЕШНО!** ✅              ║\n"
            "╠══════════════════════════════════════╣\n"
            "║                                      ║\n"
            "║   📝 **Данные вашей карты**          ║\n"
            "║   💳 Номер: `{}`          \n"
            "║   👤 Владелец: **{}**        \n"
            "║                                      ║\n"
            "║   ✅ **ПРИНЯТО!**                     ║\n"
            "║                                      ║\n"
            "║   ⏳ После проверки админом           ║\n"
            "║   💰 приз будет отправлен!           ║\n"
            "║                                      ║\n"
            "║   📱 Следите за своей картой!        ║\n"
            "║                                      ║\n"
            "╚══════════════════════════════════════╝\n"
            "\n"
            "✨ **Баракялла!** ✨\n"
            "🤲 Да примет Аллах!"
        ),
        'AR': (
            "╔══════════════════════════════════════╗\n"
            "║     ✅ **تم بنجاح!** ✅              ║\n"
            "╠══════════════════════════════════════╣\n"
            "║                                      ║\n"
            "║   📝 **بيانات بطاقتك**                ║\n"
            "║   💳 الرقم: `{}`          \n"
            "║   👤 المالك: **{}**          \n"
            "║                                      ║\n"
            "║   ✅ **تم الاستلام!**                  ║\n"
            "║                                      ║\n"
            "║   ⏳ بعد التحقق من قبل المشرف          ║\n"
            "║   💰 سيتم إرسال الجائزة!              ║\n"
            "║                                      ║\n"
            "║   📱 ترقبوا بطاقتكم!                  ║\n"
            "║                                      ║\n"
            "╚══════════════════════════════════════╝\n"
            "\n"
            "✨ **بارك الله فيك!** ✨\n"
            "🤲 تقبل الله!"
        ),
        'EN': (
            "╔══════════════════════════════════════╗\n"
            "║     ✅ **SUCCESSFUL!** ✅            ║\n"
            "╠══════════════════════════════════════╣\n"
            "║                                      ║\n"
            "║   📝 **Your card information**       ║\n"
            "║   💳 Number: `{}`          \n"
            "║   👤 Holder: **{}**          \n"
            "║                                      ║\n"
            "║   ✅ **RECEIVED!**                    ║\n"
            "║                                      ║\n"
            "║   ⏳ After admin verification         ║\n"
            "║   💰 your prize will be sent!        ║\n"
            "║                                      ║\n"
            "║   📱 Keep an eye on your card!       ║\n"
            "║                                      ║\n"
            "╚══════════════════════════════════════╝\n"
            "\n"
            "✨ **Barakallah!** ✨\n"
            "🤲 May Allah accept!"
        )
    }
    
    await message.answer(success_messages.get(lang, success_messages['UZ']).format(formatted_card, card_name))
    
    # ===== KONFETTI VA TABRIKLAR =====
    confetti = ["🎊", "✨", "🎉", "⭐", "💫", "🌟"]
    confetti_line = ""
    for i in range(10):
        confetti_line += confetti[i % len(confetti)] + " "
    
    await message.answer(f"**{confetti_line}**")
    await asyncio.sleep(0.5)
    
    # ===== ADMINGA XABAR YUBORISH =====
    user_info = user_sessions[user_id].get('name', 'Noma\'lum')
    username = message.from_user.username or "Yo'q"
    
    admin_message = (
        "╔══════════════════════════════════════╗\n"
        "║     💰 **YANGI MUKOFOT SO'ROVI** 💰  ║\n"
        "╠══════════════════════════════════════╣\n"
        "║                                      ║\n"
        f"║   👤 **Foydalanuvchi:**             ║\n"
        f"║      {user_info}                    ║\n"
        f"║   🆔 **ID:** `{user_id}`            ║\n"
        f"║   🌐 **Username:** @{username}      ║\n"
        f"║   💳 **Karta:** `{formatted_card}`  ║\n"
        f"║   👤 **Ega:** {card_name}           ║\n"
        f"║   🌍 **Til:** {lang}                ║\n"
        "║                                      ║\n"
        "║   ⏳ **Holat:** Kutilmoqda           ║\n"
        "║                                      ║\n"
        "╚══════════════════════════════════════╝\n"
        "\n"
        "🔍 **Tekshirish uchun:** /check_rewards"
    )
    
    # Barcha adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_message)
            # Adminlarga ham konfetti
            await asyncio.sleep(0.2)
            await bot.send_message(admin_id, f"**{confetti_line}**")
        except Exception as e:
            print(f"Admin {admin_id} ga xabar yuborilmadi: {e}")
    
    # ===== FOYDALANUVCHIGA YAKUNIY XABAR =====
    final_messages = {
        'UZ': (
            "🎯 **Ma'lumotlaringiz adminga yuborildi!**\n\n"
            "📋 **Keyingi qadamlar:**\n"
            "1. ✅ Admin ma'lumotlaringizni tekshiradi\n"
            "2. ⏳ 1-24 soat ichida mukofotingiz yuboriladi\n"
            "3. 💳 Kartangizni kuzatib turing\n"
            "4. 📞 Savollar bo'lsa, admin bilan bog'lanishingiz mumkin\n\n"
            "🤲 **Barakalla!**"
        ),
        'RU': (
            "🎯 **Ваши данные отправлены админу!**\n\n"
            "📋 **Следующие шаги:**\n"
            "1. ✅ Админ проверит ваши данные\n"
            "2. ⏳ В течение 1-24 часов приз будет отправлен\n"
            "3. 💳 Следите за своей картой\n"
            "4. 📞 Если есть вопросы, свяжитесь с админом\n\n"
            "🤲 **Баракялла!**"
        ),
        'AR': (
            "🎯 **تم إرسال بياناتك إلى المشرف!**\n\n"
            "📋 **الخطوات التالية:**\n"
            "1. ✅ سيتحقق المشرف من بياناتك\n"
            "2. ⏳ سيتم إرسال الجائزة خلال 1-24 ساعة\n"
            "3. 💳 ترقبوا بطاقتكم\n"
            "4. 📞 إذا كان لديك أسئلة، اتصل بالمشرف\n\n"
            "🤲 **بارك الله فيك!**"
        ),
        'EN': (
            "🎯 **Your information has been sent to admin!**\n\n"
            "📋 **Next steps:**\n"
            "1. ✅ Admin will verify your information\n"
            "2. ⏳ Within 1-24 hours the prize will be sent\n"
            "3. 💳 Keep an eye on your card\n"
            "4. 📞 If you have questions, contact admin\n\n"
            "🤲 **Barakallah!**"
        )
    }
    
    await message.answer(final_messages.get(lang, final_messages['UZ']))
    
    # ===== ASOSIY MENYUGA QAYTISH =====
    await message.answer(
        "📌 **Asosiy menyu:**" if lang == 'UZ' else 
        "📌 **Главное меню:**" if lang == 'RU' else
        "📌 **القائمة الرئيسية:**" if lang == 'AR' else
        "📌 **Main menu:**",
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    # State ni tozalash
    await state.clear()
    
    # Karta ma'lumotlarini bazaga saqlash (agar kerak bo'lsa)
    db.save_card_info(user_id, card_number, card_name)


# ============================================
# UMUMIY YORDAMCHI FUNKSIYALAR
# ============================================

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Admin panelga qaytish"""
    await callback.message.delete()
    await callback.message.answer(
        "👋 Admin panel:",
        reply_markup=get_admin_keyboard('UZ')
    )
    await callback.answer()    

# Shutdown handler
async def on_shutdown():
    logger.info("Bot shutting down...")
    await bot.session.close()
    db.close()
# Webhook handler
async def handle_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
# ... (yuqoridagi barcha importlar va kodlar o'zgarishsiz qoladi) ...

# ============================================
# POLLING UCHUN KOD (WEBHOOK EMAS)
# ============================================

# Startup notification
async def on_startup():
    logger.info("Bot started successfully!")
    logger.info(f"Admin IDs: {ADMIN_IDS}")
    
    try:
        me = await bot.get_me()
        logger.info(f"Bot connected: @{me.username}")
    except Exception as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        return
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "✅ Bot ishga tushdi!\n\n"
                "Bot muvaffaqiyatli ishga tushirildi.\n"
                "Barcha tillarga avtomatik tarjima tizimi faol."
            )
        except:
            pass
    
    print("\n" + "="*50)
    print("🤖 ISLOMIY SAVOL-JAVOB BOTI")
    print("="*50)
    print("✅ Bot ishga tushdi!")
    print(f"👤 Adminlar: {ADMIN_IDS}")
    print(f"📊 Jami foydalanuvchilar: {db.get_total_users()}")
    print("🌐 Avtomatik tarjima tizimi faol")
    print("="*50 + "\n")

# Shutdown handler
async def on_shutdown():
    logger.info("Bot shutting down...")
    await bot.session.close()
    db.close()

# Main function - POLLING
async def main():
    keep_alive()
    
    # Webhook ni o'chirish (ishonch hosil qilish uchun)
    await bot.delete_webhook()
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # POLLING ishlatish
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")