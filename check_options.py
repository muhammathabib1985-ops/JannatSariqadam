import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

print("=" * 70)
print("🔍 VARIANTLARNI TEKSHIRISH")
print("=" * 70)

# Barcha savollarni olish
cursor.execute('''
    SELECT id, 
           question_uz, question_ar,
           option1_uz, option1_ar,
           option2_uz, option2_ar,
           option3_uz, option3_ar
    FROM questions
    WHERE is_active = 1
''')

questions = cursor.fetchall()

for q in questions:
    print(f"\n📝 ID: {q[0]}")
    print(f"   Savol (UZ): {q[1][:50]}...")
    print(f"   Savol (AR): {q[2][:50]}...")
    print(f"   1-variant (UZ): {q[3]}")
    print(f"   1-variant (AR): {q[4]}")
    print(f"   2-variant (UZ): {q[5]}")
    print(f"   2-variant (AR): {q[6]}")
    print(f"   3-variant (UZ): {q[7]}")
    print(f"   3-variant (AR): {q[8]}")
    
    # Arab variantlari mavjudligini tekshirish
    if not q[4] or q[4] == q[3]:
        print("   ⚠️ Arab varianti yo'q yoki o'zbekcha bilan bir xil!")

print("=" * 70)
conn.close()