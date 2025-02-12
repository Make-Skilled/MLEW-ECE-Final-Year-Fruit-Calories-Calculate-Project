from flask import Flask, render_template, request
from tensorflow.keras.models import load_model # type: ignore
from PIL import Image, ImageOps
import numpy as np
import logging
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load the trained model
try:
    model = load_model("keras_Model.h5", compile=False)
    logging.info("Model loaded successfully")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    raise e

# Load the class labels
try:
    with open("labels.txt", "r") as file:
        class_names = [line.strip().split(" ", 1)[-1] for line in file.readlines()]
    logging.info("Class labels loaded successfully")
except Exception as e:
    logging.error(f"Error loading class labels: {e}")
    raise e

# Updated estimated calories per fruit
calories_per_fruit = {
    "ACEROLAS": 32, "APPLES": 52, "APRICOTS": 48, "AVOCADOS": 160, "BANANAS": 89,
    "BACKBERRIES": 43, "BLUEBERRIES": 57, "CANALOUPES": 34, "CHERRIES": 50, "COCONUTS": 354,
    "FIGS": 74, "GRAPEFRUITS": 42, "GAPES": 69, "GUAVA": 68, "KIWIFRUIT": 61,
    "LEMONS": 29, "LIMES": 30, "MANGOES": 60, "OLIVES": 115, "ORANGES": 47,
    "PASSIONFRUIT": 97, "PEACHES": 39, "PEARS": 57, "PINEAPPLES": 50, "PLUMS": 46,
    "POMEGRANATES": 83, "RASPBERRIES": 52, "STRAWBERRIES": 32, "WATERMELONS": 30
}

# Home route
@app.route('/')
def index():
    return render_template('index.html', prediction=None)

# Image prediction route
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return render_template('index.html', prediction="No image file found.")

    image = request.files['image']

    try:
        # Open and process the image
        image = Image.open(image).convert("RGB")
        image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)

        # Convert image to numpy array and normalize
        image_array = np.asarray(image, dtype=np.float32)
        normalized_image_array = (image_array / 127.5) - 1

        # Prepare input data for model
        data = np.expand_dims(normalized_image_array, axis=0)

        # Make prediction
        prediction = model.predict(data)
        index = np.argmax(prediction)
        class_name = class_names[index]
        confidence_score = float(prediction[0][index])

        # Get calories for predicted fruit
        calories = calories_per_fruit.get(class_name, "Unknown")

        return render_template(
            'index.html',
            class_name=class_name,
            calories=calories
        )

    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return render_template('index.html', prediction="An error occurred. Please try again.")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
