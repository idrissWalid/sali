"""
Service de profilage de données basé sur ydata-profiling.
Génère des statistiques descriptives complètes pour les fichiers tabulaires.
"""
import pandas as pd
import numpy as np
import json
from ydata_profiling import ProfileReport


def _safe_convert(obj):
    """Convertit les types numpy en types Python natifs pour la sérialisation JSON."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _clean_dict(d: dict) -> dict:
    """Nettoie récursivement un dict pour la sérialisation JSON."""
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, dict):
            cleaned[k] = _clean_dict(v)
        elif isinstance(v, list):
            cleaned[k] = [_safe_convert(item) if not isinstance(item, dict) else _clean_dict(item) for item in v]
        else:
            cleaned[k] = _safe_convert(v)
    return cleaned


def generate_profiling_stats(df: pd.DataFrame) -> dict:
    """
    Génère les statistiques descriptives complètes via ydata-profiling.
    
    Retourne un dict structuré avec :
    - dataset_overview : infos globales (nb lignes, colonnes, doublons, valeurs manquantes)
    - variables : stats détaillées par colonne (type, distribution, outliers, etc.)
    - correlations : matrice de corrélation (Pearson) pour les colonnes numériques
    - missing : analyse des valeurs manquantes
    """
    # Génération du rapport ydata-profiling (mode minimal pour la performance)
    profile = ProfileReport(
        df,
        title="Profiling Report",
        minimal=True,          # Mode rapide, adapté aux gros fichiers
        explorative=False,
        progress_bar=False,
    )

    # Extraction du JSON complet
    report_json = json.loads(profile.to_json())

    # ── 1. Vue d'ensemble du dataset ──────────────────────────────
    table_info = report_json.get("table", {})
    dataset_overview = {
        "n_lignes": table_info.get("n", 0),
        "n_colonnes": table_info.get("n_var", 0),
        "n_doublons": table_info.get("n_duplicates", 0),
        "pct_doublons": round(table_info.get("p_duplicates", 0) * 100, 2),
        "n_valeurs_manquantes_total": table_info.get("n_cells_missing", 0),
        "pct_valeurs_manquantes_total": round(table_info.get("p_cells_missing", 0) * 100, 2),
        "n_variables_numeriques": table_info.get("types", {}).get("Numeric", 0),
        "n_variables_categorielles": table_info.get("types", {}).get("Categorical", 0),
        "n_variables_booleennes": table_info.get("types", {}).get("Boolean", 0),
        "taille_memoire": table_info.get("memory_size", 0),
    }

    # ── 2. Stats par variable ─────────────────────────────────────
    variables = {}
    raw_variables = report_json.get("variables", {})

    for col_name, col_data in raw_variables.items():
        var_type = col_data.get("type", "Unknown")
        var_stats = {
            "type": var_type,
            "n_valeurs_distinctes": col_data.get("n_distinct", 0),
            "pct_valeurs_distinctes": round(col_data.get("p_distinct", 0) * 100, 2),
            "n_manquantes": col_data.get("n_missing", 0),
            "pct_manquantes": round(col_data.get("p_missing", 0) * 100, 2),
        }

        # Stats numériques
        if var_type in ("Numeric",):
            var_stats.update({
                "moyenne": _safe_convert(col_data.get("mean")),
                "ecart_type": _safe_convert(col_data.get("std")),
                "variance": _safe_convert(col_data.get("variance")),
                "min": _safe_convert(col_data.get("min")),
                "max": _safe_convert(col_data.get("max")),
                "mediane": _safe_convert(col_data.get("median")),
                "q1": _safe_convert(col_data.get("25%")),
                "q3": _safe_convert(col_data.get("75%")),
                "iqr": _safe_convert(col_data.get("iqr")),
                "skewness": _safe_convert(col_data.get("skewness")),
                "kurtosis": _safe_convert(col_data.get("kurtosis")),
                "coefficient_variation": _safe_convert(col_data.get("cv")),
                "somme": _safe_convert(col_data.get("sum")),
                "n_zeros": col_data.get("n_zeros", 0),
            })

        # Stats catégorielles
        elif var_type in ("Categorical", "Boolean"):
            var_stats.update({
                "valeur_dominante": str(col_data.get("top", "")),
                "frequence_dominante": col_data.get("freq", 0),
            })

        variables[col_name] = var_stats

    # ── 3. Corrélations ───────────────────────────────────────────
    correlations = {}
    raw_correlations = report_json.get("correlations", {})
    # Extraire la matrice de Pearson si disponible
    for corr_type in ("pearson", "spearman", "auto"):
        if corr_type in raw_correlations:
            corr_data = raw_correlations[corr_type]
            if isinstance(corr_data, dict):
                correlations[corr_type] = _clean_dict(corr_data)
            break

    # ── 4. Analyse des valeurs manquantes ─────────────────────────
    missing = {}
    for col_name, col_data in raw_variables.items():
        n_missing = col_data.get("n_missing", 0)
        if n_missing > 0:
            missing[col_name] = {
                "n_manquantes": n_missing,
                "pct_manquantes": round(col_data.get("p_missing", 0) * 100, 2),
            }

    return {
        "dataset_overview": dataset_overview,
        "variables": _clean_dict(variables),
        "correlations": correlations,
        "missing": _clean_dict(missing),
    }


def generate_profiling_html(df: pd.DataFrame) -> str:
    """
    Génère le rapport HTML complet de ydata-profiling.
    Utile si on veut l'afficher directement dans le frontend.
    """
    profile = ProfileReport(
        df,
        title="Rapport de Profilage",
        minimal=True,
        explorative=False,
        progress_bar=False,
    )
    return profile.to_html()
