import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Load the local health database ---
with open('database.json', 'r', encoding='utf-8') as f:
    health_data = json.load(f)

# In-memory session storage for multi-turn conversation
user_sessions = {}

# --- Language Translations ---
translations = {
    "en": {
        "welcome": "Hello! I am MO Swasthya Saathi 🙏\nPlease select your language:\n1. English\n2. ଓଡ଼ିଆ (Odia)",
        "menu": "How can I help you?\n1. Check Symptoms\n2. Health Alerts\n3. Vaccination Info",
        "symptom_prompt": "Please describe your symptoms. For example: 'I have fever, headache, and a cough'.",
        "alert_info": "Current Health Alert for Bhubaneswar: Increased Dengue cases reported. Please ensure there is no stagnant water near your home.",
        "vaccine_info": health_data.get("vaccination_schedule_en", "Vaccination info not found."),
        "no_diagnosis": "I could not identify a specific condition from those symptoms. For accurate advice, please consult a doctor.",
        "consult_doctor": "Please note: This is not a medical diagnosis. You should consult with a real doctor.",
        "error": "Sorry, an error occurred. Please try again later."
    },
    "or": {
        "welcome": "ନମସ୍କାର! ମୁଁ MO ସ୍ୱାସ୍ଥ୍ୟ ସାଥୀ 🙏\nଦୟାକରି ଆପଣଙ୍କ ଭାଷା ବାଛନ୍ତୁ:\n1. English\n2. ଓଡ଼ିଆ",
        "menu": "ମୁଁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?\n1. ଲକ୍ଷଣ ଯାଞ୍ଚ କରନ୍ତୁ\n2. ସ୍ୱାସ୍ଥ୍ୟ ସତର୍କତା\n3. ଟୀକାକରଣ ସୂଚନା",
        "symptom_prompt": "ଦୟାକରି ଆପଣଙ୍କ ଲକ୍ଷଣ ବର୍ଣ୍ଣନା କରନ୍ତୁ। ଉଦାହରଣ: 'ମୋତେ ଜ୍ୱର, ମୁଣ୍ଡବିନ୍ଧା, ଏବଂ କାଶ ଅଛି'।",
        "alert_info": "ଭୁବନେଶ୍ୱର ପାଇଁ ସ୍ୱାସ୍ଥ୍ୟ ସତର୍କତା: ଡେଙ୍ଗୁ ମାମଲା ବୃଦ୍ଧି ପାଇଛି। ଦୟାକରି ଆପଣଙ୍କ ଘର ପାଖରେ ପାଣି ଜମା ନହେବାକୁ ଦିଅନ୍ତୁ।",
        "vaccine_info": health_data.get("vaccination_schedule_or", "ଟୀକାକରଣ ସୂଚନା ମିଳିଲା ନାହିଁ।"),
        "no_diagnosis": "ଏହି ଲକ୍ଷଣଗୁଡିକରୁ ମୁଁ କୌଣସି ନିର୍ଣ୍ଣୟ କରିପାରିଲି ନାହିଁ। ସଠିକ୍ ପରାମର୍ଶ ପାଇଁ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।",
        "consult_doctor": "ଦୟାକରି ଧ୍ୟାନ ଦିଅନ୍ତୁ: ଏହା ଏକ ଡାକ୍ତରୀ ନିରାକରଣ ନୁହେଁ। ସଠିକ୍ ପରାମର୍ଶ ପାଇଁ ଆପଣ ଜଣେ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରିବା ଉଚିତ୍।",
        "error": "କ୍ଷମା କରନ୍ତୁ, ଏକ ତ୍ରୁଟି ଘଟିଛି। ଦୟାକରି ପରେ ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।"
    }
}

def get_diagnosis_from_db(symptoms_text, lang):
    """Function to diagnose symptoms based on the local JSON database."""
    user_symptoms = set(symptoms_text.lower().replace("and", "").replace(",", "").split())
    
    best_match = None
    max_matches = 0

    for disease, data in health_data.get('diseases', {}).items():
        disease_symptoms = set(data['symptoms_en'])
        matches = len(user_symptoms.intersection(disease_symptoms))
        
        if matches > max_matches:
            max_matches = matches
            best_match = disease

    if max_matches > 0:
        disease_info = health_data['diseases'][best_match]
        if lang == 'or':
            response = (
                f"ଲକ୍ଷଣ ଅନୁଯାୟୀ, ଆପଣଙ୍କୁ '{disease_info['name_or']}' ହୋଇପାରେ।\n\n"
                f"*ପ୍ରତିରୋଧ*: {disease_info['prevention_or']}\n"
                f"*ଚିକିତ୍ସା*: {disease_info['treatment_or']}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        else: # Default to English
            response = (
                f"Based on your symptoms, the potential issue could be '{best_match.replace('_', ' ').title()}'.\n\n"
                f"*Prevention*: {disease_info['prevention_en']}\n"
                f"*Treatment*: {disease_info['treatment_en']}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        return response
    
    return translations[lang]['no_diagnosis']

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook to handle incoming WhatsApp messages."""
    incoming_msg = request.values.get('Body', '').lower().strip()
    from_number = request.values.get('From')
    
    twiml_response = MessagingResponse()
    response_text = ""

    session = user_sessions.get(from_number, {"lang": None, "state": "start"})
    
    if session["state"] == "start":
        response_text = translations["en"]["welcome"]
        session["state"] = "lang_select"
    elif session["state"] == "lang_select":
        if "1" in incoming_msg:
            session["lang"] = "en"
            session["state"] = "main_menu"
            response_text = translations["en"]["menu"]
        elif "2" in incoming_msg:
            session["lang"] = "or"
            session["state"] = "main_menu"
            response_text = translations["or"]["menu"]
        else:
            response_text = translations["en"]["welcome"]
    elif session["state"] == "main_menu":
        lang = session["lang"]
        if "1" in incoming_msg:
            response_text = translations[lang]["symptom_prompt"]
            session["state"] = "symptom_check"
        elif "2" in incoming_msg:
            response_text = translations[lang]["alert_info"]
        elif "3" in incoming_msg:
            response_text = translations[lang]["vaccine_info"]
        else:
            response_text = translations[lang]["menu"]
    elif session["state"] == "symptom_check":
        lang = session["lang"]
        diagnosis_result = get_diagnosis_from_db(incoming_msg, lang)
        response_text = diagnosis_result
        session["state"] = "main_menu" # Reset state for the next command
    
    user_sessions[from_number] = session
    twiml_response.message(response_text)
    return str(twiml_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
