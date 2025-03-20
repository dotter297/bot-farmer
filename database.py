import sqlite3
#код базы данных

def get_all_accounts():
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, phone_number, session_name, api_id, status FROM accounts")
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def delete_account(phone_number):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts WHERE phone_number = ?", (phone_number,))
    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      phone_number TEXT UNIQUE,
                      session_name TEXT UNIQUE,
                      api_id INTEGER,
                      api_hash TEXT,
                      status TEXT)''')
    conn.commit()
    conn.close()

def save_api_keys(phone_number, api_id, api_hash):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO accounts (phone_number, api_id, api_hash, status) VALUES (?, ?, ?, ?)",
                   (phone_number, api_id, api_hash, "pending"))
    conn.commit()
    conn.close()

def get_api_keys(phone_number):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT api_id, api_hash FROM accounts WHERE phone_number = ?", (phone_number,))
    result = cursor.fetchone()
    conn.close()
    return result
