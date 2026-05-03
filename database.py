import os, sqlite3, shutil, requests
from kivy.utils import platform
from kivy.app import App


class Database:
    def __init__(self):
        self.db_name = "tutor_ap.db"
        self.db_path = None
        # Ensure this URL matches your Firebase exactly
        self.cloud_url = "https://myguru-app-default-rtdb.firebaseio.com/"

    def get_path(self):
        """Determines the writable path based on the platform."""
        if self.db_path: return self.db_path
        if platform == 'android':
            self.db_path = os.path.join(App.get_running_app().user_data_dir, self.db_name)
        else:
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.db_name)
        return self.db_path

    def get_connection(self):
        conn = sqlite3.connect(self.get_path())
        conn.row_factory = sqlite3.Row
        return conn

    def setup_db(self):
        """Initializes tables, handles migrations, and creates Admin."""
        create_commands = [
            """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT, role TEXT, is_verified INTEGER DEFAULT 0, verification_code TEXT, credits INTEGER DEFAULT 0, referral_code TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS student_profiles (email TEXT PRIMARY KEY, name TEXT, phone TEXT, house_no TEXT, street TEXT, landmark TEXT, area TEXT, city TEXT, pincode TEXT, class TEXT, subjects TEXT, aadhar_path TEXT, status TEXT DEFAULT 'pending')""",
            """CREATE TABLE IF NOT EXISTS tutor_profiles (email TEXT PRIMARY KEY, name TEXT, phone TEXT, area TEXT, city TEXT, landmark TEXT, house_no TEXT, street TEXT, pincode TEXT, subjects TEXT, qualification TEXT, experience TEXT, tuition_mode TEXT, aadhar_path TEXT, status TEXT DEFAULT 'pending')""",
            """CREATE TABLE IF NOT EXISTS credit_purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, amount REAL, status TEXT DEFAULT 'pending', request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS credit_usage_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, target_name TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS admin_broadcasts (id INTEGER PRIMARY KEY AUTOINCREMENT, target_role TEXT, message_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        ]
        try:
            with self.get_connection() as conn:
                for cmd in create_commands: conn.execute(cmd)

                # --- AUTO-MIGRATION LOGIC ---
                for table in ["student_profiles", "tutor_profiles"]:
                    cols = ["house_no", "street", "landmark", "city", "pincode", "class", "subjects", "aadhar_path"]
                    for col in cols:
                        try:
                            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
                        except:
                            pass
                conn.commit()

            self.create_default_admin()
            print("--- DATABASE SETUP COMPLETE ---")
        except Exception as e:
            print(f"DB Setup Error: {e}")

    def create_default_admin(self):
        """Creates the default admin if missing."""
        existing = self.query("SELECT * FROM users WHERE role='admin'", fetchone=True)
        if not existing:
            self.query(
                "INSERT INTO users (email, password, role, is_verified) VALUES (?, ?, 'admin', 1)",
                ("admin@gmail.com", "admin123")
            )
            print("--- DEFAULT ADMIN CREATED: admin@gmail.com / admin123 ---")

    # --- THE CLOUD METHODS ---

    def get_from_cloud(self, table):
        """Fetches data from Firebase."""
        try:
            url = f"{self.cloud_url}{table}.json"
            response = requests.get(url)
            if response.status_code == 200 and response.json():
                return [v for k, v in response.json().items()]
            return []
        except Exception as e:
            print(f"Cloud Fetch Error: {e}")
            return []

    def save_to_cloud(self, table, email, data):
        """Saves data to Firebase."""
        try:
            clean_email = email.replace('.', '_')
            url = f"{self.cloud_url}{table}/{clean_email}.json"
            response = requests.put(url, json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Cloud Save Error: {e}")
            return False

    # --- FIXED QUERY METHOD ---

    def query(self, sql, params=(), fetchone=False):
        """Safe execution method that avoids returning None on SELECT."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if not isinstance(params, (list, tuple)): params = (params,)
                cursor.execute(sql, params)

                if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    conn.commit()
                    return cursor.lastrowid if sql.strip().upper().startswith("INSERT") else cursor.rowcount

                res = cursor.fetchone() if fetchone else cursor.fetchall()

                # If fetchone is True, return a dict or an empty dict (not None)
                if fetchone:
                    return dict(res) if res else {}

                # For regular fetchall, return a list of dicts or an empty list (not None)
                return [dict(row) for row in res] if res else []
        except Exception as e:
            print(f"SQL Error: {e}")
            return {} if fetchone else []