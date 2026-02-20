import sqlite3
from googletrans import Translator

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
translator = Translator()

print("=" * 60)
print("🔧 ARAB TILIDAGI SAVOLLARNI TUZATISH")
print("=" * 60)

# Arab tilidagi ustunlari o'zbekcha bo'lgan savollarni topish
cursor.execute('''
    SELECT id, question_uz, question_ar, question_ru, question_en
    FROM questions
    WHERE question_ar IS NOT NULL AND question_ar != ''
''')

questions = cursor.fetchall()

for q in questions:
    q_id, q_uz, q_ar, q_ru, q_en = q
    
    # Agar arabcha matn o'zbekcha bo'lsa (lotin yoki kirill harflari bo'lsa)
    if q_ar and any(c.isalpha() and c.isascii() for c in q_ar[:10]):
        print(f"\n📝 ID: {q_id}")
        print(f"   O'zbek: {q_uz[:50]}...")
        print(f"   Arab (noto'g'ri): {q_ar[:50]}...")
        
        # Arab tiliga tarjima qilish
        try:
            translated = translator.translate(q_uz, dest='ar')
            if hasattr(translated, 'text'):
                correct_ar = translated.text
                print(f"   Arab (to'g'ri): {correct_ar[:50]}...")
                
                # Yangilash
                cursor.execute('''
                    UPDATE questions 
                    SET question_ar = ? 
                    WHERE id = ?
                ''', (correct_ar, q_id))
                conn.commit()
                print("   ✅ Tuzatildi!")
        except Exception as e:
            print(f"   ❌ Xatolik: {e}")

print("\n" + "=" * 60)
print("✅ Tuzatish tugadi!")
print("=" * 60)

conn.close()