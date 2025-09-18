import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Load the health database ---
with open('database.json', 'r', encoding='utf-8') as f:
    health_data = json.load(f)

# --- Transliteration Mapping ---
# Correctly maps Roman script words to their English symptom keyword.
TRANSLITERATION_MAP = {
    # Hindi
    'bukhar': 'fever', 'khansi': 'cough', 'sirdard': 'headache', 'dard': 'pain',
    'thakan': 'fatigue', 'ulti': 'vomiting', 'chakkar': 'dizziness',
    # Odia
    'jwara': 'fever', 'kasa': 'cough', 'mundabindha': 'headache', 'jantrana': 'pain',
    'durbalata': 'weakness', 'banti': 'vomiting', 'mundabuleiba': 'dizziness'
}

GREETINGS = ["hi", "hello", "namaste", "namaskar", "kemitichanti", "kemiti achha", "नमस्ते", "ନମସ୍କାର"]

def format_disease_info(disease_data):
    """Formats the disease information into a single trilingual message with corrected fields."""
    # The symptom keywords are in English in the database, so we display them for all languages.
    symptoms_list_en = ', '.join(disease_data['symptoms_en']).title()
    
    return (
        f"*{disease_data['name_en']}*\n"
        f"Symptoms: {symptoms_list_en}\n"
        f"Prevention: {disease_data['prevention_en']}\n"
        f"Treatment: {disease_data['treatment_en']}\n\n"
        
        f"*{disease_data['name_hi']}*\n"
        f"लक्षण (Symptoms): {symptoms_list_en}\n"
        f"रोकथाम (Prevention): {disease_data['prevention_hi']}\n"
        f"उपचार (Treatment): {disease_data['treatment_hi']}\n\n"

        f"*{disease_data['name_or']}*\n"
        f"ଲକ୍ଷଣ (Symptoms): {symptoms_list_en}\n"
        f"ପ୍ରତିରୋଧ (Prevention): {disease_data['prevention_or']}\n"
        f"ଚିକିତ୍ସା (Treatment): {disease_data['treatment_or']}\n\n"
        
        "_Please note: This is not a medical diagnosis. Consult a doctor for accurate advice._"
    )

def process_user_input(text):
    """Analyzes user input to find a disease by name or by symptoms."""
    lower_text = text.lower()
    
    # --- Check 1: Direct Disease Name Match ---
    for disease_id, data in health_data.get('diseases', {}).items():
        if (lower_text == data['name_en'].lower() or
            lower_text == data['name_hi'].lower() or
            lower_text == data['name_or'].lower()):
            return format_disease_info(data)

    # --- Check 2: Symptom Analysis ---
    words = set(lower_text.replace("and", "").replace(",", "").split())
    
    # Convert any transliterated words to their English equivalent
    user_symptoms_en = set()
    for word in words:
        if word in TRANSLITERATION_MAP:
            user_symptoms_en.add(TRANSLITERATION_MAP[word])
        else:
            user_symptoms_en.add(word)

    best_match_disease_id = None
    max_matches = 0

    for disease_id, data in health_data.get('diseases', {}).items():
        disease_symptoms_en = set(data['symptoms_en'])
        matches = len(user_symptoms_en.intersection(disease_symptoms_en))
        
        if matches > max_matches:
            max_matches = matches
            best_match_disease_id = disease_id
    
    # Require at least one symptom match to provide a diagnosis
    if max_matches > 0:
        matched_disease_data = health_data['diseases'][best_match_disease_id]
        return format_disease_info(matched_disease_data)
        
    # --- Check 3: If nothing matches ---
    return (
        "I'm sorry, I couldn't understand that. Please tell me your symptoms (e.g., 'fever and headache') or the name of a disease you want to know about (e.g., 'Dengue').\n\n"
        "मुझे क्षमा करें, मैं यह समझ नहीं सका। कृपया मुझे अपने लक्षण बताएं (उदाहरण: 'बुखार और सिरदर्द') या उस बीमारी का नाम बताएं जिसके बारे में आप जानना चाहते हैं (उदाहरण: 'डेंगू')।\n\n"
        "ମୁଁ ଦୁଃଖିତ, ମୁଁ ତାହା ବୁଝିପାରିଲି ନାହିଁ। ଦୟାକରି ମୋତେ ଆପଣଙ୍କର ଲକ୍ଷଣ (ଯେପରିକି 'ଜ୍ୱର ଏବଂ ମୁଣ୍ଡବିନ୍ଧା') କିମ୍ବା ଆପଣ ଜାଣିବାକୁ ଚାହୁଁଥିବା ରୋଗର ନାମ (ଯେପରିକି 'ଡେଙ୍ଗୁ') କୁହନ୍ତୁ।"
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook to handle incoming WhatsApp messages."""
    incoming_msg = request.values.get('Body', '').strip()
    twiml_response = MessagingResponse()
    response_text = ""

    if not incoming_msg:
        # Handle empty messages gracefully
        response_text = "Please send a message."
    elif incoming_msg.lower() in GREETINGS:
        response_text = (
            "Hello! I am MO Swasthya Saathi 🙏\n"
            "You can tell me your symptoms or ask about a specific disease.\n\n"
            "नमस्ते! मैं मो स्वास्थ्य साथी हूँ 🙏\n"
            "आप मुझे अपने लक्षण बता सकते हैं या किसी विशिष्ट बीमारी के बारे में पूछ सकते हैं।\n\n"
            "ନମସ୍କାର! ମୁଁ MO ସ୍ୱାସ୍ଥ୍ୟ ସାଥୀ 🙏\n"
            "ଆପଣ ମୋତେ ଆପଣଙ୍କର ଲକ୍ଷଣ କହିପାରିବେ କିମ୍ବା ଏକ ନିର୍ଦ୍ଦିଷ୍ଟ ରୋଗ ବିଷୟରେ ପଚାରିପାରିବେ।"
        )
    else:
        response_text = process_user_input(incoming_msg)
    
    twiml_response.message(response_text)
    return str(twiml_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

