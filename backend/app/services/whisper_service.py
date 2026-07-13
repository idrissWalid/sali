import os
import tempfile
import traceback
from typing import Optional

# Modèle Whisper lazy-loaded pour éviter de bloquer le démarrage d'uvicorn
# ou de crasher si internet n'est pas disponible au lancement.
_whisper_model = None

def get_whisper_model():
    """
    Charge le modèle Whisper de manière paresseuse.
    """
    global _whisper_model
    if _whisper_model is None:
        import whisper
        try:
            # On charge le modèle "small". 
            # Note: cela nécessitera une connexion internet la première fois.
            _whisper_model = whisper.load_model("small")
        except Exception as e:
            print(f"Erreur lors du chargement du modèle Whisper: {e}")
            raise RuntimeError(f"Impossible de charger Whisper: {e}")
    return _whisper_model

def transcribe_audio(file_bytes: bytes, filename: str) -> dict:
    """
    Transcende l'audio en utilisant Whisper small.
    Retourne un dictionnaire avec le texte ou l'erreur.
    """
    try:
        # Obtenir le modèle
        model = get_whisper_model()
        
        # Whisper a besoin d'un chemin de fichier physique
        # Nous allons donc sauvegarder temporairement le fichier
        ext = filename.split('.')[-1] if '.' in filename else 'wav'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
            
        try:
            # Transcrire le fichier audio
            result = model.transcribe(tmp_path)
            text = result.get("text", "").strip()
            
            return {
                "status": "ok",
                "text": text
            }
        finally:
            # Toujours nettoyer le fichier temporaire
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
