import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Load the health database ---
# This code assumes you have a 'database.json' file in the same directory.
with open('database.json', 'r', encoding='utf-8') as f:
    health_data = json.load(f)

# In-memory session storage for multi-turn conversation
user_sessions = {}

# --- Trilingual Translations ---
translations = {
    "en": {
        "welcome": "Hello! I am MO Swasthya Saathi 🙏\nPlease select your language:\n1. English\n2. हिंदी (Hindi)\n3. ଓଡ଼ିଆ (Odia)",
        "menu": "How can I help you?\n1. Check Symptoms\n2. Health Alerts\n3. Vaccination Info\n\n(You can type 'menu' anytime to return here)",
        "symptom_prompt": "Please describe your symptoms. For example: 'I have fever, headache, and a cough'.",
        "alert_info": "Current Health Alert for Bhubaneswar: Increased Dengue cases reported. Please ensure there is no stagnant water near your home.",
        "vaccine_info": health_data.get("vaccination_schedule_en", "Vaccination info not found."),
        "no_diagnosis": "I could not identify a specific condition from those symptoms. For accurate advice, please consult a doctor.",
        "consult_doctor": "Please note: This is not a medical diagnosis. You should consult with a real doctor.",
        "error": "Sorry, an error occurred. Please try again later."
    },
    "hi": {
        "welcome": "नमस्ते! मैं हूँ मो स्वास्थ्य साथी 🙏\nकृपया अपनी भाषा चुनें:\n1. English\n2. हिंदी\n3. ଓଡ଼ିଆ (Odia)",
        "menu": "मैं आपकी कैसे मदद कर सकता हूँ?\n1. लक्षण जांचें\n2. स्वास्थ्य अलर्ट\n3. टीकाकरण की जानकारी\n\n(आप कभी भी 'menu' टाइप करके यहां लौट सकते हैं)",
        "symptom_prompt": "कृपया अपने लक्षण बताएं। उदाहरण: 'मुझे बुखार, सिरदर्द और खांसी है।'",
        "alert_info": "भुवनेश्वर के लिए स्वास्थ्य अलर्ट: डेंगू के मामले बढ़े हैं। कृपया सुनिश्चित करें कि आपके घर के पास पानी जमा न हो।",
        "vaccine_info": health_data.get("vaccination_schedule_hi", "टीकाकरण की जानकारी नहीं मिली।"),
        "no_diagnosis": "मैं इन लक्षणों से किसी विशेष स्थिति की पहचान नहीं कर सका। सटीक सलाह के लिए, कृपया डॉक्टर से परामर्श लें।",
        "consult_doctor": "कृपया ध्यान दें: यह एक चिकित्सीय निदान नहीं है। आपको एक वास्तविक डॉक्टर से परामर्श करना चाहिए।",
        "error": "क्षमा करें, एक त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।"
    },
    "or": {
        "welcome": "ନମସ୍କାର! ମୁଁ MO ସ୍ୱାସ୍ଥ୍ୟ ସାଥୀ 🙏\nଦୟାକରି ଆପଣଙ୍କ ଭାଷା ବାଛନ୍ତୁ:\n1. English\n2. हिंदी (Hindi)\n3. ଓଡ଼ିଆ",
        "menu": "ମୁଁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?\n1. ଲକ୍ଷଣ ଯାଞ୍ଚ କରନ୍ତୁ\n2. ସ୍ୱାସ୍ଥ୍ୟ ସତର୍କତା\n3. ଟୀକାକରଣ ସୂଚନା\n\n(ଆପଣ ଯେକୌଣସି ସମୟରେ 'menu' ଟାଇପ୍ କରି ଏଠାକୁ ଫେରିପାରିବେ)",
        "symptom_prompt": "ଦୟାକରି ଆପଣଙ୍କ ଲକ୍ଷଣ ବର୍ଣ୍ଣନା କରନ୍ତୁ। ଉଦାହରଣ: 'ମୋତେ ଜ୍ୱର, ମୁଣ୍ଡବିନ୍ଧା, ଏବଂ କାଶ ଅଛି'।",
        "alert_info": "ଭୁବନେଶ୍ୱର ପାଇଁ ସ୍ୱାସ୍ଥ୍ୟ ସତର୍କତା: ଡେଙ୍ଗୁ ମାମଲା ବୃଦ୍ଧି ପାଇଛି। ଦୟାକରି ଆପଣଙ୍କ ଘର ପାଖରେ ପାଣି ଜମା ନହେବାକୁ ଦିଅନ୍ତୁ।",
        "vaccine_info": health_data.get("vaccination_schedule_or", "ଟୀକାକରଣ ସୂଚନା ମିଳିଲା ନାହିଁ।"),
        "no_diagnosis": "ଏହି ଲକ୍ଷଣଗୁଡିକରୁ ମୁଁ କୌଣସି ନିର୍ଣ୍ଣୟ କରିପାରିଲି ନାହିଁ। ସଠିକ୍ ପରାମର୍ଶ ପାଇଁ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।",
        "consult_doctor": "ଦୟାକରି ଧ୍ୟାନ ଦିଅନ୍ତୁ: ଏହା ଏକ ଡାକ୍ତରୀ ନିରାକରଣ ନୁହେଁ। ସଠିକ୍ ପରାମର୍ଶ ପାଇଁ ଆପଣ ଜଣେ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରିବା ଉଚିତ୍।",
        "error": "କ୍ଷମା କରନ୍ତୁ, ଏକ ତ୍ରୁଟି ଘଟିଛି। ଦୟାକରି ପରେ ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।"
    }
}

def get_diagnosis_from_db(symptoms_text, lang):
    """Diagnose symptoms based on keywords from the local JSON database."""
    user_symptoms = set(symptoms_text.lower().replace("and", "").replace(",", "").split())
    
    best_match = None
    max_matches = 0

    # Ensure at least one symptom is provided
    if not user_symptoms:
        return translations[lang]['symptom_prompt']

    for disease, data in health_data.get('diseases', {}).items():
        # Using English symptoms as the base for matching logic
        disease_symptoms = set(data['symptoms_en'])
        matches = len(user_symptoms.intersection(disease_symptoms))
        
        # Prioritize more specific matches
        if matches > max_matches:
            max_matches = matches
            best_match = disease

    if max_matches > 0:
        disease_info = health_data['diseases'][best_match]
        
        if lang == 'hi':
            response = (
                f"लक्षणों के आधार पर, संभावित समस्या '{disease_info['name_hi']}' हो सकती है।\n\n"
                f"*रोकथाम*: {disease_info['prevention_hi']}\n"
                f"*उपचार*: {disease_info['treatment_hi']}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        elif lang == 'or':
            response = (
                f"ଲକ୍ଷଣ ଅନୁଯାୟୀ, ଆପଣଙ୍କୁ '{disease_info['name_or']}' ହୋଇପାରେ।\n\n"
                f"*ପ୍ରତିରୋଧ*: {disease_info['prevention_or']}\n"
                f"*ଚିକିତ୍ସା*: {disease_info['treatment_or']}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        else: # Default to English
            response = (
                f"Based on your symptoms, the potential issue could be '{disease_info['name_en']}'.\n\n"
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

    # Universal command to restart the conversation
    if incoming_msg in ["menu", "restart", "start over", "hi", "hello", "नमस्ते", "ନମସ୍କାର"]:
        user_sessions[from_number] = {"lang": None, "state": "start"}

    session = user_sessions.get(from_number, {"lang": None, "state": "start"})
    
    if session.get("state") == "start":
        response_text = translations["en"]["welcome"]
        session["state"] = "lang_select"
    elif session.get("state") == "lang_select":
        if "1" in incoming_msg or "english" in incoming_msg:
            session["lang"] = "en"
            session["state"] = "main_menu"
            response_text = translations["en"]["menu"]
        elif "2" in incoming_msg or "hindi" in incoming_msg or "हिंदी" in incoming_msg:
            session["lang"] = "hi"
            session["state"] = "main_menu"
            response_text = translations["hi"]["menu"]
        elif "3" in incoming_msg or "odia" in incoming_msg or "ଓଡ଼ିଆ" in incoming_msg:
            session["lang"] = "or"
            session["state"] = "main_menu"
            response_text = translations["or"]["menu"]
        else:
            # If input is invalid, ask again
            response_text = translations["en"]["welcome"]
    elif session.get("state") == "main_menu":
        lang = session.get("lang", "en") # Default to English if language not set
        if "1" in incoming_msg:
            response_text = translations[lang]["symptom_prompt"]
            session["state"] = "symptom_check"
        elif "2" in incoming_msg:
            response_text = translations[lang]["alert_info"]
        elif "3" in incoming_msg:
            response_text = translations[lang]["vaccine_info"]
        else:
            # If input is invalid, show the menu again
            response_text = translations[lang]["menu"]
    elif session.get("state") == "symptom_check":
        lang = session.get("lang", "en")
        diagnosis_result = get_diagnosis_from_db(incoming_msg, lang)
        response_text = diagnosis_result
        # After diagnosis, go back to the main menu to allow further questions
        session["state"] = "main_menu" 
    
    # Save the updated session state
    user_sessions[from_number] = session
    twiml_response.message(response_text)
    return str(twiml_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

