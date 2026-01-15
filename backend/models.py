import sqlite3
from config import Config
import bcrypt
from datetime import datetime

class Database:
    def __init__(self):
        # Extract just the database name from DATABASE_URL
        db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                site_source TEXT,
                product_title TEXT,
                current_price REAL,
                target_price REAL NOT NULL,
                last_checked TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                alert_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
    
    def get_cursor(self):
        return self.conn.cursor()

class User:
    @staticmethod
    def create(db, email, password):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor = db.get_cursor()
        cursor.execute(
            'INSERT INTO users (email, password_hash) VALUES (?, ?)',
            (email, password_hash.decode('utf-8'))
        )
        db.conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def find_by_email(db, email):
        cursor = db.get_cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

class Product:
    @staticmethod
    def create(db, user_id, url, target_price, site_source, product_title, current_price):
        cursor = db.get_cursor()
        cursor.execute(
            '''INSERT INTO products 
               (user_id, url, target_price, site_source, product_title, current_price, last_checked)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, url, target_price, site_source, product_title, current_price, datetime.now())
        )
        db.conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_user_products(db, user_id):
        cursor = db.get_cursor()
        cursor.execute(
            'SELECT * FROM products WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def count_user_products(db, user_id):
        cursor = db.get_cursor()
        cursor.execute(
            'SELECT COUNT(*) as count FROM products WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        return cursor.fetchone()['count']
    
    @staticmethod
    def delete(db, product_id, user_id):
        cursor = db.get_cursor()
        cursor.execute(
            'UPDATE products SET is_active = 0 WHERE id = ? AND user_id = ?',
            (product_id, user_id)
        )
        db.conn.commit()
    
    @staticmethod
    def update_price(db, product_id, new_price):
        cursor = db.get_cursor()
        cursor.execute(
            'UPDATE products SET current_price = ?, last_checked = ? WHERE id = ?',
            (new_price, datetime.now(), product_id)
        )
        db.conn.commit()
    
    @staticmethod
    def mark_alert_sent(db, product_id):
        cursor = db.get_cursor()
        cursor.execute(
            'UPDATE products SET alert_sent = 1 WHERE id = ?',
            (product_id,)
        )
        db.conn.commit()
    
    @staticmethod
    def get_all_active(db):
        cursor = db.get_cursor()
        cursor.execute('SELECT * FROM products WHERE is_active = 1')
        return [dict(row) for row in cursor.fetchall()]