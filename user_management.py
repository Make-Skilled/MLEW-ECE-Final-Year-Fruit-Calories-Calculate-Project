from datetime import datetime, timedelta
import sqlite3
import hashlib
import json
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

def get_user(user_id):
    """Retrieve user by ID."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''SELECT id, username, email FROM users WHERE id = ?''', (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def init_user_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  email TEXT UNIQUE,
                  created_at TIMESTAMP)''')
    
    # Create nutritional goals table
    c.execute('''CREATE TABLE IF NOT EXISTS nutritional_goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  daily_calories INTEGER,
                  daily_protein REAL,
                  daily_fiber REAL,
                  created_at TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Create progress tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS progress_tracking
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date DATE,
                  fruits_consumed TEXT,
                  total_calories INTEGER,
                  total_protein REAL,
                  total_fiber REAL,
                  notes TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email):
    """Register a new user."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO users (username, password_hash, email, created_at)
                     VALUES (?, ?, ?, ?)''',
                  (username, hash_password(password), email, datetime.now()))
        conn.commit()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    finally:
        conn.close()

def login_user(username, password):
    """Verify user credentials."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''SELECT id, password_hash FROM users WHERE username = ?''',
              (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[1] == hash_password(password):
        return True, result[0]  # Return user ID
    return False, None

def set_nutritional_goals(user_id, daily_calories, daily_protein, daily_fiber):
    """Set nutritional goals for a user."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO nutritional_goals 
                 (user_id, daily_calories, daily_protein, daily_fiber, created_at)
                 VALUES (?, ?, ?, ?, ?)''',
              (user_id, daily_calories, daily_protein, daily_fiber, datetime.now()))
    
    conn.commit()
    conn.close()

def track_progress(user_id, fruits_consumed, total_calories, total_protein, total_fiber, notes=""):
    """Track daily nutritional progress."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO progress_tracking 
                 (user_id, date, fruits_consumed, total_calories, 
                  total_protein, total_fiber, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_id, datetime.now().date(), json.dumps(fruits_consumed),
               total_calories, total_protein, total_fiber, notes))
    
    conn.commit()
    conn.close()

def get_weekly_progress(user_id):
    """Get user's progress for the last 7 days, combining scans and meal plans."""
    # Connect to both databases
    user_conn = sqlite3.connect('users.db')
    fruit_conn = sqlite3.connect('fruit_tracker.db')
    user_c = user_conn.cursor()
    fruit_c = fruit_conn.cursor()
    
    # Get today's date at midnight for consistent comparison
    today = datetime.now().date()
    seven_days_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Initialize daily tracking for the past 7 days
    daily_data = {}
    for i in range(7):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_data[date] = {
            'date': date,
            'scans': [],
            'meal_plans': [],
            'total_calories': 0,
            'total_protein': 0,
            'total_fiber': 0,
            'activity_count': 0  # Track number of scans + meal plans
        }
    
    try:
        # Get scans from fruit_tracker.db
        fruit_c.execute('''
            SELECT scan_date, fruit_name, calories, nutrition_data
            FROM scans
            WHERE user_id = ? AND date(scan_date) >= date(?)
            ORDER BY scan_date ASC
        ''', (user_id, seven_days_ago))
        
        for scan in fruit_c.fetchall():
            try:
                date = datetime.strptime(scan[0].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            except ValueError:
                # Try parsing without time
                date = datetime.strptime(scan[0].split()[0], '%Y-%m-%d').strftime('%Y-%m-%d')
            if date in daily_data:
                nutrition = json.loads(scan[3]) if scan[3] else {}
                daily_data[date]['scans'].append({
                    'fruit': scan[1],
                    'calories': scan[2],
                    'protein': nutrition.get('protein', 0),
                    'fiber': nutrition.get('fiber', 0)
                })
                daily_data[date]['total_calories'] += scan[2]
                daily_data[date]['total_protein'] += nutrition.get('protein', 0)
                daily_data[date]['total_fiber'] += nutrition.get('fiber', 0)
                daily_data[date]['activity_count'] += 1
        
        # Get meal plans from fruit_tracker.db
        fruit_c.execute('''
            SELECT plan_date, fruits, total_calories, total_protein, total_fiber
            FROM meal_plans
            WHERE user_id = ? AND date(plan_date) >= date(?)
            ORDER BY plan_date ASC
        ''', (user_id, seven_days_ago))
        
        for plan in fruit_c.fetchall():
            try:
                date = datetime.strptime(plan[0].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            except ValueError:
                # Try parsing without time
                date = datetime.strptime(plan[0].split()[0], '%Y-%m-%d').strftime('%Y-%m-%d')
            if date in daily_data:
                daily_data[date]['meal_plans'].append({
                    'fruits': json.loads(plan[1]),
                    'calories': plan[2],
                    'protein': plan[3],
                    'fiber': plan[4]
                })
                daily_data[date]['total_calories'] += plan[2]
                daily_data[date]['total_protein'] += plan[3]
                daily_data[date]['total_fiber'] += plan[4]
                daily_data[date]['activity_count'] += 1
        
        # Get user's goals
        goals = get_nutritional_goals(user_id)
        
        # Calculate weekly summary
        active_days = sum(1 for d in daily_data.values() if d['activity_count'] > 0)
        weekly_summary = {
            'dates': list(daily_data.keys()),
            'daily_data': daily_data,
            'goals': goals,
            'total_activities': sum(d['activity_count'] for d in daily_data.values()),
            'active_days': active_days,
            'avg_calories': sum(d['total_calories'] for d in daily_data.values()) / max(active_days, 1),
            'avg_protein': sum(d['total_protein'] for d in daily_data.values()) / max(active_days, 1),
            'avg_fiber': sum(d['total_fiber'] for d in daily_data.values()) / max(active_days, 1)
        }
        
        # Calculate goal progress
        if goals:
            weekly_summary.update({
                'calories_progress': (weekly_summary['avg_calories'] / goals['daily_calories'] * 100) if goals.get('daily_calories') else 0,
                'protein_progress': (weekly_summary['avg_protein'] / goals['daily_protein'] * 100) if goals.get('daily_protein') else 0,
                'fiber_progress': (weekly_summary['avg_fiber'] / goals['daily_fiber'] * 100) if goals.get('daily_fiber') else 0
            })
        
        return weekly_summary
        
    finally:
        user_conn.close()
        fruit_conn.close()

def get_nutritional_goals(user_id):
    """Get user's current nutritional goals."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''SELECT daily_calories, daily_protein, daily_fiber 
                 FROM nutritional_goals 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC 
                 LIMIT 1''', (user_id,))
    
    goals = c.fetchone()
    conn.close()
    
    return {
        'daily_calories': goals[0] if goals else 2000,
        'daily_protein': goals[1] if goals else 50,
        'daily_fiber': goals[2] if goals else 25
    }
