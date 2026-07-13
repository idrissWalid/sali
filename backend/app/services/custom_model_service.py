import requests
import json
import logging

logger = logging.getLogger(__name__)

CUSTOM_MODEL_URL = "https://tug-turtle-handled.ngrok-free.dev"

def ask_custom_model(prompt: str, history: list = [], data_context: str = "") -> str:
    """
    Appelle le modèle externe via ngrok.
    """
    try:
        # Construction du prompt avec le contexte
        full_prompt = ""
        if data_context:
            full_prompt += f"{data_context}\n\n"
            
        # Ajouter un peu d'historique au prompt
        if history:
            for msg in history[-5:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
                
        full_prompt += f"Question : {prompt}"

        headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        }
        
        payload = {
            "prompt": full_prompt
        }
        
        response = requests.post(f"{CUSTOM_MODEL_URL}/ask", json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Suppose response structure, default to fallback
        if "response" in data:
            return data["response"]
        elif "answer" in data:
            return data["answer"]
        elif "text" in data:
            return data["text"]
        else:
            # Si le format est inconnu, on retourne tout en string
            return str(data)

    except Exception as e:
        logger.error(f"Erreur avec le modèle custom ngrok : {e}")
        return f"Erreur modèle externe : {str(e)}"
