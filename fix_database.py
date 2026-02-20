import sqlite3
import os

print("=" * 50)
print("🔧 ISLOMIY BOT - BAZA TUZATISH SKRIPTI")
print("=" * 50)

# Bazaning joylashuvini tekshirish
db_path = 'bot_database.db'
if not os.path.exists(db_path):
    print(f"❌ Baza fayli topilmadi: {db_path}")
    print("✅ Yangi baza yaratiladi...")
else:
    print(f"✅ Baza fayli topildi: {db_path}")
    # Baza hajmini ko'rsatish
    size = os.path.getsize(db_path)
    print(f"📊 Baza hajmi: {size} bayt")

# Bazaga ulanish
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("✅ Bazaga ulanish muvaffaqiyatli!")
except Exception as e:
    print(f"❌ Bazaga ulanishda xatolik: {e}")
    exit(1)

try:
    # 1. MAVJUD JADVALLARNI TEKSHIRISH
    print("\n📋 MAVJUD JADVALLAR:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    
    # 2. questions JADVALINI TEKSHIRISH
    print("\n🔍 questions JADVALI TEKSHIRILMOQDA...")
    cursor.execute("PRAGMA table_info(questions)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"📊 Mavjud ustunlar: {', '.join(column_names)}")
    
    # 3. is_active USTUNI BOR-YO'QLIGINI TEKSHIRISH
    if 'is_active' not in column_names:
        print("➕ 'is_active' ustuni qo'shilmoqda...")
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN is_active INTEGER DEFAULT 1;")
            conn.commit()
            print("✅ 'is_active' ustuni muvaffaqiyatli qo'shildi!")
        except Exception as e:
            print(f"❌ Ustun qo'shishda xatolik: {e}")
    else:
        print("✅ 'is_active' ustuni allaqachon mavjud")
    
    # 4. BARCHA SAVOLLARNI FAOLLASHTIRISH
    print("\n🔄 Barcha savollar faollashtirilmoqda...")
    cursor.execute("UPDATE questions SET is_active = 1;")
    conn.commit()
    print(f"✅ {cursor.rowcount} ta savol faollashtirildi!")
    
    # 5. SAVOLLARNI KO'RISH
    print("\n📝 BAZADAGI SAVOLLAR:")
    cursor.execute("SELECT id, question_uz, is_active FROM questions;")
    questions = cursor.fetchall()
    
    if questions:
        for q in questions:
            status = "✅ FAOL" if q[2] == 1 else "❌ FAOL EMAS"
            print(f"   ID: {q[0]}, Savol: {q[1][:50]}... {status}")
    else:
        print("   Bazada hali savollar yo'q")
    
    # 6. STATISTIKA
    print("\n📊 BAZA STATISTIKASI:")
    cursor.execute("SELECT COUNT(*) FROM questions;")
    total = cursor.fetchone()[0]
    print(f"   Jami savollar: {total}")
    
    cursor.execute("SELECT COUNT(*) FROM questions WHERE is_active = 1;")
    active = cursor.fetchone()[0]
    print(f"   Faol savollar: {active}")
    
    cursor.execute("SELECT COUNT(*) FROM users;")
    users = cursor.fetchone()[0]
    print(f"   Foydalanuvchilar: {users}")
    
    cursor.execute("SELECT COUNT(*) FROM prophets;")
    prophets = cursor.fetchone()[0]
    print(f"   Payg'ambarlar: {prophets}")
    
    print("\n" + "=" * 50)
    print("✅ BAZA MUVAFFAQIYATLI TUZATILDI!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ XATOLIK: {e}")
    import traceback
    traceback.print_exc()

finally:
    conn.close()
    print("\n🔌 Baza ulanishi yopildi")
    
input("\nTugatish uchun ENTER tugmasini bosing...")