# fix_translations.py
import sqlite3
from googletrans import Translator
import time

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
translator = Translator()

# Barcha savollarni olish
cursor.execute('SELECT id, question_uz FROM questions WHERE is_active = 1')
questions = cursor.fetchall()

print(f"{len(questions)} ta savol tekshirilmoqda...")

for q in questions:
    q_id, q_uz = q
    
    print(f"\n📝 ID: {q_id}")
    print(f"   O'zbek: {q_uz}")
    
    # Rus tiliga tarjima
    q_ru = translator.translate(q_uz, dest='ru').text
    print(f"   Rus: {q_ru}")
    
    # Arab tiliga tarjima
    q_ar = translator.translate(q_uz, dest='ar').text
    print(f"   Arab: {q_ar}")
    
    # Ingliz tiliga tarjima
    q_en = translator.translate(q_uz, dest='en').text
    print(f"   Ingliz: {q_en}")
    
    # Bazaga yangilash
    cursor.execute('''
        UPDATE questions 
        SET question_ru=?, question_ar=?, question_en=?
        WHERE id=?
    ''', (q_ru, q_ar, q_en, q_id))
    
    conn.commit()
    time.sleep(0.5)  # Tarjimalar orasida kutish

conn.close()
print("\n✅ Barcha tarjimalar yangilandi!")