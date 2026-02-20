import sqlite3
from googletrans import Translator

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
translator = Translator()

print("=" * 70)
print("🔧 ARAB VARIANTLARINI TUZATISH")
print("=" * 70)

# Arab variantlari yo'q yoki noto'g'ri bo'lgan savollarni topish
cursor.execute('''
    SELECT id, 
           option1_uz, option1_ar,
           option2_uz, option2_ar,
           option3_uz, option3_ar
    FROM questions
    WHERE option1_ar IS NULL OR option1_ar = '' OR option1_ar = option1_uz
''')

questions = cursor.fetchall()

for q in questions:
    q_id = q[0]
    opt1_uz = q[1]
    opt2_uz = q[3]
    opt3_uz = q[5]
    
    print(f"\n📝 ID: {q_id} tuzatilmoqda...")
    
    try:
        # Arab tiliga tarjima qilish
        opt1_ar = translator.translate(opt1_uz, dest='ar').text
        opt2_ar = translator.translate(opt2_uz, dest='ar').text
        opt3_ar = translator.translate(opt3_uz, dest='ar').text
        
        print(f"   1: {opt1_uz} -> {opt1_ar}")
        print(f"   2: {opt2_uz} -> {opt2_ar}")
        print(f"   3: {opt3_uz} -> {opt3_ar}")
        
        # Yangilash
        cursor.execute('''
            UPDATE questions 
            SET option1_ar = ?, option2_ar = ?, option3_ar = ?
            WHERE id = ?
        ''', (opt1_ar, opt2_ar, opt3_ar, q_id))
        conn.commit()
        
        print("   ✅ Tuzatildi!")
        
    except Exception as e:
        print(f"   ❌ Xatolik: {e}")

print("\n" + "=" * 70)
print("✅ Tuzatish tugadi!")
print("=" * 70)

conn.close()