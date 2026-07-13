from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ModelFamily(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_REGRESSION = "linear_regression"
    TREE_ENSEMBLE = "tree_ensemble"
    CLUSTERING = "clustering"
    FACTOR_ANALYSIS = "factor_analysis"


class ROCPoint(BaseModel):
    fpr: float
    tpr: float
    threshold: float


class LogisticRegressionOutput(BaseModel):
    coefficients: dict[str, float]
    odds_ratios: dict[str, float]
    ci_95_odds_ratios: dict[str, tuple[float, float]]
    p_values: dict[str, float]
    vif: dict[str, float]
    confusion_matrix: list[list[int]]
    roc_curve: list[ROCPoint]
    roc_auc: float
    youden_threshold: float
    mcfadden_pseudo_r2: float
    non_significant_variables: list[str]
    high_vif_variables: list[str]


class LinearRegressionOutput(BaseModel):
    coefficients: dict[str, float]
    ci_95: dict[str, tuple[float, float]]
    p_values: dict[str, float]
    r_squared: float
    r_squared_adj: float
    f_test_pvalue: float
    vif: dict[str, float]
    shapiro_pvalue: float
    breusch_pagan_pvalue: float
    durbin_watson: float
    influential_points_indices: list[int]
    rmse_train: float
    rmse_test: float
    mae_train: float
    mae_test: float


class TreeEnsembleOutput(BaseModel):
    feature_importance: dict[str, float]
    cv_scores_mean: float
    cv_scores_std: float
    train_score: float
    test_score: float
    overfitting_warning: bool
    hyperparameters: dict
    confusion_matrix: Optional[list[list[int]]] = None
    roc_curve: Optional[list[ROCPoint]] = None
    roc_auc: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r_squared: Optional[float] = None


class ClusteringOutput(BaseModel):
    n_clusters: int
    selection_method: str  # "elbow" | "silhouette"
    silhouette_score: float
    cluster_profiles: dict[str, dict[str, float]]
    pca_explained_variance_2d: tuple[float, float]


class FactorAnalysisOutput(BaseModel):
    explained_variance_ratio: list[float]
    n_axes_retained: int
    retention_rule: str  # "kaiser" | "elbow"
    contributions: dict[str, float]
    cos2: dict[str, float]


class ModelSpec(BaseModel):
    family: ModelFamily
    required_outputs: list[str]
    output_schema: type[BaseModel]
    prompt_fragment: str
    diagnostic_checks: list[str]


MODEL_SPECS: dict[ModelFamily, ModelSpec] = {
    ModelFamily.LOGISTIC_REGRESSION: ModelSpec(
        family=ModelFamily.LOGISTIC_REGRESSION,
        required_outputs=list(LogisticRegressionOutput.model_fields.keys()),
        output_schema=LogisticRegressionOutput,
        prompt_fragment="""
MODELE ATTENDU : Régression Logistique.
OBLIGATION ABSOLUE : Tu dois générer un fichier "metrics.json" contenant EXACTEMENT ces clés (et aucune autre) :
- coefficients: dictionnaire (variable -> coef)
- odds_ratios: dictionnaire (variable -> exp(coef))
- ci_95_odds_ratios: dictionnaire (variable -> [lower, upper])
- p_values: dictionnaire (variable -> p-value)
- vif: dictionnaire (variable -> VIF)
- confusion_matrix: liste de liste d'entiers (matrice 2x2)
- roc_curve: liste d'objets avec "fpr", "tpr", "threshold"
- roc_auc: float
- youden_threshold: float
- mcfadden_pseudo_r2: float
- non_significant_variables: liste de strings (p_value > 0.05)
- high_vif_variables: liste de strings (VIF > 5)

Utilise statsmodels.api.Logit. Sauvegarde les visualisations générées avec matplotlib.
Tu DOIS sauvegarder ce JSON structuré avec : 
import json
with open('metrics.json', 'w') as f: json.dump(..., f)
""",
        diagnostic_checks=[]
    ),
    ModelFamily.LINEAR_REGRESSION: ModelSpec(
        family=ModelFamily.LINEAR_REGRESSION,
        required_outputs=list(LinearRegressionOutput.model_fields.keys()),
        output_schema=LinearRegressionOutput,
        prompt_fragment="""
MODELE ATTENDU : Régression Linéaire (OLS).
OBLIGATION ABSOLUE : Tu dois générer un fichier "metrics.json" contenant EXACTEMENT ces clés :
- coefficients
- ci_95
- p_values
- r_squared
- r_squared_adj
- f_test_pvalue
- vif
- shapiro_pvalue
- breusch_pagan_pvalue
- durbin_watson
- influential_points_indices
- rmse_train
- rmse_test
- mae_train
- mae_test

Sépare les données (80/20).
Utilise statsmodels.api.OLS. Sauvegarde les visualisations générées (ex: résidus) avec matplotlib.
Tu DOIS sauvegarder ce JSON structuré avec : 
import json
with open('metrics.json', 'w') as f: json.dump(metrics_dict, f)
""",
        diagnostic_checks=[]
    ),
    ModelFamily.TREE_ENSEMBLE: ModelSpec(
        family=ModelFamily.TREE_ENSEMBLE,
        required_outputs=list(TreeEnsembleOutput.model_fields.keys()),
        output_schema=TreeEnsembleOutput,
        prompt_fragment="""
MODELE ATTENDU : Arbres / Random Forest / Gradient Boosting.
OBLIGATION ABSOLUE : Tu dois générer un fichier "metrics.json" contenant EXACTEMENT ces clés :
- feature_importance
- cv_scores_mean
- cv_scores_std
- train_score
- test_score
- overfitting_warning (boolean, True si test_score << train_score)
- hyperparameters (dict)
(Si classification) : confusion_matrix, roc_curve (liste de {fpr, tpr, threshold}), roc_auc
(Si régression) : rmse, mae, r_squared

Sépare en train/test et fais une cross-validation k-fold (k=5) sur le train.
Tu DOIS sauvegarder ce JSON structuré avec : 
import json
with open('metrics.json', 'w') as f: json.dump(metrics_dict, f)
""",
        diagnostic_checks=[]
    ),
    ModelFamily.CLUSTERING: ModelSpec(
        family=ModelFamily.CLUSTERING,
        required_outputs=list(ClusteringOutput.model_fields.keys()),
        output_schema=ClusteringOutput,
        prompt_fragment="""
MODELE ATTENDU : Clustering (K-Means ou CAH).
OBLIGATION ABSOLUE : Tu dois générer un fichier "metrics.json" contenant EXACTEMENT ces clés :
- n_clusters (entier choisi)
- selection_method ("elbow" ou "silhouette")
- silhouette_score (float)
- cluster_profiles (dict : cluster_id -> {variable: moyenne})
- pca_explained_variance_2d (tuple de 2 floats)

Teste plusieurs valeurs de K, génère un graphique, et fais une PCA pour projeter en 2D.
Tu DOIS sauvegarder ce JSON structuré avec : 
import json
with open('metrics.json', 'w') as f: json.dump(metrics_dict, f)
""",
        diagnostic_checks=[]
    ),
    ModelFamily.FACTOR_ANALYSIS: ModelSpec(
        family=ModelFamily.FACTOR_ANALYSIS,
        required_outputs=list(FactorAnalysisOutput.model_fields.keys()),
        output_schema=FactorAnalysisOutput,
        prompt_fragment="""
MODELE ATTENDU : Analyse Factorielle (ACP / AFC / ACM).
OBLIGATION ABSOLUE : Tu dois générer un fichier "metrics.json" contenant EXACTEMENT ces clés :
- explained_variance_ratio (liste de floats)
- n_axes_retained (entier)
- retention_rule ("kaiser" ou "elbow")
- contributions (dict : variable -> float)
- cos2 (dict : variable -> float)

Justifie le nombre d'axes, trace le cercle des corrélations et la carte des individus.
Tu DOIS sauvegarder ce JSON structuré avec : 
import json
with open('metrics.json', 'w') as f: json.dump(metrics_dict, f)
""",
        diagnostic_checks=[]
    )
}
