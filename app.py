# app.py
from flask import Flask, render_template, request, jsonify, session, send_file
from myapi import get_gemini_response
import os
import json
import logging
import pathlib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from io import BytesIO
from markupsafe import escape

# Load .env
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key-2025")

# In-memory chat history
chat_histories = {}

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
    return session['session_id']

@app.before_request
def check_api_key():
    key_status = "SET" if os.getenv("GOOGLE_API_KEY") else "MISSING"
    logger.info(f"GOOGLE_API_KEY status: {key_status}")

def load_medicines():
    medicines_file = 'data/medicines.json'
    try:
        if os.path.exists(medicines_file):
            with open(medicines_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading medicines: {e}")
        return []
    return []

# ——— ROUTES ———

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ayurvedic-bot')
def bot_page():
    return render_template('bot.html')

@app.route('/marketplace')
def marketplace():
    medicines = load_medicines()
    return render_template('marketplace.html', medicines=medicines)

@app.route('/cart')
def cart_page():
    cart = session.get('cart', [])
    # Safely calculate total, handling potential missing keys or non-numeric prices
    total = 0
    for item in cart:
        try:
            price_str = item.get('price', '₹0').replace('₹', '').replace(',', '')
            total += int(price_str)
        except ValueError:
            logger.warning(f"Invalid price format found in cart: {item.get('price')}")
            pass # Skip item with bad price

    return render_template('cart.html', cart=cart, total=f'{total:,}') # Format total for display

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    name = data.get('name') 
    
    if not name:
        return jsonify({'error': 'Medicine name required'}), 400

    medicines = load_medicines()
    # Find the item details in the loaded medicine list
    item_to_add = next((m for m in medicines if m['medicine_name'] == name), None)
    
    if not item_to_add:
        return jsonify({'error': f'Product "{name}" not found'}), 404

    cart = session.get('cart', [])
    cart.append(item_to_add)
    session['cart'] = cart
    
    return jsonify({
        'message': f'{name} added to cart', 
        'count': len(cart)
    })

# Consolidated and fixed remove_from_cart
@app.route('/api/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    index = data.get('index')
    
    try:
        index = int(index)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid index format'}), 400
    
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        removed_name = escape(cart[index]['medicine_name'])
        cart.pop(index)
        session['cart'] = cart
        return jsonify({'message': f'{removed_name} removed', 'count': len(cart)})
    return jsonify({'error': 'Invalid index'}), 400

@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.get_json()
    name = data.get('name', '').strip()
    address = data.get('address', '').strip()
    mobile = data.get('mobile', '').strip()

    if not all([name, address, mobile]):
        return jsonify({'error': 'All fields required'}), 400
    
# ——— CHAT API ———
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get('message', '').strip()
    session_id = get_session_id()

    if not user_msg:
        return jsonify({'reply': 'Please share your wellness concern.'})

    if session_id not in chat_histories:
        chat_histories[session_id] = []

    history = chat_histories[session_id]
    gemini_history = [
        {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": msg}]}
        for i, msg in enumerate(history)
    ]

    try:
        bot_reply = get_gemini_response(user_msg, gemini_history or None)
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        bot_reply = (
            "Namaste. I am not a medical professional. "
            "I'm experiencing a temporary technical issue. "
            "Please consult a qualified Ayurvedic physician."
        )

    history.extend([user_msg, bot_reply])
    if len(history) > 20:
        history = history[-20:]
    chat_histories[session_id] = history

    return jsonify({'reply': bot_reply})

@app.template_filter('escapejs')
def jinja_escapejs(value):
    return escape(value)

@app.route('/about-team')
def team():
    return render_template('team.html')


@app.route('/library')
def lib():
    return render_template('library.html')

if __name__ == '__main__':
    logger.info("AyurVeda App Starting...")
    app.run(host='0.0.0.0', port=5000, debug=True)