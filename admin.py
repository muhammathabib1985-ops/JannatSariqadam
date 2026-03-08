from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import get_admin_keyboard, get_main_menu_keyboard
import logging
from googletrans import Translator
from datetime import datetime

logger = logging.getLogger(__name__)
router = Router()
db = Database()
translator = Translator()

# Admin ID larni saqlash uchun global o'zgaruvchi
admin_ids = []

def set_admin_ids(ids):
    """Admin ID larni o'rnatish"""
    global admin_ids
    admin_ids = ids
    logger.info(f"Admin IDs set: {admin_ids}")

# Admin check
def is_admin(user_id: int) -> bool:
    return user_id in admin_ids

# States
class AddQuestion(StatesGroup):
    waiting_for_question_uz = State()
    waiting_for_options_uz = State()
    waiting_for_correct = State()
    waiting_for_confirmation = State()

class AddProphet(StatesGroup):
    waiting_for_name_uz = State()
    waiting_for_audio = State()
    
class AddPromoVideo(StatesGroup):
    waiting_for_video = State()
    waiting_for_caption = State()

# ============================================
# REKLAMA VIDEO QO'SHISH HANDLERLARI
# ============================================

@router.message(lambda msg: msg.text == "🎬 Reklama video qo'shish" and is_admin(msg.from_user.id))
async def add_promo_start(message: Message, state: FSMContext):
    """Reklama video qo'shishni boshlash"""
    print(f"🔴🔴🔴 Reklama video qo'shish tugmasi bosildi! Admin: {message.from_user.id}")
    await message.answer(
        "📹 **Yangi reklama videosi qo'shish**\n\n"
        "Video faylni yuboring (MP4 formatida):"
    )
    await state.set_state(AddPromoVideo.waiting_for_video)

@router.message(AddPromoVideo.waiting_for_video, F.video)
async def process_promo_video(message: Message, state: FSMContext):
    """Video qabul qilish"""
    video_id = message.video.file_id
    await state.update_data(video_id=video_id)
    
    await message.answer(
        "✅ Video qabul qilindi!\n\n"
        "Endi video uchun sarlavha (caption) kiriting (ixtiyoriy):\n"
        "Masalan: `Bizning kanalimizga obuna bo'ling!`\n\n"
        "Yoki /skip ni bosing"
    )
    await state.set_state(AddPromoVideo.waiting_for_caption)

@router.message(AddPromoVideo.waiting_for_caption)
async def process_promo_caption(message: Message, state: FSMContext):
    """Caption qabul qilish va saqlash"""
    caption = message.text if message.text != "/skip" else ""
    
    data = await state.get_data()
    video_id = data.get('video_id')
    
    # Bazaga saqlash
    promo_id = db.add_promo_video(video_id, caption, message.from_user.id)
    
    if promo_id:
        await message.answer(
            f"✅ **Reklama video muvaffaqiyatli qo'shildi!** (ID: {promo_id})\n\n"
            f"📹 Video ID: `{video_id}`\n"
            f"📝 Caption: {caption if caption else 'Yo\\'q'}\n\n"
            f"Yangi foydalanuvchilar salovotlardan keyin ushbu videoni ko'rishadi."
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!")
    
    await state.clear()

@router.message(AddPromoVideo.waiting_for_video)
async def process_promo_video_error(message: Message, state: FSMContext):
    """Video emas boshqa narsa yuborilsa"""
    await message.answer(
        "❌ **Xato!** Iltimos, video fayl yuboring (MP4 formatida).\n\n"
        "📹 Video yuborish uchun: 📎 → Video → MP4 fayl tanlang"
    )

@router.message(Command("skip"))
async def skip_caption(message: Message, state: FSMContext):
    """Caption ni skip qilish"""
    current_state = await state.get_state()
    if current_state == AddPromoVideo.waiting_for_caption.state:
        await process_promo_caption(message, state)

# ============================================
# REKLAMA STATISTIKASI HANDLERLARI
# ============================================

@router.message(lambda msg: msg.text == "📊 Reklama statistikasi" and is_admin(msg.from_user.id))
async def show_promo_stats(message: Message):
    """Reklama statistikasini ko'rsatish"""
    stats = db.get_promo_stats()
    
    if not stats:
        await message.answer("📭 Reklama statistikasi topilmadi")
        return
    
    # Matnni tayyorlash
    text = "📊 **REKLAMA STATISTIKASI** 📊\n\n"
    
    if stats['active_video']:
        video_id, file_id, caption, created_at = stats['active_video']
        text += f"🎬 **Faol video:**\n"
        text += f"   🆔 ID: {video_id}\n"
        text += f"   📅 Qo'shilgan: {created_at[:16] if created_at else 'Noma\\'lum'}\n"
        text += f"   📝 Caption: {caption if caption else 'Yo\\'q'}\n\n"
    else:
        text += "🎬 **Faol video yo'q**\n\n"
    
    text += f"👁️ **Jami ko'rishlar:** {stats['total_views']}\n"
    text += f"👥 **Unikal foydalanuvchilar:** {stats['unique_users']}\n"
    text += f"📊 **Barcha vaqtlardagi ko'rishlar:** {stats['all_time_views']}\n"
    text += f"👤 **Barcha vaqtlardagi foydalanuvchilar:** {stats['all_time_users']}\n\n"
    
    if stats['recent_views']:
        text += "🕒 **Oxirgi ko'rishlar:**\n"
        for i, (name, username, viewed_at) in enumerate(stats['recent_views'][:5], 1):
            username_text = f"@{username}" if username else "no username"
            time_str = viewed_at[:16] if viewed_at else "Noma'lum"
            text += f"{i}. 👤 {name} ({username_text}) - {time_str}\n"
    
    await message.answer(text)

# ============================================
# ADMIN PANEL ASOSIY HANDLERLARI
# ============================================

@router.message(lambda message: message.from_user.id in admin_ids)
async def admin_message_handler(message: Message, state: FSMContext):
    """Barcha admin xabarlarini ushlab, tegishli funksiyaga yo'naltiradi"""
    user_id = message.from_user.id
    text = message.text
    
    # Current state ni tekshirish
    current_state = await state.get_state()
    
    # Agar state bo'lsa - FSM jarayonida
    if current_state:
        return  # FSM handlerlar ishlaydi
    
    # State yo'q - menyu tugmalarini tekshirish
    if text == "➕ Savol qo'shish":
        await add_question_start(message, state)
    elif text == "👤 Payg'ambar qo'shish":
        await add_prophet_start(message, state)
    elif text == "📊 Statistika":
        await show_stats(message)
    elif text == "🎬 Reklama video qo'shish":
        await add_promo_start(message, state)
    elif text == "📊 Reklama statistikasi":
        await show_promo_stats(message)
    elif text == "🔙 Chiqish":
        await admin_exit(message)

# ============================================
# SAVOL QO'SHISH FUNKSIYALARI
# ============================================

async def add_question_start(message: Message, state: FSMContext):
    """Savol qo'shishni boshlash"""
    await message.answer(
        "📝 Yangi savol qo'shish\n\n"
        "Savol matnini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddQuestion.waiting_for_question_uz)

@router.message(AddQuestion.waiting_for_question_uz)
async def process_question_uz(message: Message, state: FSMContext):
    """Savol matnini qabul qilish"""
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

# ============================================
# STATISTIKA FUNKSIYASI
# ============================================

async def show_stats(message: Message):
    """Statistika ko'rsatish"""
    try:
        total_users = db.get_total_users()
        today_users = db.get_today_users()
        total_questions = db.get_question_count()
        
        db.cursor.execute('SELECT COUNT(*) FROM prophets')
        total_prophets = db.cursor.fetchone()[0]
        
        stats_text = (
            f"📊 BOT STATISTIKASI\n\n"
            f"👥 Jami foydalanuvchilar: {total_users}\n"
            f"📅 Bugun qo'shilganlar: {today_users}\n"
            f"❓ Jami savollar: {total_questions}\n"
            f"👤 Payg'ambarlar: {total_prophets}\n"
        )
        
        await message.answer(stats_text, reply_markup=get_admin_keyboard('UZ'))
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer(f"❌ Xatolik: {e}")

# ============================================
# PAYG'AMBAR QO'SHISH FUNKSIYALARI
# ============================================

async def add_prophet_start(message: Message, state: FSMContext):
    """Payg'ambar qo'shishni boshlash"""
    await message.answer(
        "👤 Yangi payg'ambar qo'shish\n\n"
        "Payg'ambar nomini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddProphet.waiting_for_name_uz)

# ============================================
# CHIQISH FUNKSIYASI
# ============================================

async def admin_exit(message: Message):
    """Admin panelidan chiqish"""
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu_keyboard('UZ')
    )

@router.message(AddQuestion.waiting_for_question_uz)
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

@router.message(AddQuestion.waiting_for_options_uz)
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

@router.message(AddQuestion.waiting_for_correct)
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
        
        # Tarjima qilish (sinxron)
        from googletrans import Translator
        translator = Translator()
        
        # Rus tiliga tarjima
        question_ru = translator.translate(question_uz, dest='ru').text
        option1_ru = translator.translate(option1_uz, dest='ru').text
        option2_ru = translator.translate(option2_uz, dest='ru').text
        option3_ru = translator.translate(option3_uz, dest='ru').text
        
        # Arab tiliga tarjima
        question_ar = translator.translate(question_uz, dest='ar').text
        option1_ar = translator.translate(option1_uz, dest='ar').text
        option2_ar = translator.translate(option2_uz, dest='ar').text
        option3_ar = translator.translate(option3_uz, dest='ar').text
        
        # Ingliz tiliga tarjima
        question_en = translator.translate(question_uz, dest='en').text
        option1_en = translator.translate(option1_uz, dest='en').text
        option2_en = translator.translate(option2_uz, dest='en').text
        option3_en = translator.translate(option3_uz, dest='en').text
        
        # TARJIMA NATIJALARINI TEKSHIRISH
        print(f"🇸🇦 Arabcha tarjima: {question_ar}")
        print(f"🇷🇺 Ruscha tarjima: {question_ru}")
        print(f"🇬🇧 Inglizcha tarjima: {question_en}")
        
        # Database ga saqlash
        from database import Database
        db = Database()
        
        question_data = (
            question_uz, question_ru, question_ar, question_en,
            option1_uz, option1_ru, option1_ar, option1_en,
            option2_uz, option2_ru, option2_ar, option2_en,
            option3_uz, option3_ru, option3_ar, option3_en,
            data['correct'], datetime.now(), callback.from_user.id
        )
        
        print("✅ Ma'lumotlar bazaga saqlanmoqda...")
        
        # add_question metodini chaqirish
        cursor = db.conn.cursor()
        query = '''
            INSERT INTO questions (
                question_uz, question_ru, question_ar, question_en,
                option1_uz, option1_ru, option1_ar, option1_en,
                option2_uz, option2_ru, option2_ar, option2_en,
                option3_uz, option3_ru, option3_ar, option3_en,
                correct_option, created_at, created_by, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        '''
        cursor.execute(query, question_data)
        db.conn.commit()
        question_id = cursor.lastrowid
        
        if question_id:
            # Tarjimalarni ko'rsatish
            preview = (
                f"✅ Savol muvaffaqiyatli qo'shildi! (ID: {question_id})\n\n"
                f"🇺🇿 O'zbek: {question_uz}\n"
                f"🇷🇺 Rus: {question_ru}\n"
                f"🇸🇦 Arab: {question_ar}\n"
                f"🇬🇧 Ingliz: {question_en}\n\n"
                f"1️⃣ {option1_uz} | {option1_ru} | {option1_ar} | {option1_en}\n"
                f"2️⃣ {option2_uz} | {option2_ru} | {option2_ar} | {option2_en}\n"
                f"3️⃣ {option3_uz} | {option3_ru} | {option3_ar} | {option3_en}\n"
            )
            
            await callback.message.edit_text(preview)
        else:
            await callback.message.edit_text("❌ Saqlashda xatolik yuz berdi!")
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(f"❌ Xatolik: {str(e)}")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_cancel_save")
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

# STATISTIKA
async def show_stats(message: Message):
    try:
        total_users = db.get_total_users()
        today_users = db.get_today_users()
        total_questions = db.get_question_count()
        
        db.cursor.execute('SELECT COUNT(*) FROM prophets')
        total_prophets = db.cursor.fetchone()[0]
        
        stats_text = (
            f"📊 BOT STATISTIKASI\n\n"
            f"👥 Jami foydalanuvchilar: {total_users}\n"
            f"📅 Bugun qo'shilganlar: {today_users}\n"
            f"❓ Jami savollar: {total_questions}\n"
            f"👤 Payg'ambarlar: {total_prophets}\n"
        )
        
        await message.answer(stats_text, reply_markup=get_admin_keyboard('UZ'))
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer(f"❌ Xatolik: {e}")

# PAYG'AMBAR QO'SHISH
async def add_prophet_start(message: Message, state: FSMContext):
    await message.answer(
        "👤 Yangi payg'ambar qo'shish\n\n"
        "Payg'ambar nomini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddProphet.waiting_for_name_uz)

@router.message(AddProphet.waiting_for_name_uz)
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

@router.message(AddProphet.waiting_for_audio)
async def process_prophet_audio(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    if not message.audio:
        await message.answer("❌ Iltimos, audio fayl yuboring!")
        return
    
    data = await state.get_data()
    
    try:
        # Tarjima qilish
        name_ru = (await translator.translate(data['name_uz'], dest='ru')).text
        name_ar = (await translator.translate(data['name_uz'], dest='ar')).text
        name_en = (await translator.translate(data['name_uz'], dest='en')).text
        
        # Database ga saqlash
        db.add_prophet(data['name_uz'], name_ru, name_ar, name_en, message.audio.file_id)
        
        await message.answer(f"✅ Payg'ambar muvaffaqiyatli qo'shildi!")
        await message.answer(
            "Admin panel:",
            reply_markup=get_admin_keyboard('UZ')
        )
        
    except Exception as e:
        logger.error(f"Error adding prophet: {e}")
        await message.answer(f"❌ Xatolik: {e}")
    
    await state.clear()

# CHIQISH
async def admin_exit(message: Message):
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu_keyboard('UZ')
    )