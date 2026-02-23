import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'UZ',
                registered_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Questions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_uz TEXT,
                question_ru TEXT,
                question_ar TEXT,
                question_en TEXT,
                option1_uz TEXT,
                option1_ru TEXT,
                option1_ar TEXT,
                option1_en TEXT,
                option2_uz TEXT,
                option2_ru TEXT,
                option2_ar TEXT,
                option2_en TEXT,
                option3_uz TEXT,
                option3_ru TEXT,
                option3_ar TEXT,
                option3_en TEXT,
                correct_option INTEGER CHECK(correct_option IN (1,2,3)),
                created_at TIMESTAMP,
                created_by INTEGER,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Prophets stories table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prophets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT,
                name_ru TEXT,
                name_ar TEXT,
                name_en TEXT,
                audio_file_id TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # User answers tracking
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                selected_option INTEGER,
                is_correct BOOLEAN,
                answered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')
        
        # Allohning 99 ismi jadvali
        self.cursor.execute('''
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
        
        # Foydalanuvchi statistikasi
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                last_question_date DATE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # 20 ta savol rekordi
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_20_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                correct_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                reward_paid BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Foydalanuvchi savollari (20 talik uchun)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_question_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id INTEGER,
                question_id INTEGER,
                selected_option INTEGER,
                is_correct BOOLEAN,
                answered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')
        
        # Karta raqamlari
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                card_number TEXT,
                card_name TEXT,
                submitted_at TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                verified_by INTEGER,
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Mukofotlar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id INTEGER,
                amount INTEGER DEFAULT 200000,
                status TEXT DEFAULT 'pending',
                paid_by INTEGER,
                paid_at TIMESTAMP,
                check_photo_id TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
          # User wait time jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wait_times (
                user_id INTEGER PRIMARY KEY,
                wait_until TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()
        print("✅ Database tables created successfully")
        
    def set_user_wait(self, user_id, minutes=30):
        """Foydalanuvchi uchun kutish vaqti o'rnatish"""
        try:
            from datetime import datetime, timedelta
            wait_until = datetime.now() + timedelta(minutes=minutes)
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_wait_times (user_id, wait_until)
                VALUES (?, ?)
            ''', (user_id, wait_until))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error setting wait time: {e}")
            return False

    def check_user_wait(self, user_id):
        """Foydalanuvchi kutish vaqtida yoki yo'qligini tekshirish"""
        try:
            from datetime import datetime
            self.cursor.execute('''
                SELECT wait_until FROM user_wait_times WHERE user_id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            
            if result:
                wait_until = datetime.fromisoformat(result[0])
                if datetime.now() < wait_until:
                    # Hali kutish vaqti
                    remaining = (wait_until - datetime.now()).seconds // 60
                    return True, remaining
                else:
                    # Kutish vaqti tugagan
                    self.cursor.execute('DELETE FROM user_wait_times WHERE user_id = ?', (user_id,))
                    self.conn.commit()
                    return False, 0
            return False, 0
        except Exception as e:
            print(f"Error checking wait time: {e}")
            return False, 0    
    
    # User methods
    def add_user(self, user_id, username, first_name):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, registered_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.now()))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user_language(self, user_id):
        try:
            self.cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 'UZ'
        except Exception as e:
            print(f"Error getting user language: {e}")
            return 'UZ'
    
    def set_user_language(self, user_id, language):
        try:
            self.cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
            self.conn.commit()
        except Exception as e:
            print(f"Error setting user language: {e}")
    
    def update_user_name(self, user_id, name):
        try:
            self.cursor.execute('''
                UPDATE users SET first_name = ? WHERE user_id = ?
            ''', (name, user_id))
            self.conn.commit()
        except Exception as e:
            print(f"Error updating user name: {e}")
    
    # Questions methods
    def add_question(self, question_data):
        try:
            query = '''
                INSERT INTO questions (
                    question_uz, question_ru, question_ar, question_en,
                    option1_uz, option1_ru, option1_ar, option1_en,
                    option2_uz, option2_ru, option2_ar, option2_en,
                    option3_uz, option3_ru, option3_ar, option3_en,
                    correct_option, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.cursor.execute(query, question_data)
            self.conn.commit()
            question_id = self.cursor.lastrowid
            self.cursor.execute('UPDATE questions SET is_active = 1 WHERE id = ?', (question_id,))
            self.conn.commit()
            return question_id
        except Exception as e:
            print(f"Error adding question: {e}")
            return None
    
    def get_random_question(self, lang='UZ'):
        try:
            if lang not in ['UZ', 'RU', 'AR', 'EN']:
                lang = 'UZ'
            
            query = f'''
                SELECT id, question_{lang}, option1_{lang}, option2_{lang}, option3_{lang}, correct_option 
                FROM questions 
                WHERE is_active = 1 
                ORDER BY RANDOM() 
                LIMIT 1
            '''
            self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error getting random question: {e}")
            return None
    
    def get_random_question_excluding(self, lang='UZ', excluded_ids=None):
        try:
            if excluded_ids is None:
                excluded_ids = []
            
            if lang not in ['UZ', 'RU', 'AR', 'EN']:
                lang = 'UZ'
            
            print(f"🔍 get_random_question_excluding: lang={lang}, excluded_ids={excluded_ids}")
            
            if excluded_ids and len(excluded_ids) > 0:
                placeholders = ','.join(['?'] * len(excluded_ids))
                query = f'''
                    SELECT id, question_{lang}, option1_{lang}, option2_{lang}, option3_{lang}, correct_option 
                    FROM questions 
                    WHERE is_active = 1 
                      AND question_{lang} IS NOT NULL 
                      AND question_{lang} != ''
                      AND id NOT IN ({placeholders})
                    ORDER BY RANDOM() 
                    LIMIT 1
                '''
                self.cursor.execute(query, excluded_ids)
            else:
                query = f'''
                    SELECT id, question_{lang}, option1_{lang}, option2_{lang}, option3_{lang}, correct_option 
                    FROM questions 
                    WHERE is_active = 1 
                      AND question_{lang} IS NOT NULL 
                      AND question_{lang} != ''
                    ORDER BY RANDOM() 
                    LIMIT 1
                '''
                self.cursor.execute(query)
            
            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Topildi: ID={result[0]}, savol={result[1][:30]}...")
            else:
                print(f"❌ {lang} tilida savol topilmadi, UZ ga o'tiladi")
                # Agar tanlangan tilda savol bo'lmasa, o'zbekchasini olish
                if lang != 'UZ':
                    return self.get_random_question_excluding('UZ', excluded_ids)
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting random question excluding: {e}")
            return None
    
    def get_all_questions(self):
        try:
            self.cursor.execute('SELECT id, question_uz, is_active FROM questions')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting all questions: {e}")
            return []
    
    # Prophet methods
    def add_prophet(self, name_uz, name_ru, name_ar, name_en, audio_file_id):
        try:
            self.cursor.execute('''
                INSERT INTO prophets (name_uz, name_ru, name_ar, name_en, audio_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name_uz, name_ru, name_ar, name_en, audio_file_id, datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error adding prophet: {e}")
            return None
    
    def get_prophets(self, lang='UZ'):
        try:
            if lang not in ['UZ', 'RU', 'AR', 'EN']:
                lang = 'UZ'
            self.cursor.execute(f'SELECT id, name_{lang}, audio_file_id FROM prophets')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting prophets: {e}")
            return []
    
    def get_prophet_audio(self, prophet_id):
        try:
            self.cursor.execute('SELECT audio_file_id FROM prophets WHERE id = ?', (prophet_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting prophet audio: {e}")
            return None
    
    # Answer tracking
    def save_answer(self, user_id, question_id, selected_option, is_correct):
        try:
            self.cursor.execute('''
                INSERT INTO user_answers (user_id, question_id, selected_option, is_correct, answered_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, question_id, selected_option, is_correct, datetime.now()))
            self.conn.commit()
        except Exception as e:
            print(f"Error saving answer: {e}")
    
    # Statistics
    def get_total_users(self):
        try:
            self.cursor.execute('SELECT COUNT(*) FROM users')
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting total users: {e}")
            return 0
    
    def get_today_users(self):
        try:
            self.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE date(registered_at) = date('now')
            ''')
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting today users: {e}")
            return 0
    
    def get_questions_stats(self):
        stats = {'UZ': 0, 'RU': 0, 'AR': 0, 'EN': 0}
        try:
            for lang in ['UZ', 'RU', 'AR', 'EN']:
                self.cursor.execute(f'SELECT COUNT(*) FROM questions WHERE question_{lang} IS NOT NULL AND is_active = 1')
                stats[lang] = self.cursor.fetchone()[0]
            return stats
        except Exception as e:
            print(f"Error getting questions stats: {e}")
            return stats
    
    # ============================================
    # 20 TA SAVOL SESSIYASI UCHUN METODLAR
    # ============================================
    
    def start_20_questions_session(self, user_id):
        """20 ta savol uchun yangi sessiya boshlash"""
        try:
            self.cursor.execute('''
                SELECT id FROM user_20_questions 
                WHERE user_id = ? AND status = 'active'
            ''', (user_id,))
            
            if self.cursor.fetchone():
                return None
            
            self.cursor.execute('''
                INSERT INTO user_20_questions (user_id, start_date, correct_count, status)
                VALUES (?, ?, 0, 'active')
            ''', (user_id, datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error starting session: {e}")
            return None
    
    def get_active_session(self, user_id):
        """Foydalanuvchining aktiv sessiyasini olish"""
        try:
            self.cursor.execute('''
                SELECT id, correct_count FROM user_20_questions 
                WHERE user_id = ? AND status = 'active'
            ''', (user_id,))
            result = self.cursor.fetchone()
            
            if result:
                print(f"✅ Aktiv sessiya topildi: ID={result[0]}, correct={result[1]}")
                return result
            else:
                print(f"ℹ️ Aktiv sessiya yo'q (user_id={user_id})")
                return None
        except Exception as e:
            print(f"Error getting active session: {e}")
            return None
    
    def save_question_answer(self, user_id, session_id, question_id, selected_option, is_correct):
        """Savol javobini saqlash"""
        try:
            self.cursor.execute('''
                INSERT INTO user_question_sessions 
                (user_id, session_id, question_id, selected_option, is_correct, answered_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, session_id, question_id, selected_option, is_correct, datetime.now()))
            
            if is_correct:
                self.cursor.execute('''
                    UPDATE user_20_questions 
                    SET correct_count = correct_count + 1 
                    WHERE id = ? AND user_id = ?
                ''', (session_id, user_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving answer: {e}")
            return False
    
    def complete_session(self, session_id, user_id, success=True):
        """Sessiyani yakunlash"""
        try:
            status = 'completed' if success else 'failed'
            self.cursor.execute('''
                UPDATE user_20_questions 
                SET status = ?, end_date = ? 
                WHERE id = ? AND user_id = ?
            ''', (status, datetime.now(), session_id, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error completing session: {e}")
            return False
    
    def create_reward(self, user_id, session_id):
        """Mukofot yaratish"""
        try:
            self.cursor.execute('''
                INSERT INTO rewards (user_id, session_id, amount, status, created_at)
                VALUES (?, ?, 200000, 'pending', ?)
            ''', (user_id, session_id, datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error creating reward: {e}")
            return None
    
    def save_card_info(self, user_id, card_number, card_name):
        """Karta ma'lumotlarini saqlash"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_cards (user_id, card_number, card_name, submitted_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, card_number, card_name, datetime.now()))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving card info: {e}")
            return False
    
    def mark_reward_paid(self, reward_id, admin_id, check_photo_id=None):
        """Mukofotni to'langan deb belgilash"""
        try:
            self.cursor.execute('''
                UPDATE rewards 
                SET status = 'paid', paid_by = ?, paid_at = ?, check_photo_id = ?
                WHERE id = ?
            ''', (admin_id, datetime.now(), check_photo_id, reward_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error marking reward paid: {e}")
            return False
    
    def get_pending_rewards(self):
        """Kutilayotgan mukofotlarni olish"""
        try:
            self.cursor.execute('''
                SELECT r.id, r.user_id, u.first_name, u.username, r.amount, r.created_at
                FROM rewards r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.status = 'pending'
                ORDER BY r.created_at DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting pending rewards: {e}")
            return []
    
    def update_user_stats(self, user_id, is_correct):
        """Foydalanuvchi statistikasini yangilash"""
        try:
            self.cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    INSERT INTO user_stats (user_id, correct_count, wrong_count, total_questions)
                    VALUES (?, 0, 0, 0)
                ''', (user_id,))
            
            if is_correct:
                self.cursor.execute('''
                    UPDATE user_stats 
                    SET correct_count = correct_count + 1,
                        total_questions = total_questions + 1,
                        current_streak = current_streak + 1,
                        best_streak = MAX(best_streak, current_streak + 1)
                    WHERE user_id = ?
                ''', (user_id,))
            else:
                self.cursor.execute('''
                    UPDATE user_stats 
                    SET wrong_count = wrong_count + 1,
                        total_questions = total_questions + 1,
                        current_streak = 0
                    WHERE user_id = ?
                ''', (user_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False
    
    def get_all_users_stats(self):
        """Barcha foydalanuvchilar statistikasini olish"""
        try:
            self.cursor.execute('''
                SELECT u.user_id, u.first_name, u.username, u.language,
                       COALESCE(us.correct_count, 0) as correct,
                       COALESCE(us.wrong_count, 0) as wrong,
                       COALESCE(us.total_questions, 0) as total,
                       COALESCE(us.best_streak, 0) as best_streak
                FROM users u
                LEFT JOIN user_stats us ON u.user_id = us.user_id
                ORDER BY us.correct_count DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting users stats: {e}")
            return []
    
    def get_user_answers(self, user_id=None, limit=100):
        """Foydalanuvchi javoblarini olish"""
        try:
            if user_id:
                self.cursor.execute('''
                    SELECT ua.*, u.first_name, u.username, q.question_uz
                    FROM user_answers ua
                    JOIN users u ON ua.user_id = u.user_id
                    JOIN questions q ON ua.question_id = q.id
                    WHERE ua.user_id = ?
                    ORDER BY ua.answered_at DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                self.cursor.execute('''
                    SELECT ua.*, u.first_name, u.username, q.question_uz
                    FROM user_answers ua
                    JOIN users u ON ua.user_id = u.user_id
                    JOIN questions q ON ua.question_id = q.id
                    ORDER BY ua.answered_at DESC
                    LIMIT ?
                ''', (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting user answers: {e}")
            return []
    
    # Alloh names methods
    def get_allah_names(self, lang='UZ'):
        try:
            if lang not in ['UZ', 'RU', 'AR', 'EN']:
                lang = 'UZ'
            self.cursor.execute(f'SELECT number, name_{lang}, description_{lang} FROM allah_names ORDER BY number')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting allah names: {e}")
            return []
    
    def get_allah_name_by_number(self, number, lang='UZ'):
        try:
            if lang not in ['UZ', 'RU', 'AR', 'EN']:
                lang = 'UZ'
            self.cursor.execute(f'SELECT number, name_{lang}, description_{lang} FROM allah_names WHERE number = ?', (number,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error getting allah name: {e}")
            return None
    
    def close(self):
        try:
            self.conn.close()
        except Exception as e:
            print(f"Error closing database: {e}")
            