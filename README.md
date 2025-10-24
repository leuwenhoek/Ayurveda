# 🌿 AyurVaidya: AI Ayurvedic Consultant

## Project Overview

**AyurVaidya** is a Flask web application that serves as a **complementary, educational Ayurvedic consultant**. It utilizes the **Gemini API** with a highly customized system prompt to deliver structured, safe, and context-aware wellness advice based on traditional Ayurvedic principles (Charaka Samhita, Sushruta Samhita, Ashtanga Hridayam).

The application is built with a strong focus on **user safety**, enforcing mandatory disclaimers and professional consultation recommendations in every AI response.

## ✨ Features

* **Custom AI Persona (`Vaidya`):** The AI is strictly constrained by a detailed system prompt (`myapi.py`) to maintain a warm, wise, and responsible tone while adhering to all Ayurvedic safety guidelines.
* **Safety-Constrained Responses:** Every response is automatically framed with mandatory disclaimers and adheres to a strict **150-word limit** to ensure conciseness and responsible guidance.
* **Structured Consultation:** AI advice is delivered in a fixed, easy-to-read format:
    1.  Empathetic Acknowledgment.
    2.  Ayurvedic Insight (Dosha/Cause).
    3.  Safe Home Remedy/Lifestyle Tip.
    4.  Responsible Herbal Suggestion (with dosage and contraindications).
* **Conversational Chat:** Maintains chat history across turns using Flask sessions, allowing for contextual, multi-turn consultations.
* **E-commerce Integration:** Includes front-end routes for a **Marketplace** and **Shopping Cart** to display and manage related products (data sourced from `data/medicines.json`).

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

* Python 3.8+
* A **Google API Key** for the Gemini API.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd AyurVaidya

2. Setup Environment
Create a Python virtual environment and activate it:

Bash

python -m venv .venv
source .venv/bin/activate   # On Linux/macOS
.venv\Scripts\activat