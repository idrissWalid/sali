"""
pandasai_service.py — Statistiques descriptives via PandasAI v3 + Gemini.

PandasAI v3 utilise un LLM via l'interface pandasai.llm.base.LLM.
On crée un wrapper GeminiLLM compatible avec cette interface pour utiliser
le modèle Gemini déjà configuré dans le projet.
"""

import io
import os
import base64
import traceback
from pathlib import Path

import pandas as pd

# Répertoire temporaire pour les charts PandasAI
_CHARTS_DIR = Path("/tmp/pandasai_charts")
_CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Wrapper Gemini compatible avec PandasAI v3 ────────────────────────────────

class GeminiLLM:
    """
    Adaptateur minimal qui rend google-generativeai compatible
    avec l'interface pandasai.llm.base.LLM (v3).
    """

    def __init__(self):
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        self._client = genai.Client(api_key=api_key)
        self._model_name = "gemini-1.5-flash"

    # PandasAI v3 appelle call() avec un objet BasePrompt
    def call(self, instruction, context=None) -> str:
        try:
            prompt_str = str(instruction)
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt_str
            )
            return response.text
        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc

    # generate_code utilisé par certains chemin de PandasAI v3
    def generate_code(self, instruction, context=None) -> str:
        raw = self.call(instruction, context)
        # Nettoyer les blocs markdown si présents
        if "```python" in raw:
            raw = raw.split("```python")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        return raw.strip()

    @property
    def type(self) -> str:
        return "gemini"

    # Méthode attendue pour la vérification is_pandasai_llm
    @staticmethod
    def is_pandasai_llm() -> bool:
        return True


# ── Chargement du DataFrame ───────────────────────────────────────────────────

def _load_df(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Charge un DataFrame depuis les bytes bruts du fichier uploadé."""
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


# ── Service principal PandasAI ────────────────────────────────────────────────

def ask_pandasai(file_bytes: bytes, filename: str, question: str) -> dict:
    """
    Répond à une question de statistiques descriptives via PandasAI v3.

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
        from pandasai import SmartDataframe
        from pandasai.config import Config

        llm = GeminiLLM()
        config = Config(llm=llm, verbose=False, max_retries=2)

        sdf = SmartDataframe(
            df,
            config=config,
            description=f"DataFrame chargé depuis {filename}",
        )

        # Consigne en français explicite
        full_question = f"Réponds en français. {question}"
        result = sdf.chat(full_question)

        # Récupérer les graphiques éventuellement générés
        images = _collect_charts()

        # Convertir le résultat en string lisible
        output = _format_result(result)

        return {"output": output, "images": images, "error": None}

    except Exception:
        tb = traceback.format_exc()
        lines = [l for l in tb.strip().splitlines() if l.strip()]
        return {
            "output": "",
            "images": [],
            "error": {
                "technical": tb,
                "simple": lines[-1] if lines else "Erreur PandasAI inconnue.",
            },
        }


def _format_result(result) -> str:
    """Convertit le résultat PandasAI en string propre."""
    if result is None:
        return "Aucun résultat retourné."
    if isinstance(result, pd.DataFrame):
        if hasattr(result, "to_markdown"):
            return result.to_markdown(index=False)
        return result.to_string(index=False)
    if isinstance(result, (int, float)):
        return str(result)
    return str(result)


def _collect_charts() -> list:
    """Récupère les graphiques PNG générés et les encode en base64."""
    images = []
    try:
        chart_files = sorted(_CHARTS_DIR.glob("*.png"))
        for chart_path in chart_files:
            with open(chart_path, "rb") as f:
                images.append(base64.b64encode(f.read()).decode("utf-8"))
            chart_path.unlink()
    except Exception:
        pass
    return images


# ── Stats descriptives rapides (sans LLM) ────────────────────────────────────

def get_descriptive_stats(file_bytes: bytes, filename: str) -> dict:
    """
    Génère les statistiques descriptives complètes sans LLM.
    Utilisé pour enrichir le contexte initial de la session.
    """
    try:
        df = _load_df(file_bytes, filename)

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()

        stats = {}

        if numeric_cols:
            desc = df[numeric_cols].describe().round(4)
            stats["numeriques"] = desc.to_dict()

        cat_stats = {}
        for col in cat_cols:
            vc = df[col].value_counts()
            cat_stats[col] = {
                "n_valeurs_distinctes": int(df[col].nunique()),
                "valeur_dominante": str(vc.index[0]) if len(vc) > 0 else None,
                "frequence_dominante": int(vc.iloc[0]) if len(vc) > 0 else 0,
                "n_manquantes": int(df[col].isna().sum()),
            }
        if cat_stats:
            stats["categorielles"] = cat_stats

        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr().round(4)
            stats["correlations"] = corr.to_dict()

        missing = df.isna().sum()
        stats["valeurs_manquantes"] = {
            col: int(missing[col])
            for col in df.columns
            if missing[col] > 0
        }

        return {"status": "ok", "stats": stats, "shape": list(df.shape)}

    except Exception:
        return {
            "status": "error",
            "error": traceback.format_exc(),
        }
