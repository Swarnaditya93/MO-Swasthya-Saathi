import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Load the health database ---
with open('database.json', 'r', encoding='utf-8') as f:
    health_data = json.load(f)

# --- Keywords for different languages ---
# These help the bot understand transliterated (Roman script) inputs
HINDI_SYMPTOM_KEYWORDS = ['bukhar', 'khansi', 'sirdard', 'dard', 'thakan', 'ulti', 'chakkar']
ODIA_SYMPTOM_KEYWORDS = ['jwara', 'kasa', 'mundabindha', 'jantrana', 'durbalata', 'banti', 'mundabuleiba']
GREETINGS = ["hi", "hello", "namaste", "namaskar", "kemitichanti", "kemiti achha", "नमस्ते", "ନମସ୍କାର"]

def format_disease_info(disease_data):
    """Formats the disease information into a single trilingual message."""
    return (
        f"*{disease_data['name_en']}*\n"
        f"Symptoms: {', '.join(disease_data['symptoms_en']).title()}\n"
        f"Prevention: {disease_data['prevention_en']}\n\n"
        
        f"*{disease_data['name_hi']}*\n"
        f"लक्षण: {disease_data['prevention_hi']}\n"
        f"रोकथाम: {disease_data['treatment_hi']}\n\n"

        f"*{disease_data['name_or']}*\n"
        f"ଲକ୍ଷଣ: {disease_data['prevention_or']}\n"
        f"ପ୍ରତିରୋଧ: {disease_data['treatment_or']}\n\n"
        
        "_Please note: This is not a medical diagnosis. You should consult with a real doctor._"
    )

def process_user_input(text):
    """Analyzes user input to see if it's a disease name or a list of symptoms."""
    lower_text = text.lower()
    
    # --- Check 1: Direct Disease Name Match ---
    # This is the highest priority. If a user names a disease, show its info.
    for disease_id, data in health_data.get('diseases', {}).items():
        if (lower_text in data['name_en'].lower() or
            lower_text in data['name_hi'].lower() or
            lower_text in data['name_or'].lower()):
            return format_disease_info(data)

    # --- Check 2: Symptom Analysis ---
    user_symptoms = set(lower_text.replace("and", "").replace(",", "").split())
    
    # Add transliterated keywords to the user's symptoms for better matching
    for word in user_symptoms:
        if word in HINDI_SYMPTOM_KEYWORDS:
            user_symptoms.update(['fever', 'cough', 'headache', 'pain', 'fatigue', 'vomiting', 'dizziness'])
        if word in ODIA_SYMPTOM_KEYWORDS:
             user_symptoms.update(['fever', 'cough', 'headache', 'pain', 'fatigue', 'vomiting', 'dizziness'])

    best_match_disease_id = None
    max_matches = 0

    for disease_id, data in health_data.get('diseases', {}).items():
        disease_symptoms_en = set(data['symptoms_en'])
        matches = len(user_symptoms.intersection(disease_symptoms_en))
        
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
        "ମୁଁ ଦୁଃଖିତ, ମୁଁ ତାହା ବୁଝିପାରିଲି ନାହିଁ। ଦୟାକରି ମୋତେ ଆପଣଙ୍କର ଲକ୍ଷଣ (ଯେପରିକି 'ଜ୍ୱର ଏବଂ ମୁଣ୍ଡବିନ୍ଧା') କିମ୍ବା ଆପଣ ଜାଣିବାକୁ ଚାହୁଁଥିବା ରୋଗର ନାମ (ଯେପରିକି 'ଡେଙ୍ଗୁ') କୁହନ୍ତୁ।\n\n"
        "मुझे क्षमा करें, मैं यह समझ नहीं सका। कृपया मुझे अपने लक्षण बताएं (उदाहरण: 'बुखार और सिरदर्द') या उस बीमारी का नाम बताएं जिसके बारे में आप जानना चाहते हैं (उदाहरण: 'डेंगू')।"
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook to handle incoming WhatsApp messages."""
    incoming_msg = request.values.get('Body', '').strip()
    twiml_response = MessagingResponse()
    response_text = ""

    # Check if the message is a greeting
    if incoming_msg.lower() in GREETINGS:
        response_text = (
            "Hello! I am MO Swasthya Saathi 🙏\n"
            "You can tell me your symptoms or ask about a specific disease.\n\n"
            "नमस्ते! मैं मो स्वास्थ्य साथी हूँ 🙏\n"
            "आप मुझे अपने लक्षण बता सकते हैं या किसी विशिष्ट बीमारी के बारे में पूछ सकते हैं।\n\n"
            "ନମସ୍କାର! ମୁଁ MO ସ୍ୱାସ୍ଥ୍ୟ ସାଥୀ 🙏\n"
            "ଆପଣ ମୋତେ ଆପଣଙ୍କର ଲକ୍ଷଣ କହିପାରିବେ କିମ୍ବା ଏକ ନିର୍ଦ୍ଦିଷ୍ଟ ରୋଗ ବିଷୟରେ ପଚାରିପାରିବେ।"
        )
    else:
        # If not a greeting, process the input for symptoms or disease name
        response_text = process_user_input(incoming_msg)
    
    twiml_response.message(response_text)
    return str(twiml_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

