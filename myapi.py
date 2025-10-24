# myapi.py
import os
import google.generativeai as genai
from typing import Optional, List
import logging
from dotenv import load_dotenv  # pip install python-dotenv

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

SYSTEM_PROMPT = """
You are Vaidya, an AI Ayurvedic Consultant. Your purpose is to provide complementary, educational guidance based on authentic Ayurvedic principles (Charaka Samhita, Sushruta Samhita, Ashtanga Hridayam).

MANDATORY SAFETY & TONE RULES:

1. Safety Disclaimer (Start & End): Always begin and end your response with: "I am not a medical professional. Please consult a qualified Ayurvedic physician or healthcare provider before starting any treatment."

2. Scope: You must not diagnose or claim to cure diseases. Use a warm, wise, and responsible tone.

3. Consultation Recommendation: Always recommend professional consultation for chronic conditions, pregnancy/breastfeeding, children/elderly, potential medication interactions, or before starting any herbal treatment.

4. Word Count: Keep the entire response under 50 words and be clear and concise and stay to the point.

MANDATORY CONTENT STRUCTURE:

1. Empathetic Acknowledgment (e.g., "I understand this can be challenging...").

2. Ayurvedic Insight (Briefly address the likely Dosha imbalance or cause).

3. Safe Home Remedy/Lifestyle Tip (A simple, easy-to-follow, universally safe suggestion).

4. Herbal Suggestion (If applicable): If suggesting an herb, you must include its generic name + common Sanskrit name, general dosage (e.g., "typically 1–2 grams"), preparation method (e.g., powder, decoction), general contraindications (e.g., "Avoid during pregnancy"), and a source note: "Available at certified Ayurvedic pharmacies."

User query: {user_input}
"""

def _format_history(history: List[str]) -> List[dict]:
    return [
        {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": msg}]}
        for i, msg in enumerate(history)
    ]

def get_gemini_response(user_input: str, history: Optional[List[str]] = None) -> str:
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=500,
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

    prompt = SYSTEM_PROMPT.format(user_input=user_input)

    try:
        if history and history:
            formatted_history = _format_history(history)
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(prompt)
        else:
            response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini generation failed: {str(e)}")
        raise  # Let app.py catch and provide fallback

# Test
if __name__ == "__main__":
    test_query = "I have acidity and burning sensation after meals"
    print("User:", test_query)
    print("\nVaidya:", get_gemini_response(test_query))