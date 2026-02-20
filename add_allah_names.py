import sqlite3
from datetime import datetime
from googletrans import Translator
import time

print("=" * 60)
print("🔧 ALLAH NAMES JADVALI YARATILMOQDA")
print("=" * 60)

# Bazaga ulanish
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# AVVAL JADVALNI YARATAMIZ - BU ENG MUHIM QISM
cursor.execute('''
    CREATE TABLE IF NOT EXISTS allah_names (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number INTEGER UNIQUE,
        name_uz TEXT,
        name_ru TEXT,
        name_ar TEXT,
        name_en TEXT,
        description_uz TEXT,
        description_ru TEXT,
        description_ar TEXT,
        description_en TEXT,
        created_at TIMESTAMP
    )
''')
conn.commit()
print("✅ allah_names jadvali yaratildi!")

# Jadval mavjudligini tekshirish
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allah_names'")
if cursor.fetchone():
    print("✅ Jadval muvaffaqiyatli yaratildi!")
else:
    print("❌ Jadval yaratilmadi!")
    exit()

translator = Translator()

print("=" * 60)
print("🌸 ALLOHNING 99 GO'ZAL ISMLARI 🌸")
print("=" * 60)

# Allohning 99 ismi (siz bergan ro'yxat bo'yicha)
allah_names = [
    (1, "Allah", "الله"),
    (2, "Ar-Rohman", "الرحمن"),
    (3, "Ar-Rohim", "الرحيم"),
    (4, "Al-Malik", "الملك"),
    (5, "Al-Quddus", "القدوس"),
    (6, "As-Salam", "السلام"),
    (7, "Al-Mu'min", "المؤمن"),
    (8, "Al-Muhaymin", "المهيمن"),
    (9, "Al-Aziz", "العزيز"),
    (10, "Al-Jabbar", "الجبار"),
    (11, "Al-Mutakabbir", "المتكبر"),
    (12, "Al-Holiq", "الخالق"),
    (13, "Al-Bāri", "البارئ"),
    (14, "Al-Musovvir", "المصور"),
    (15, "Al-G'offār", "الغفار"),
    (16, "Al-Qohhar", "القهار"),
    (17, "Al-Vahhab", "الوهاب"),
    (18, "Ar-Rozzaq", "الرزاق"),
    (19, "Al-Fattah", "الفتاح"),
    (20, "Al-'Alim", "العليم"),
    (21, "Al-Qobiz", "القابض"),
    (22, "Al-Basit", "الباسط"),
    (23, "Al-Hofiz", "الخافض"),
    (24, "Ar-Rafi'", "الرافع"),
    (25, "Al-Mu'izz", "المعز"),
    (26, "Al-Muzill", "المذل"),
    (27, "As-Sami'", "السميع"),
    (28, "Al-Basir", "البصير"),
    (29, "Al-Hakam", "الحكم"),
    (30, "Al-'Adl", "العدل"),
    (31, "Al-Latif", "اللطيف"),
    (32, "Al-Habir", "الخبير"),
    (33, "Al-Halim", "الحليم"),
    (34, "Al-'Azim", "العظيم"),
    (35, "Al-G'afur", "الغفور"),
    (36, "Ash-Shakur", "الشكور"),
    (37, "Al-'Aliyy", "العلي"),
    (38, "Al-Kabir", "الكبير"),
    (39, "Al-Hafiz", "الحفيظ"),
    (40, "Al-Muqit", "المقيت"),
    (41, "Al-Hasib", "الحسيب"),
    (42, "Al-Jalil", "الجليل"),
    (43, "Al-Karim", "الكريم"),
    (44, "Ar-Raqib", "الرقيب"),
    (45, "Al-Mujib", "المجيب"),
    (46, "Al-Wasi'", "الواسع"),
    (47, "Al-Hakim", "الحكيم"),
    (48, "Al-Wadud", "الودود"),
    (49, "Al-Majid", "المجيد"),
    (50, "Al-Ba'ith", "الباعث"),
    (51, "Ash-Shahid", "الشهيد"),
    (52, "Al-Haqq", "الحق"),
    (53, "Al-Wakil", "الوكيل"),
    (54, "Al-Qawiyy", "القوي"),
    (55, "Al-Matin", "المتين"),
    (56, "Al-Waliyy", "الولي"),
    (57, "Al-Hamid", "الحميد"),
    (58, "Al-Muhsi", "المحصي"),
    (59, "Al-Mubdi'", "المبدئ"),
    (60, "Al-Mu'id", "المعيد"),
    (61, "Al-Muhyi", "المحيي"),
    (62, "Al-Mumit", "المميت"),
    (63, "Al-Hayy", "الحي"),
    (64, "Al-Qayyum", "القيوم"),
    (65, "Al-Wajid", "الواجد"),
    (66, "Al-Majid", "الماجد"),
    (67, "Al-Wahid", "الواحد"),
    (68, "As-Samad", "الصمد"),
    (69, "Al-Qadir", "القادر"),
    (70, "Al-Muqtadir", "المقتدر"),
    (71, "Al-Muqaddim", "المقدم"),
    (72, "Al-Mu'akhkhir", "المؤخر"),
    (73, "Al-Awwal", "الأول"),
    (74, "Al-Akhir", "الآخر"),
    (75, "Az-Zahir", "الظاهر"),
    (76, "Al-Batin", "الباطن"),
    (77, "Al-Wali", "الوالي"),
    (78, "Al-Muta'ali", "المتعالي"),
    (79, "Al-Barr", "البر"),
    (80, "At-Tawwab", "التواب"),
    (81, "Al-Muntaqim", "المنتقم"),
    (82, "Al-'Afuww", "العفو"),
    (83, "Ar-Ra'uf", "الرؤوف"),
    (84, "Malik-ul-Mulk", "مالك الملك"),
    (85, "Dhul-Jalali wal-Ikram", "ذو الجلال والإكرام"),
    (86, "Al-Muqsit", "المقسط"),
    (87, "Al-Jami'", "الجامع"),
    (88, "Al-Ghaniyy", "الغني"),
    (89, "Al-Mughni", "المغني"),
    (90, "Al-Mani'", "المانع"),
    (91, "Ad-Darr", "الضار"),
    (92, "An-Nafi'", "النافع"),
    (93, "An-Nur", "النور"),
    (94, "Al-Hadi", "الهادي"),
    (95, "Al-Badi'", "البديع"),
    (96, "Al-Baqi", "الباقي"),
    (97, "Al-Warith", "الوارث"),
    (98, "Ar-Rashid", "الرشيد"),
    (99, "As-Sabur", "الصبور")
]

print("\n" + "=" * 60)
print("🤲 ALLOHNING 99 GO'ZAL ISMLARI BAZAGA QO'SHILMOQDA")
print("=" * 60)

success_count = 0
error_count = 0

for num, name_uz, name_ar in allah_names:
    try:
        print(f"\n🔄 {num}. {name_uz} tarjima qilinmoqda...")
        
        # Rus va ingliz tillariga tarjima qilish
        name_ru = translator.translate(name_uz, dest='ru').text
        name_en = translator.translate(name_uz, dest='en').text
        
        # Ma'nolarni tarjima qilish
        desc_uz = f"{name_uz} - Allohning go'zal ismlaridan biri"
        desc_ru = translator.translate(desc_uz, dest='ru').text
        desc_ar = translator.translate(desc_uz, dest='ar').text
        desc_en = translator.translate(desc_uz, dest='en').text
        
        cursor.execute('''
            INSERT OR REPLACE INTO allah_names 
            (number, name_uz, name_ru, name_ar, name_en,
             description_uz, description_ru, description_ar, description_en, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (num, name_uz, name_ru, name_ar, name_en,
              desc_uz, desc_ru, desc_ar, desc_en, datetime.now()))
        
        conn.commit()
        print(f"✅ {num}. {name_uz} - {name_ar}")
        success_count += 1
        
        # Tarjimalar orasida biroz kutish (bloklanmaslik uchun)
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ {num}. Xatolik: {e}")
        error_count += 1

# Hadisni saqlash
hadith_uz = "Nabiy Sallallohu Alayhi Vossallam: «Allohning to'qson to'qqizta ismi bor. Kim ularni yod olsa, Jannatga kiradi. Albatta, Alloh toqdir va toqni yaxshi ko'radi» dedilar.☝️😊"
hadith_ru = "Пророк (мир ему и благословение Аллаха) сказал: «У Аллаха девяносто девять имен. Кто выучит их, тот войдет в Рай. Поистине, Аллах нечетный и любит нечетное»."
hadith_ar = "قال النبي صلى الله عليه وسلم: «إن لله تسعة وتسعين اسما، من أحصاها دخل الجنة، إن الله وتر يحب الوتر»."
hadith_en = "The Prophet (peace be upon him) said: \"Allah has ninety-nine names. Whoever memorizes them will enter Paradise. Indeed, Allah is Odd and loves odd numbers.\""

# Hadis jadvali
cursor.execute('''
    CREATE TABLE IF NOT EXISTS hadith (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text_uz TEXT,
        text_ru TEXT,
        text_ar TEXT,
        text_en TEXT
    )
''')
cursor.execute('''
    INSERT OR REPLACE INTO hadith (id, text_uz, text_ru, text_ar, text_en)
    VALUES (1, ?, ?, ?, ?)
''', (hadith_uz, hadith_ru, hadith_ar, hadith_en))
conn.commit()

conn.close()

print("\n" + "=" * 60)
print("🌸 BAZAGA QO'SHISH YAKUNLANDI 🌸")
print("=" * 60)
print(f"✅ Muvaffaqiyatli: {success_count} ta")
print(f"❌ Xatolik: {error_count} ta")
print(f"📊 Jami: {success_count + error_count} ta")
print("=" * 60)
print("🍃🌸سبحان الله🌸🍃")
print("=" * 60)