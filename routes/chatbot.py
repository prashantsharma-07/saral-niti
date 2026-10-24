# backend/routes/chatbot.py
# Person 4 — Rule-based chatbot backend

from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint('chatbot', __name__)

# Simple rule-based response map
RULES = {
    "hello": "Namaste! 🙏 I am Saral Niti Bot. I can help you find government schemes. Try asking: 'schemes for farmers' or 'schemes for women'.",
    "hi": "Namaste! 🙏 How can I help you today? Ask me about government schemes.",
    "help": "You can ask me things like:\n- Schemes for farmers\n- Schemes for students\n- Schemes for women\n- What is PM Kisan?",
    "farmer": "Here are some schemes for farmers:\n1. PM-KISAN — ₹6000/year income support\n2. Pradhan Mantri Fasal Bima Yojana — crop insurance\n3. Kisan Credit Card — easy credit access",
    "student": "Here are some schemes for students:\n1. National Scholarship Portal — multiple scholarships\n2. PM Vidya Lakshmi — education loans\n3. Post Matric Scholarship — for SC/ST students",
    "women": "Here are some schemes for women:\n1. Beti Bachao Beti Padhao\n2. Ujjwala Yojana — free LPG connection\n3. PM Matru Vandana Yojana — maternity benefit",
    "health": "Here are health-related schemes:\n1. Ayushman Bharat — free health cover up to ₹5 lakh\n2. Janani Suraksha Yojana — safe motherhood\n3. PM Jan Arogya Yojana",
    "rural area": "Here are key schemes for rural areas:\n1. PM Awas Yojana Gramin — housing for rural poor\n2. MGNREGA — 100 days guaranteed rural employment\n3. PM Gram Sadak Yojana — rural road connectivity\n4. PM-KISAN — financial support for rural farmers",
    "rural": "Here are key schemes for rural areas:\n1. PM Awas Yojana Gramin — housing for rural poor\n2. MGNREGA — 100 days guaranteed rural employment\n3. PM Gram Sadak Yojana — rural road connectivity\n4. PM-KISAN — financial support for rural farmers",
    "pm kisan": "PM-KISAN gives ₹6000/year to eligible farmers in 3 installments of ₹2000. You can apply at pmkisan.gov.in",
    "ayushman": "Ayushman Bharat Yojana provides health insurance cover of up to ₹5 lakh per family per year for hospitalisation.",
    "bye": "Thank you for using Saral Niti! Jai Hind 🇮🇳",
    "thanks": "You're welcome! Is there anything else I can help you with?"
}

DEFAULT_RESPONSE = "I'm not sure about that. Try asking about schemes for farmers, women, students, or health. Type 'help' for more options."


@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot_reply():
    """Rule-based chatbot endpoint"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data['message'].lower().strip()

    # Match rules
    reply = DEFAULT_RESPONSE
    for keyword, response in RULES.items():
        if keyword in user_message:
            reply = response
            break

    return jsonify({
        "reply": reply,
        "bot": "Saral Niti Bot"
    }), 200