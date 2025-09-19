import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ... (Your Flask app setup, translations, and user_sessions dictionary remain the same) ...
# --- PASTE THE CORRECTED FUNCTIONS BELOW INTO YOUR app.py ---

def get_diagnosis_from_db(symptoms_text, lang):
    """
    Diagnose symptoms based on multi-lingual keywords from the JSON database.
    (CORRECTED VERSION: Uses .get() for safe dictionary access)
    """
    user_symptoms = set(symptoms_text.lower().replace("and", "").replace(",", "").split())
    
    if not user_symptoms:
        return translations[lang]['symptom_prompt']

    best_match = None
    max_matches = 0

    for disease, data in health_data.get('diseases', {}).items():
        disease_keywords = set(data.get('symptoms_keywords', []))
        matches = len(user_symptoms.intersection(disease_keywords))
        
        if matches > max_matches:
            max_matches = matches
            best_match = disease

    if max_matches > 0:
        disease_info = health_data['diseases'][best_match]
        
        # Safely get data using .get() with default fallback messages
        default_name = disease_info.get('name_en', 'Unknown Disease')
        default_prevention = "Prevention info not available."
        default_treatment = "Treatment info not available."
        
        if lang == 'hi':
            response = (
                f"आपके लक्षणों के आधार पर, संभावित समस्या '{disease_info.get('name_hi', default_name)}' हो सकती है।\n\n"
                f"*रोकथाम*: {disease_info.get('prevention_hi', default_prevention)}\n"
                f"*उपचार*: {disease_info.get('treatment_hi', default_treatment)}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        elif lang == 'or':
            response = (
                f"ଆପଣଙ୍କ ଲକ୍ଷଣ ଅନୁଯାୟୀ, ସମ୍ଭାବିତ ସମସ୍ୟା '{disease_info.get('name_or', default_name)}' ହୋଇପାରେ।\n\n"
                f"*ପ୍ରତିରୋଧ*: {disease_info.get('prevention_or', default_prevention)}\n"
                f"*ଚିକିତ୍ସା*: {disease_info.get('treatment_or', default_treatment)}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        else: # Default to English
            response = (
                f"Based on your symptoms, the potential issue could be '{disease_info.get('name_en', default_name)}'.\n\n"
                f"*Prevention*: {disease_info.get('prevention_en', default_prevention)}\n"
                f"*Treatment*: {disease_info.get('treatment_en', default_treatment)}\n\n"
                f"{translations[lang]['consult_doctor']}"
            )
        return response
    
    return translations[lang]['no_diagnosis']

def get_disease_info_from_db(disease_name, lang):
    """
    Search for a disease by name using multi-lingual search terms.
    (CORRECTED VERSION: Uses .get() for safe dictionary access)
    """
    search_term = disease_name.lower().strip()
    
    for disease, data in health_data.get('diseases', {}).items():
        if search_term in data.get('search_terms', []):
            
            # Safely get data using .get() with default fallback messages
            default_name = data.get('name_en', 'Unknown Disease')
            default_symptoms = "Symptoms info not available."
            default_prevention = "Prevention info not available."
            default_treatment = "Treatment info not available."

            symptoms_list = data.get('symptoms_en', [])
            symptoms_str = ', '.join(symptoms_list).title() if symptoms_list else default_symptoms

            if lang == 'hi':
                response = (
                    f"*{data.get('name_hi', default_name)}*\n\n"
                    f"*लक्षण*: {symptoms_str}\n\n"
                    f"*रोकथाम*: {data.get('prevention_hi', default_prevention)}\n\n"
                    f"*उपचार*: {data.get('treatment_hi', default_treatment)}"
                )
            elif lang == 'or':
                response = (
                    f"*{data.get('name_or', default_name)}*\n\n"
                    f"*ଲକ୍ଷଣ*: {symptoms_str}\n\n"
                    f"*ପ୍ରତିରୋଧ*: {data.get('prevention_or', default_prevention)}\n\n"
                    f"*ଚିକିତ୍ସା*: {data.get('treatment_or', default_treatment)}"
                )
            else: # Default to English
                response = (
                    f"*{data.get('name_en', default_name)}*\n\n"
                    f"*Symptoms*: {symptoms_str}\n\n"
                    f"*Prevention*: {data.get('prevention_en', default_prevention)}\n\n"
                    f"*Treatment*: {data.get('treatment_en', default_treatment)}"
                )
            return response
            
    return translations[lang]['disease_not_found']

# ... (The rest of your app.py, including the @app.route('/webhook') function, remains the same) ...
