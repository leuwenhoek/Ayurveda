# app.py - Updated with /marketplace route loading from data/medicines.json

from flask import Flask, render_template, request, jsonify, session
from myapi import get_gemini_response
import os
import json
from dotenv import load_dotenv
import logging
import pathlib

# Load .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# In-memory chat history (use Redis/DB in production)
chat_histories = {}

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
    return session['session_id']

@app.before_request
def check_api_key():
    """Log API key status without exposing the key"""
    key_status = "SET" if os.getenv("GOOGLE_API_KEY") else "MISSING"
    logger.info(f"GOOGLE_API_KEY status: {key_status}")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ayurvedic-bot')
def bot_page():
    return render_template('bot.html')

@app.route('/marketplace')
def marketplace():
    """Load medicines from data/medicines.json and render marketplace.html"""
    medicines_file = 'data/medicines.json'
    medicines = []
    
    try:
        if os.path.exists(medicines_file):
            with open(medicines_file, 'r', encoding='utf-8') as f:
                medicines = json.load(f)
            logger.info(f"Loaded {len(medicines)} medicines from {medicines_file}")
        else:
            logger.warning(f"{medicines_file} not found. Create it with sample data.")
            medicines = []  # Empty list if file missing
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {medicines_file}: {e}")
        medicines = []
    except Exception as e:
        logger.error(f"Error loading {medicines_file}: {e}")
        medicines = []
    
    return render_template('marketplace.html', medicines=medicines)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get('message', '').strip()
    session_id = get_session_id()

    if not user_msg:
        return jsonify({'reply': 'Please share your wellness concern.'})

    # Initialize session history
    if session_id not in chat_histories:
        chat_histories[session_id] = []

    history = chat_histories[session_id]

    # Format history for Gemini
    gemini_history = [
        {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": msg}]}
        for i, msg in enumerate(history)
    ]

    try:
        logger.info(f"Querying Gemini for: {user_msg[:50]}...")
        bot_reply = get_gemini_response(user_msg, gemini_history or None)
        logger.info("Gemini response received successfully.")
    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        bot_reply = (
            "Namaste. I am not a medical professional. "
            "I'm experiencing a temporary technical issue. "
            "Please consult a qualified Ayurvedic physician for personalized guidance. "
            "For general wellness, try sipping warm water with a pinch of ginger in the morning."
        )

    # Update history
    history.extend([user_msg, bot_reply])
    if len(history) > 20:
        history = history[-20:]
    chat_histories[session_id] = history

    return jsonify({'reply': bot_reply})

if __name__ == '__main__':
    logger.info("Starting AyurVeda Flask app...")
    logger.info("Ensure GOOGLE_API_KEY is set via export or .env file.")
    app.run(host='0.0.0.0', port=5000, debug=True)