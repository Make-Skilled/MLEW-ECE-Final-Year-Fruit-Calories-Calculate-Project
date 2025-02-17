from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from tensorflow.keras.models import load_model # type: ignore
from PIL import Image, ImageOps
import numpy as np
import logging
from flask_cors import CORS
import json
from datetime import datetime
import csv
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO

# Import custom modules
from nutrition_db import get_fruit_nutrition, calculate_serving_calories, get_seasonal_fruits
from database import (init_db, save_scan, get_scan_history, save_meal_plan,
                  get_meal_plans, delete_meal_plan)
from user_management import (init_user_db, register_user, login_user as auth_login, 
    set_nutritional_goals, track_progress, get_weekly_progress, get_nutritional_goals,
    User, get_user)
from recipes import get_recipes_by_fruit, calculate_recipe_nutrition
from fruit_comparison import (compare_fruits, find_alternatives, get_nutritional_ranking,
    get_complementary_fruits, correct_fruit_spelling)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
CORS(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Template filters
@app.template_filter('datetime')
def format_datetime(value):
    if value is None:
        return ''
    if isinstance(value, (int, float)):
        try:
            value = datetime.fromtimestamp(value)
        except (ValueError, OSError, TypeError):
            return str(value)
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return str(value)

@app.template_filter('fromjson')
def from_json(value):
    return json.loads(value)

@app.template_filter('safe_title')
def safe_title(value):
    if value is None:
        return ''
    return str(value).title()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add custom functions to Jinja2 environment
app.jinja_env.globals.update(min=min)

# Initialize databases
init_db()
init_user_db()

# Load the model and labels
try:
    model = load_model("keras_Model.h5", compile=False)
    with open("labels.txt", "r") as file:
        class_names = [correct_fruit_spelling(line.strip().split(" ", 1)[-1]) for line in file.readlines()]
    logging.info("Model and labels loaded successfully")
except Exception as e:
    logging.error(f"Loading error: {e}")
    raise e

@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)

# Routes
@app.route('/')
def index():
    seasonal_fruits = get_seasonal_fruits()
    top_fruits = get_nutritional_ranking("vitamin_c", "desc", 5)
    
    if current_user.is_authenticated:
        scan_history = get_scan_history(current_user.id, 5)
        meal_plans = get_meal_plans(5)
        weekly_progress = get_weekly_progress(current_user.id)
        
        # Create progress visualization
        progress_chart = create_progress_chart(weekly_progress)
        
        return render_template('index.html',
                             seasonal_fruits=seasonal_fruits,
                             top_fruits=top_fruits,
                             scan_history=scan_history,
                             meal_plans=meal_plans,
                             progress_chart=progress_chart)
    
    return render_template('index.html',
                         seasonal_fruits=seasonal_fruits,
                         top_fruits=top_fruits)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        success, user_id = auth_login(username, password)
        
        if success:
            user = get_user(user_id)
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        success, message = register_user(username, password, email)
        if success:
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        
        flash(message)
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if 'image' not in request.files:
        flash('No image file found.')
        return redirect(url_for('index'))

    image = request.files['image']
    serving_size = float(request.form.get('serving_size', 100))

    try:
        # Process image and make prediction
        image = Image.open(image).convert("RGB")
        image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
        image_array = np.asarray(image, dtype=np.float32)
        normalized_image_array = (image_array / 127.5) - 1
        data = np.expand_dims(normalized_image_array, axis=0)
        
        prediction = model.predict(data)
        index = np.argmax(prediction)
        class_name = str(class_names[index])  # Ensure it's a string
        confidence_score = float(prediction[0][index])

        # Get nutrition information
        nutrition_data = get_fruit_nutrition(class_name)
        if not nutrition_data:
            flash('Nutrition data not found for this fruit.')
            return redirect(url_for('index'))

        calories = calculate_serving_calories(class_name, serving_size)
        
        # Get recipes and alternatives
        recipes = get_recipes_by_fruit(class_name)
        alternatives = find_alternatives(class_name)
        complementary = get_complementary_fruits(class_name)
        
        # Save scan and track progress
        save_scan(current_user.id, class_name, calories, serving_size, nutrition_data)
        track_progress(current_user.id, [class_name], calories, 
                      nutrition_data['protein'], nutrition_data['fiber'])
        
        return render_template('prediction.html',
                             class_name=class_name,
                             calories=calories,
                             serving_size=serving_size,
                             nutrition_data=nutrition_data,
                             confidence=confidence_score,
                             recipes=recipes,
                             alternatives=alternatives,
                             complementary=complementary)

    except Exception as e:
        logging.error(f"Prediction error: {e}")
        flash('An error occurred during prediction.')
        return redirect(url_for('index'))

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    if request.method == 'POST':
        fruits = request.form.getlist('fruits')
        serving_size = float(request.form.get('serving_size', 100))
        comparison = compare_fruits(fruits, serving_size)
        return render_template('compare.html', comparison=comparison)
    
    return render_template('compare.html', fruits=class_names)

@app.route('/recipes')
def recipes():
    fruit = request.args.get('fruit')
    if fruit:
        recipes = get_recipes_by_fruit(fruit)
        return render_template('recipes.html', 
                             recipes=recipes, 
                             selected_fruit=fruit,
                             zip=zip,
                             class_names=class_names,
                             calculate_recipe_nutrition=calculate_recipe_nutrition)
    
    # Show all available fruits for recipe search
    return render_template('recipes.html', 
                          fruits=class_names,
                          class_names=class_names,
                          zip=zip,
                          calculate_recipe_nutrition=calculate_recipe_nutrition)

@app.route('/meal_plans')
@login_required
def meal_plans():
    # Get saved meal plans
    plans = get_meal_plans(current_user.id)
    goals = get_nutritional_goals(current_user.id)
    
    # Calculate statistics
    today = datetime.now().strftime('%Y-%m-%d')
    weekly_data = get_weekly_progress(current_user.id)
    today_data = weekly_data['daily_data'].get(today, {
        'total_calories': 0,
        'total_protein': 0,
        'total_fiber': 0,
        'meal_plans': [],
        'scans': []
    })
    
    stats = {
        'total_plans': len(plans),
        'avg_calories': 0,
        'avg_protein': 0,
        'avg_fiber': 0,
        'today_calories': today_data['total_calories'],
        'today_protein': today_data['total_protein'],
        'today_fiber': today_data['total_fiber'],
        'goal_calories': goals.get('daily_calories', 2000),
        'goal_protein': goals.get('daily_protein', 50),
        'goal_fiber': goals.get('daily_fiber', 25)
    }
    
    if plans:
        stats.update({
            'avg_calories': sum(plan['total_calories'] for plan in plans) / len(plans),
            'avg_protein': sum(plan['total_protein'] for plan in plans) / len(plans),
            'avg_fiber': sum(plan['total_fiber'] for plan in plans) / len(plans),
        })
    
    # Calculate progress percentages
    stats.update({
        'calories_progress': (stats['today_calories'] / stats['goal_calories'] * 100) if stats['goal_calories'] else 0,
        'protein_progress': (stats['today_protein'] / stats['goal_protein'] * 100) if stats['goal_protein'] else 0,
        'fiber_progress': (stats['today_fiber'] / stats['goal_fiber'] * 100) if stats['goal_fiber'] else 0,
        'weekly_avg_calories': weekly_data.get('avg_calories', 0),
        'weekly_avg_protein': weekly_data.get('avg_protein', 0),
        'weekly_avg_fiber': weekly_data.get('avg_fiber', 0)
    })
    
    return render_template('meal_plans.html', 
                          meal_plans=plans, 
                          fruits=class_names, 
                          stats=stats)

@app.route('/get_nutrition/<fruit_name>')
@login_required
def get_nutrition(fruit_name):
    try:
        # Get nutrition data for the fruit
        nutrition = get_fruit_nutrition(fruit_name)
        if nutrition:
            return jsonify({
                'success': True,
                'calories': nutrition['calories'],
                'protein': nutrition['protein'],
                'fiber': nutrition['fiber']
            })
        return jsonify({'success': False, 'message': 'Fruit not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/save_meal_plan', methods=['POST'])
@login_required
def save_meal_plan_route():
    try:
        data = request.get_json()
        fruits = data.get('fruits', [])
        notes = data.get('notes', '')
        
        # Calculate total calories
        total_calories = sum(fruit['calories'] for fruit in fruits)
        
        # Save the meal plan
        if save_meal_plan(current_user.id, fruits, total_calories, notes):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Failed to save meal plan'})
    except Exception as e:
        logging.error(f"Error saving meal plan: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_meal_plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_meal_plan_route(plan_id):
    try:
        if delete_meal_plan(current_user.id, plan_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Failed to delete meal plan'})
    except Exception as e:
        logging.error(f"Error deleting meal plan: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/export_history')
@login_required
def export_history():
    try:
        scan_history = get_scan_history()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Fruit', 'Calories', 'Serving Size (g)'])
        
        for scan in scan_history:
            writer.writerow([scan[4], scan[1], scan[2], scan[3]])
        
        # Create the response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'fruit_history_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        logging.error(f"Error exporting history: {e}")
        flash('Error exporting history')
        return redirect(url_for('index'))
    if fruit:
        recipes = get_recipes_by_fruit(fruit)
        return render_template('recipes.html', recipes=recipes, fruit=fruit)
    return render_template('recipes.html')

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    if request.method == 'POST':
        try:
            # Get and validate form data
            daily_calories = float(request.form.get('daily_calories', 0))
            daily_protein = float(request.form.get('daily_protein', 0))
            daily_fiber = float(request.form.get('daily_fiber', 0))
            
            # Validate reasonable ranges
            if daily_calories < 0 or daily_calories > 5000:
                flash('Please enter a reasonable daily calorie goal (0-5000)', 'error')
                return redirect(url_for('goals'))
            
            if daily_protein < 0 or daily_protein > 200:
                flash('Please enter a reasonable daily protein goal (0-200g)', 'error')
                return redirect(url_for('goals'))
            
            if daily_fiber < 0 or daily_fiber > 100:
                flash('Please enter a reasonable daily fiber goal (0-100g)', 'error')
                return redirect(url_for('goals'))
            
            # Save goals
            set_nutritional_goals(current_user.id, daily_calories, daily_protein, daily_fiber)
            flash('Nutritional goals updated successfully!', 'success')
            
        except ValueError:
            flash('Please enter valid numbers for your goals', 'error')
            return redirect(url_for('goals'))
        except Exception as e:
            logging.error(f"Error setting goals: {e}")
            flash('An error occurred while updating goals', 'error')
            return redirect(url_for('goals'))
    
    # Get current goals and progress
    user_goals = get_nutritional_goals(current_user.id)
    weekly_data = get_weekly_progress(current_user.id)
    progress_chart = create_progress_chart(weekly_data)
    
    # Get today's progress from the daily data
    today = datetime.now().strftime('%Y-%m-%d')
    today_progress = weekly_data['daily_data'].get(today, {
        'total_calories': 0,
        'total_protein': 0,
        'total_fiber': 0
    })
    
    if user_goals:
        # Calculate percentages
        today_progress['calories_percent'] = (today_progress['total_calories'] / user_goals['daily_calories'] * 100) if user_goals['daily_calories'] else 0
        today_progress['protein_percent'] = (today_progress['total_protein'] / user_goals['daily_protein'] * 100) if user_goals['daily_protein'] else 0
        today_progress['fiber_percent'] = (today_progress['total_fiber'] / user_goals['daily_fiber'] * 100) if user_goals['daily_fiber'] else 0
    
    return render_template('goals.html', 
                         goals=user_goals,
                         progress=weekly_data,
                         today_progress=today_progress,
                         progress_chart=progress_chart)

def create_progress_chart(weekly_data):
    """Create a visualization of weekly progress."""
    if not weekly_data or not weekly_data.get('daily_data'):
        return None
        
    try:
        plt.figure(figsize=(10, 6))
        
        # Extract data from the daily_data dictionary
        dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in weekly_data['dates']]
        daily_data = weekly_data['daily_data']
        
        calories = [daily_data[date]['total_calories'] for date in weekly_data['dates']]
        protein = [daily_data[date]['total_protein'] for date in weekly_data['dates']]
        fiber = [daily_data[date]['total_fiber'] for date in weekly_data['dates']]
        
        # Create subplots for each metric
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
        
        # Plot calories
        ax1.plot(dates, calories, marker='o', linestyle='-', color='#2ecc71')
        ax1.set_title('Weekly Calorie Intake')
        ax1.set_ylabel('Calories')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Add goal line if available
        if weekly_data.get('goals', {}).get('daily_calories'):
            ax1.axhline(y=weekly_data['goals']['daily_calories'], color='r', linestyle='--', alpha=0.5, label='Goal')
            ax1.legend()
        
        # Plot protein
        ax2.plot(dates, protein, marker='o', linestyle='-', color='#3498db')
        ax2.set_title('Weekly Protein Intake')
        ax2.set_ylabel('Protein (g)')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Add goal line if available
        if weekly_data.get('goals', {}).get('daily_protein'):
            ax2.axhline(y=weekly_data['goals']['daily_protein'], color='r', linestyle='--', alpha=0.5, label='Goal')
            ax2.legend()
        
        # Plot fiber
        ax3.plot(dates, fiber, marker='o', linestyle='-', color='#e74c3c')
        ax3.set_title('Weekly Fiber Intake')
        ax3.set_ylabel('Fiber (g)')
        ax3.grid(True, linestyle='--', alpha=0.7)
        
        # Add goal line if available
        if weekly_data.get('goals', {}).get('daily_fiber'):
            ax3.axhline(y=weekly_data['goals']['daily_fiber'], color='r', linestyle='--', alpha=0.5, label='Goal')
            ax3.legend()
        
        # Format x-axis for all subplots
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot to a temporary buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close('all')
        
        # Convert plot to base64 string
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        logging.error(f"Error creating progress chart: {e}")
        return None

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
