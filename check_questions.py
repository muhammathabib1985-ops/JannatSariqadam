import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

print("=" * 70)
print("🔍 BAZADAGI SAVOLLAR (barcha tillar)")
print("=" * 70)

# Barcha savollarni olish
cursor.execute('''
    SELECT id, 
           question_uz, question_ru, question_ar, question_en,
           option1_uz, option1_ru, option1_ar, option1_en,
           is_active 
    FROM questions
''')

questions = cursor.fetchall()

if questions:
    for q in questions:
        print(f"\n📝 ID: {q[0]} | Faol: {'✅' if q[9] else '❌'}")
        print(f"   🇺🇿 O'zbek: {q[1][:50]}..." if q[1] else "   🇺🇿 O'zbek: (yo'q)")
        print(f"   🇷🇺 Rus:   {q[2][:50]}..." if q[2] else "   🇷🇺 Rus: (yo'q)")
        print(f"   🇸🇦 Arab:  {q[3][:50]}..." if q[3] else "   🇸🇦 Arab: (yo'q)")
        print(f"   🇬🇧 Ingliz: {q[4][:50]}..." if q[4] else "   🇬🇧 Ingliz: (yo'q)")
        
        # Variantlarni tekshirish
        if q[5]: print(f"   1️⃣ O'zbek: {q[5]}")
        if q[6]: print(f"   1️⃣ Rus:   {q[6]}")
        if q[7]: print(f"   1️⃣ Arab:  {q[7]}")
        if q[8]: print(f"   1️⃣ Ingliz: {q[8]}")
else:
    print("❌ Bazada savollar yo'q")

print("=" * 70)
conn.close()

input("\nTugatish uchun ENTER bosing...")