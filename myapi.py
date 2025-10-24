# myapi.py
import os
import google.generativeai as genai
# Removed 'Content' and 'Part' imports entirely to fix the ImportError.
from typing import Optional, List, Dict
import logging
from dotenv import load_dotenv  # pip install python-dotenv

# --- Configuration and Setup ---

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini (fails loudly if key missing)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError(
        "ERROR: GOOGLE_API_KEY not set! "
        "Set it via: export GOOGLE_API_KEY='your-key' or in .env file. "
        "Get a free key from: https://aistudio.google.com/app/apikey"
    )
genai.configure(api_key=api_key)
logger.info("Gemini configured successfully.")

MODEL_NAME = "gemini-2.0-flash"

# --- System Prompt (Set to 150-word limit for feasibility) ---

SYSTEM_PROMPT = """
You are Vaidya, an AI Ayurvedic Consultant. Your purpose is to provide complementary, educational guidance based exclusively on authentic Ayurvedic texts (Charaka Samhita, Sushruta Samhita, Ashtanga Hridayam). Maintain a warm, wise, and responsible tone.

MANDATORY SAFETY RULES:

1. Safety Disclaimer (Start & End): You **must** begin and end the response with the exact phrase: "I am not a medical professional. Please consult a qualified Ayurvedic physician or healthcare provider before starting any treatment."
2. Scope Limit: **Do not diagnose** or claim to cure diseases.
3. Consultation Necessity: Always recommend professional consultation for chronic conditions, pregnancy/breastfeeding, children/elderly, potential medication interactions, or before starting any herbal treatment.
4. Word Count: Keep the entire response **under 150 words** and be clear and concise.

MANDATORY RESPONSE STRUCTURE & CONTENT:

1. Empathetic Acknowledgment.
2. Ayurvedic Insight (Briefly address the likely Dosha imbalance or cause).
3. Safe Home Remedy/Lifestyle Tip.
4. Herbal Suggestion (If applicable): Must include Generic name + Sanskrit name, general dosage (e.g., "typically 1–2 grams"), preparation method, general contraindications, and source note: "Available at certified Ayurvedic pharmacies."

User query: {user_input}
"""

# The problematic _format_history function has been REMOVED because 
# it relied on the unavailable genai.types.Content class, and app.py 
# already pre-formats the history correctly.

# --- Main API Function ---

# Change history type hint to List[Dict] to reflect what app.py sends.
def get_gemini_response(user_input: str, history: Optional[List[Dict]] = None) -> str:
    """
    Generates a response from the Gemini model, handling both single-turn
    and multi-turn chat based on the provided history.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=300, 
            top_p=0.8,
            top_k=40,
        ),
        safety_settings=[
            {
                "category": cat,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            for cat in (
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            )
        ],
    )

    try:
        if history:
            # Multi-turn chat: Use the dictionary history passed from app.py directly.
            # This bypasses the problematic Content object creation.
            chat = model.start_chat(history=history)
            
            # The user_input is sent as the newest message.
            response = chat.send_message(user_input)
        else:
            # Single-turn chat with the full prompt
            prompt = SYSTEM_PROMPT.format(user_input=user_input)
            response = model.generate_content(prompt)
            
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini generation failed: {str(e)}")
        raise  

# --- Test Execution (Only runs when executed directly) ---

if __name__ == "__main__":
    # Example of a single-turn query
    test_query_1 = "I have acidity and burning sensation after meals"
    print("--- Test 1 (Single-Turn) ---")
    print("User:", test_query_1)
    # The system prompt ensures the response structure is followed
    print("\nVaidya:", get_gemini_response(test_query_1))

    # Example of a multi-turn query (simulated history)
    # NOTE: The history here must match the dictionary format app.py generates
    simulated_history_dict = [
        {"role": "user", "parts": [{"text": "I feel tired all the time."}]},
        {"role": "model", "parts": [{"text": "I am not a medical professional. Please consult a qualified Ayurvedic physician or healthcare provider before starting any treatment. I understand your fatigue. This generally points to an imbalance of **Kapha** and possibly low **Agni** (digestive fire). Try practicing **Surya Namaskar** (Sun Salutations) every morning to ignite Agni. For a simple remedy, boil a slice of fresh ginger and drink the tea. Available at certified Ayurvedic pharmacies. Consult an Ayurvedic physician before starting any treatment."}]},
    ]
    test_query_2 = "What should I eat to balance Kapha then?"
    print("\n--- Test 2 (Multi-Turn Continuation) ---")
    print("User:", test_query_2)
    # This test case simulates the data structure sent from app.py
    print("\nVaidya:", get_gemini_response(test_query_2, history=simulated_history_dict))