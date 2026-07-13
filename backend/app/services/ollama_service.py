import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def ask_ollama(prompt: str, model: str) -> str:
    """
    Envoie un prompt à Ollama et retourne la réponse générée.
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        return f"Erreur Ollama ({model}) : {str(e)}"
