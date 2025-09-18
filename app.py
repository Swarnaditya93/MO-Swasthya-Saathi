import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Load the health database ---
with open('database.json', 'r', encoding='utf-8') as f:
    health_data = json.load(f)

# In-memory session storage for multi-turn conversation
user_sessions = {}

# --- Trilingual Translations ---
translations = {
    "en": {
        "welcome": "Hello! I am MO Swasthya Saathi 🙏\nPlease select your language:\n1. English\n2. हिंदी (Hindi)\n3. ଓଡ଼ିଆ (Odia)",
        "menu": "How can I help you?\n1. Check Symptoms\n2. Health Alerts\n3. Vaccination Info\n4. Search Disease Info\n\n(You can type 'menu' anytime to return here)",
        "symptom_prompt": "Please describe your symptoms. For example: 'I have fever, headache, and a cough'.",
        "symptom_repeat": "You can now check another set of symptoms, or type 'menu' to return to the main menu.",
        "disease_prompt": "Please enter the name of the disease you want to know about (e.g., Malaria).",
        "disease_repeat": "You can now search for another disease, or type 'menu' to return to the main menu.",
        "alert_info": "Current Health Alert for Bhubaneswar: Increased Dengue cases reported. Please ensure there is no stagnant water near your home.",
        "vaccine_info": health_data.get("vaccination_schedule_en", "Vaccination info not found."),
        "no_diagnosis": "I could not identify a specific condition from those symptoms. For accurate advice, please consult a doctor.",
        "disease_not_found": "Sorry, I could not find information about that disease in my database.",
        "consult_doctor": "Please note: This is not a medical diagnosis. You should consult with a real doctor.",
        "error": "Sorry, an error occurred. Please try again later."
    },
    "hi": {
        "welcome": "नमस्ते! मैं हूँ मो स्वास्थ्य साथी 🙏\nकृपया अपनी भाषा चुनें:\n1. English\n2. हिंदी\n3. ଓଡ଼ିଆ (Odia)",
        "menu": "मैं आपकी कैसे मदद कर सकता हूँ?\n1. लक्षण जांचें\n2. स्वास्थ्य अलर्ट\n3. टीकाकरण की जानकारी\n4. रोग की जानकारी खोजें\n\n(आप कभी भी 'menu' टाइप करके यहां लौट सकते हैं)",
        "symptom_prompt": "कृपया अपने लक्षण बताएं। उदाहरण: 'मुझे बुखार, सिरदर्द और खांसी है।'",
        "symptom_repeat": "अब आप लक्षणों का एक और सेट देख सकते हैं, या मुख्य मेनू पर लौटने के लिए 'menu' टाइप करें।",
        "disease_prompt": "कृपया उस रोग का नाम दर्ज करें जिसके बारे में आप जानना चाहते हैं (जैसे, मलेरिया)।",
        "disease_repeat": "अब आप किसी अन्य बीमारी की खोज कर सकते हैं, या मुख्य मेनू पर लौटने के लिए 'menu' टाइप करें।",
        "alert_info": "भुवनेश्वर के लिए स्वास्थ्य अलर्ट: डेंगू के मामले बढ़े हैं। कृपया सुनिश्चित करें कि आपके घर के पास पानी जमा न हो।",
        "vaccine_info": health_data.get("vaccination_schedule_hi", "टीकाकरण की जानकारी नहीं मिली।"),
        "no_diagnosis": "मैं इन लक्षणों से किसी विशेष स्थिति की पहचान नहीं कर सका। सटीक सलाह के लिए, कृपया डॉक्टर से परामर्श लें।",
        "disease_not_found": "क्षमा करें, मुझे मेरे डेटाबेस में उस बीमारी के बारे में जानकारी नहीं मिली।",
        "consult_doctor": "कृपया ध्यान दें: यह एक चिकित्सीय निदान नहीं है। आपको एक वास्तविक डॉक्टर से परामर्श करना चाहिए।",
        "error": "क्षमा करें, एक त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।"
    },
    "or": {
        "welcome": "ନମସ୍କାର! ମୁଁ MO ସ୍ୱାସ୍ଥ୍ୟ ସାଥୀ 🙏\nଦୟାକରି ଆପଣଙ୍କ ଭାଷା ବାଛନ୍ତୁ:\n1. English\n2. हिंदी (Hindi)\n3. ଓଡ଼ିଆ",
        "menu": "ମୁଁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?\n1. ଲକ୍ଷଣ ଯାଞ୍ଚ କରନ୍ତୁ\n2. ସ୍ୱାସ୍ଥ୍ୟ ସତର୍କତା\n3. ଟୀକାକରଣ ସୂଚନା\n4. ରୋଗ ସୂଚନା ଖୋଜନ୍ତୁ\n\n(ଆପଣ ଯେକୌଣସି ସମୟରେ 'menu' ଟାଇପ୍ କରି ଏଠାକୁ ଫେରିପାରିବେ)",
        "symptom_prompt": "ଦୟାକରି ଆପଣଙ୍କ ଲକ୍ଷଣ ବର୍ଣ୍ଣନା କରନ୍ତୁ। ଉଦାହରଣ: 'ମୋତେ ଜ୍ୱର, ମୁଣ୍ଡବିନ୍ଧା, ଏବଂ କାଶ ଅଛି'।",
        "symptom_repeat": "ଆପଣ ବର୍ତ୍ତମାନ ଆଉ ଏକ ଲକ୍ଷଣ ସେଟ୍ ଯାଞ୍ଚ କରିପାରିବେ, କିମ୍ବା ମୁଖ୍ୟ ମେନୁକୁ ଫେରିବାକୁ 'menu' ଟାଇପ୍ କରନ୍ତୁ।",
        "disease_prompt": "ଦୟାକରି ସେହି ରୋଗର ନାମ ଲେଖନ୍ତୁ ଯାହା ବିଷୟରେ ଆପଣ ଜାଣିବାକୁ ଚାହାଁନ୍ତି (ଉଦାହରଣ: ମ୍ୟାଲେରିଆ)।",
        "disease_repeat": "ଆପଣ ବର୍ତ୍ତମାନ ଅନ୍ୟ ଏକ ରୋଗ ଖୋଜି ପାରିବେ, କିମ୍ବା ମୁଖ୍ୟ ମେନୁକୁ ଫେରିବାକୁ 'menu' ଟାଇପ୍ କରନ୍ତୁ।",
        "alert_info": "ଭୁବନେଶ୍ୱର ପାଇଁ ସ୍ୱାସ୍ଥ୍ୟ ସତର୍କତା: ଡେଙ୍ଗୁ ମାମଲା ବୃଦ୍ଧି ପାଇଛି। ଦୟାକରି ଆପଣଙ୍କ ଘର ପାଖରେ ପାଣି ଜମା ନହେବାକୁ ଦିଅନ୍ତୁ।",
        "vaccine_info": health_data.get("vaccination_schedule_or", "ଟୀକାକରଣ ସୂଚନା ମିଳିଲା ନାହିଁ।"),
        "no_diagnosis": "ଏହି ଲକ୍ଷଣଗୁଡିକରୁ ମୁଁ କୌଣସି ନିର୍ଣ୍ଣୟ କରିପାରିଲି ନାହିଁ। ସଠିକ୍ ପରାମର୍ଶ ପାଇଁ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।",
        "disease_not_found": "କ୍ଷମା କରନ୍ତୁ, ମୁଁ ମୋର ଡାଟାବେସରେ ସେହି ରୋଗ ବିଷୟରେ କୌଣସି ସୂଚନା ପାଇଲି ନାହିଁ।",
        "consult_doctor": "ଦୟାକରି ଧ୍ୟାନ ଦିଅନ୍ତୁ: ଏହା ଏକ ଡାକ୍ତରୀ ନିରାକରଣ ନୁହେଁ। ସଠିକ୍ ପରାମର୍ଶ ପାଇଁ ଆପଣ ଜଣେ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରିବା ଉଚିତ୍।",
        "error": "କ୍ଷମା କରନ୍ତୁ, ଏକ ତ୍ରୁଟି ଘଟିଛି। ଦୟାକରି ପରେ ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।"
    }
}

def get_diagnosis_from_db(symptoms_text, lang):
    """Diagnose symptoms based on keywords from the local JSON database."""
    user_symptoms = set(symptoms_text.lower().replace("and", "").replace(",", "").split())
    
    best_match = None
    max_matches = 0

    if not user_symptoms:
        return translations[lang]['symptom_prompt']

    for disease, data in health_data.get('diseases', {}).items():
        disease_symptoms = set(data['symptoms_en'])
        matches = len(user_symptoms.intersection(disease_symptoms))
        
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
        else:
            response = (
                f"Based on your symptoms, the potential issue could be '{disease_info['name_en']}'.\n\n"
                f"*Prevention*: {disease_info['prevention_en']}\n"
                f"*Treatment*: {disease_info['treatment_en']}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        return response
    
    return translations[lang]['no_diagnosis']

def get_disease_info_from_db(disease_name, lang):
    """Search for a disease by name and return its details."""
    search_term = disease_name.lower().strip()
    for disease, data in health_data.get('diseases', {}).items():
        # Check against all language names for a match
        if (search_term in data['name_en'].lower() or 
            search_term in data['name_hi'].lower() or 
            search_term in data['name_or'].lower()):
            
            if lang == 'hi':
                response = (
                    f"*{data['name_hi']}*\n\n"
                    f"*लक्षण*: {', '.join(data['symptoms_en']).title()}\n\n"
                    f"*रोकथाम*: {data['prevention_hi']}\n\n"
                    f"*उपचार*: {data['treatment_hi']}"
                )
            elif lang == 'or':
                response = (
                    f"*{data['name_or']}*\n\n"
                    f"*ଲକ୍ଷଣ*: {', '.join(data['symptoms_en']).title()}\n\n"
                    f"*ପ୍ରତିରୋଧ*: {data['prevention_or']}\n\n"
                    f"*ଚିକିତ୍ସା*: {data['treatment_or']}"
                )
            else: # Default to English
                response = (
                    f"*{data['name_en']}*\n\n"
                    f"*Symptoms*: {', '.join(data['symptoms_en']).title()}\n\n"
                    f"*Prevention*: {data['prevention_en']}\n\n"
                    f"*Treatment*: {data['treatment_en']}"
                )
            return response
    
    return translations[lang]['disease_not_found']

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook to handle incoming WhatsApp messages."""
    incoming_msg = request.values.get('Body', '').lower().strip()
    from_number = request.values.get('From')
    
    twiml_response = MessagingResponse()
    response_text = ""

    # Universal command to restart the conversation
    if incoming_msg in ["menu", "restart", "start over", "hi", "hello", "नमस्ते", "ନମସ୍କାର"]:
        user_sessions.pop(from_number, None)

    session = user_sessions.get(from_number, {"lang": None, "state": "start"})
    lang = session.get("lang", "en") # Get language early, default to 'en'

    if session.get("state") == "start":
        response_text = translations["en"]["welcome"]
        session["state"] = "lang_select"
    elif session.get("state") == "lang_select":
        if "1" in incoming_msg or "english" in incoming_msg:
            session["lang"], lang = "en", "en"
            session["state"] = "main_menu"
            response_text = translations[lang]["menu"]
        elif "2" in incoming_msg or "hindi" in incoming_msg or "हिंदी" in incoming_msg:
            session["lang"], lang = "hi", "hi"
            session["state"] = "main_menu"
            response_text = translations[lang]["menu"]
        elif "3" in incoming_msg or "odia" in incoming_msg or "ଓଡ଼ିଆ" in incoming_msg:
            session["lang"], lang = "or", "or"
            session["state"] = "main_menu"
            response_text = translations[lang]["menu"]
        else:
            response_text = translations["en"]["welcome"]
    elif session.get("state") == "main_menu":
        if "1" in incoming_msg:
            response_text = translations[lang]["symptom_prompt"]
            session["state"] = "symptom_check"
        elif "2" in incoming_msg:
            response_text = translations[lang]["alert_info"]
        elif "3" in incoming_msg:
            response_text = translations[lang]["vaccine_info"]
        elif "4" in incoming_msg:
            response_text = translations[lang]["disease_prompt"]
            session["state"] = "disease_search"
        else:
            response_text = translations[lang]["menu"]
    elif session.get("state") == "symptom_check":
        diagnosis_result = get_diagnosis_from_db(incoming_msg, lang)
        response_text = f"{diagnosis_result}\n\n{translations[lang]['symptom_repeat']}"
        # Stays in the 'symptom_check' state
    elif session.get("state") == "disease_search":
        disease_info_result = get_disease_info_from_db(incoming_msg, lang)
        response_text = f"{disease_info_result}\n\n{translations[lang]['disease_repeat']}"
        # Stays in the 'disease_search' state
    
    user_sessions[from_number] = session
    twiml_response.message(response_text)
    return str(twiml_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

