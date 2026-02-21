import sqlite3
import os

print("=" * 60)
print("🧹 BAZANI TOZALASH")
print("=" * 60)

# Bazaga ulanish
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# 1. Barcha jadvallardagi ma'lumotlarni o'chirish
print("\n📊 Jadvallar tozalanmoqda...")

# O'chirish ketma-ketligi (foreign key lar uchun)
tables_to_clear = [
    'user_question_sessions',
    'rewards',
    'user_cards',
    'user_20_questions',
    'user_answers',
    'user_stats',
    'questions',
    'prophets',
    'allah_names',
    'hadith'
]

for table in tables_to_clear:
    try:
        cursor.execute(f'DELETE FROM {table}')
        print(f"   ✅ {table} tozalandi ({cursor.rowcount} ta yozuv)")
    except Exception as e:
        print(f"   ⚠️ {table} tozalanmadi: {e}")

# 2. ID larni qayta boshlash (AUTOINCREMENT ni reset qilish)
print("\n🔄 ID larni qayta boshlash...")
try:
    cursor.execute("DELETE FROM sqlite_sequence")
    print("   ✅ ID lar qayta boshlandi")
except Exception as e:
    print(f"   ⚠️ {e}")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("✅ BAZA MUVOFFAQIYATLI TOZALANDI!")
print("=" * 60)
print("\n📌 Endi yangi savollarni qo'shishingiz mumkin:")
print("   1. Alloh ismlari: python add_allah_names.py")
print("   2. Admin panel orqali savollar qo'shish")
print("=" * 60)

input("\nTugatish uchun ENTER bosing...")