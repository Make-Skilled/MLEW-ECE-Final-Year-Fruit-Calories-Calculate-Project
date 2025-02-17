from datetime import datetime
import sqlite3
import json

def init_db():
    """Initialize the database with the latest schema."""
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    try:
        # Create new scans table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS scans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      fruit_name TEXT,
                      calories REAL,
                      serving_size REAL,
                      scan_date TIMESTAMP,
                      nutrition_data TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(id))''')
        
        # Drop existing meal_plans table if it exists
        c.execute('DROP TABLE IF EXISTS meal_plans')
        
        # Create meal plans table with updated schema
        c.execute('''CREATE TABLE meal_plans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      fruits TEXT,
                      total_calories REAL,
                      total_protein REAL,
                      total_fiber REAL,
                      plan_date TIMESTAMP,
                      notes TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(id))''')
        
        conn.commit()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_scan(user_id, fruit_name, calories, serving_size, nutrition_data):
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO scans 
                 (user_id, fruit_name, calories, serving_size, scan_date, nutrition_data)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, fruit_name, calories, serving_size, 
               datetime.now().strftime('%Y-%m-%d %H:%M:%S'), json.dumps(nutrition_data)))
    
    conn.commit()
    conn.close()

def get_scan_history(user_id, limit=10):
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    c.execute('''SELECT * FROM scans 
                 WHERE user_id = ?
                 ORDER BY scan_date DESC LIMIT ?''', (user_id, limit))
    history = c.fetchall()
    
    conn.close()
    return history

def get_meal_plans(limit=10):
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    c.execute('''SELECT * FROM meal_plans 
                 ORDER BY plan_date DESC LIMIT ?''', (limit,))
    plans = c.fetchall()
    
    conn.close()
    return plans

def save_meal_plan(user_id, fruits, total_calories, notes=''):
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    try:
        # Create meal_plans table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS meal_plans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      fruits TEXT,
                      total_calories REAL,
                      total_protein REAL,
                      total_fiber REAL,
                      plan_date TIMESTAMP,
                      notes TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(id))''')
        
        # Calculate total protein and fiber
        total_protein = sum(fruit.get('protein', 0) for fruit in fruits)
        total_fiber = sum(fruit.get('fiber', 0) for fruit in fruits)
        
        c.execute('''INSERT INTO meal_plans 
                     (user_id, fruits, total_calories, total_protein, total_fiber, plan_date, notes)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, json.dumps(fruits), total_calories, total_protein, total_fiber,
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notes))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving meal plan: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_meal_plans(user_id, limit=10):
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    try:
        c.execute('''SELECT id, fruits, total_calories, total_protein, total_fiber, plan_date, notes 
                     FROM meal_plans 
                     WHERE user_id = ?
                     ORDER BY plan_date DESC LIMIT ?''', (user_id, limit))
        plans = c.fetchall()
        
        # Convert to list of dictionaries for easier handling
        return [{
            'id': p[0],
            'fruits': p[1],
            'total_calories': p[2],
            'total_protein': p[3],
            'total_fiber': p[4],
            'plan_date': p[5],
            'notes': p[6]
        } for p in plans]
    except Exception as e:
        print(f"Error getting meal plans: {e}")
        return []
    finally:
        conn.close()

def delete_meal_plan(user_id, plan_id):
    conn = sqlite3.connect('fruit_tracker.db')
    c = conn.cursor()
    
    try:
        # Verify the meal plan belongs to the user
        c.execute('SELECT user_id FROM meal_plans WHERE id = ?', (plan_id,))
        result = c.fetchone()
        if not result or result[0] != user_id:
            return False
        
        c.execute('DELETE FROM meal_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting meal plan: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
