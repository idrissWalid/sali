import io
import os
import traceback
import pandas as pd
from pathlib import Path

def _load_df(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Charge un DataFrame depuis les bytes bruts du fichier uploadé."""
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))

def ask_timecopilot(file_bytes: bytes, filename: str, question: str) -> dict:
    """
    Répond à une question sur les séries temporelles en utilisant timecopilot.

    Args:
        file_bytes: Contenu du fichier CSV/Excel
        filename:   Nom du fichier
        question:   Question en langage naturel

    Returns:
        dict:
            output (str)       — Réponse textuelle
            images (list[str]) — Graphiques base64 si générés
            error  (dict|None) — Erreur éventuelle
    """
    try:
        df = _load_df(file_bytes, filename)
    except Exception as exc:
        return {
            "output": "",
            "images": [],
            "error": {
                "technical": traceback.format_exc(),
                "simple": f"Impossible de charger le fichier : {exc}",
            },
        }

    try:
        # On s'assure que la clé Gemini est définie pour les bibliothèques sous-jacentes (litellm etc.)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        os.environ["GEMINI_API_KEY"] = api_key
        
        from timecopilot import TimeCopilot
        
        try:
            agent = TimeCopilot(llm="gemini/gemini-1.5-flash")
        except Exception:
            # Fallback constructeur par défaut
            agent = TimeCopilot()

        # Préparation du répertoire pour les graphiques
        _CHARTS_DIR = Path("/tmp/timecopilot_charts")
        _CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        # Vider les anciens graphiques
        for old_chart in _CHARTS_DIR.glob("*.png"):
            old_chart.unlink()

        # On lui demande de répondre en français avec des consignes spécifiques
        full_question = (
            f"Réponds en français. {question}\n\n"
            "INSTRUCTIONS IMPORTANTES :\n"
            "1. Fournis impérativement les détails du modèle utilisé (nom du modèle, hyperparamètres, algorithme sous-jacent) pour pouvoir suivre la checkliste de validation.\n"
            f"2. Tu DOIS toujours générer un graphique (évolution historique + prévision + intervalle de confiance) pour cette série temporelle. Sauvegarde ce graphique au format PNG dans le dossier '{_CHARTS_DIR.as_posix()}'. N'utilise pas plt.show(), utilise plt.savefig() avec un chemin absolu dans ce dossier."
        )
        
        # Exécution de la prévision / analyse
        result = agent.forecast(data=df, query=full_question)
        output = str(result)
        
        # Récupération des graphiques générés
        images = []
        import base64
        try:
            for chart_path in sorted(_CHARTS_DIR.glob("*.png")):
                with open(chart_path, "rb") as f:
                    images.append(base64.b64encode(f.read()).decode("utf-8"))
                chart_path.unlink()
        except Exception:
            pass
        
        return {"output": output, "images": images, "error": None}

    except Exception:
        tb = traceback.format_exc()
        lines = [l for l in tb.strip().splitlines() if l.strip()]
        return {
            "output": "",
            "images": [],
            "error": {
                "technical": tb,
                "simple": lines[-1] if lines else "Erreur TimeCopilot inconnue.",
            },
        }
