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

# MUHIM: Barcha admin handlerlari uchun maxsus filter
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
    elif text == "🔙 Chiqish":
        await admin_exit(message)
    # Boshqa xabarlar - e'tiborsiz qoldirish

# SAVOL QO'SHISH
async def add_question_start(message: Message, state: FSMContext):
    await message.answer(
        "📝 Yangi savol qo'shish\n\n"
        "Savol matnini O'ZBEK tilida kiriting:"
    )
    await state.set_state(AddQuestion.waiting_for_question_uz)

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

@router.callback_query(F.data == "admin_confirm_save")
async def confirm_save(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz!")
        return
    
    await callback.message.edit_text("⏳ Tarjima qilinmoqda...")
    
    data = await state.get_data()
    
    try:
        # Tarjima qilish
        question_ru = (await translator.translate(data['question_uz'], dest='ru')).text
        question_ar = (await translator.translate(data['question_uz'], dest='ar')).text
        question_en = (await translator.translate(data['question_uz'], dest='en')).text
        
        option1_ru = (await translator.translate(data['option1_uz'], dest='ru')).text
        option1_ar = (await translator.translate(data['option1_uz'], dest='ar')).text
        option1_en = (await translator.translate(data['option1_uz'], dest='en')).text
        
        option2_ru = (await translator.translate(data['option2_uz'], dest='ru')).text
        option2_ar = (await translator.translate(data['option2_uz'], dest='ar')).text
        option2_en = (await translator.translate(data['option2_uz'], dest='en')).text
        
        option3_ru = (await translator.translate(data['option3_uz'], dest='ru')).text
        option3_ar = (await translator.translate(data['option3_uz'], dest='ar')).text
        option3_en = (await translator.translate(data['option3_uz'], dest='en')).text
        
        # Database ga saqlash
        question_data = (
            data['question_uz'], question_ru, question_ar, question_en,
            data['option1_uz'], option1_ru, option1_ar, option1_en,
            data['option2_uz'], option2_ru, option2_ar, option2_en,
            data['option3_uz'], option3_ru, option3_ar, option3_en,
            data['correct'], datetime.now(), callback.from_user.id
        )
        
        question_id = db.add_question(question_data)
        
        if question_id:
            await callback.message.edit_text(f"✅ Savol muvaffaqiyatli qo'shildi! (ID: {question_id})")
            # Admin menyusiga qaytish
            await callback.message.answer(
                "Admin panel:",
                reply_markup=get_admin_keyboard('UZ')
            )
        else:
            await callback.message.edit_text("❌ Saqlashda xatolik yuz berdi!")
        
    except Exception as e:
        logger.error(f"Error saving question: {e}")
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