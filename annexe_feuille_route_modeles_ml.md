# Annexe — Feuille de route des modèles ML/statistiques (agent SANDBOX_ML)

> Complète la section 7 (Phase 5 — Sandbox & Déploiement) de `SPEC_HUB_IA_MULTI_AGENTS.md`. Ce document fixe, pour chaque famille de modèle que l'agent SANDBOX_ML peut être amené à générer, les sorties obligatoires et les procédures de diagnostic qui en découlent immédiatement. L'objectif est d'empêcher le LLM de code-gen d'improviser un sous-ensemble arbitraire de résultats.

---

## 1. Principe et faisabilité technique

### 1.1 Où ça s'insère dans le flux existant

Dans `routers/sandbox.py` (section 7.3), le code exécuté dans le sandbox est généré par un appel LLM dédié, à partir de la requête utilisateur et du schéma du dataset. Actuellement rien ne contraint ce que ce code doit produire comme sorties. Ce document ajoute une étape de contrainte en amont (prompt normatif) et une étape de validation en aval (vérification post-exécution).

```
requête utilisateur + schéma dataset
        │
        ▼
détection de la famille de modèle (LLM ou règles simples)
        │
        ▼
MODEL_SPECS[famille] → fragment de prompt normatif injecté
        │
        ▼
appel LLM dédié → code Python généré
        │
        ▼
DockerSandboxRunner.run(code, ...)
        │
        ▼
validate_output(result, MODEL_SPECS[famille].output_schema)
        │
   ┌────┴────┐
   ▼         ▼
 valide   incomplet → success=False, message listant les champs manquants
```

### 1.2 Structure de données proposée

```python
# sandbox/model_specs.py

from enum import Enum
from pydantic import BaseModel

class ModelFamily(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_REGRESSION = "linear_regression"
    TREE_ENSEMBLE = "tree_ensemble"          # arbre, random forest, gradient boosting
    CLUSTERING = "clustering"                 # k-means, CAH
    FACTOR_ANALYSIS = "factor_analysis"       # ACP, AFC, ACM


class ModelSpec(BaseModel):
    family: ModelFamily
    required_outputs: list[str]        # noms des clés obligatoires dans le JSON de sortie
    output_schema: type[BaseModel]     # schéma Pydantic strict pour validation
    prompt_fragment: str               # injecté tel quel dans le prompt de génération de code
    diagnostic_checks: list[str]       # procédures qui doivent s'exécuter automatiquement


MODEL_SPECS: dict[ModelFamily, ModelSpec] = {
    # rempli en 2.x à 6.x ci-dessous, un schéma par famille
}
```

### 1.3 Validation post-exécution

```python
def validate_output(result: "SandboxResult", spec: ModelSpec) -> "SandboxResult":
    """
    Charge le JSON produit par le code (convention : un fichier
    /workspace/output/metrics.json systématiquement écrit par le code généré).
    Valide contre spec.output_schema.

    Si validation échoue : result.success = False, result.stderr complété avec
    la liste des champs manquants — jamais un succès partiel silencieux.
    """
    ...
```

Le code généré par le LLM doit donc systématiquement écrire ses résultats structurés dans `/workspace/output/metrics.json`, en plus des artefacts visuels (courbes, matrices). C'est ce fichier que `validate_output` contrôle. Cela suppose d'ajouter cette convention explicitement dans `Dockerfile.sandbox` / le prompt de génération, pas seulement dans le code de validation côté backend.

### 1.4 Comportement en cas d'échec de validation

Un seul retry automatique, avec le message d'erreur (champs manquants) réinjecté dans le prompt de génération de code — même logique que le retry de `LLMGateway.chat()` en Phase 1. Si le second essai échoue aussi, `SandboxResult.success=False` est renvoyé tel quel à l'utilisateur avec une explication en français, pas d'exception non gérée.

---

## 2. Régression logistique

| Sortie obligatoire | Procédure qui en découle immédiatement |
|---|---|
| Coefficients (log-odds) par variable | — |
| Odds ratios (`exp(coef)`) avec IC 95% | Calculés systématiquement, jamais seulement les coefficients bruts |
| p-values (test de Wald) par variable | Variables non significatives (p > 0.05) signalées explicitement dans le texte de synthèse, jamais retirées automatiquement du modèle sans le mentionner |
| VIF (Variance Inflation Factor) par variable | Si VIF > 5, avertissement explicite listant les variables concernées et leur corrélation ; le modèle est quand même renvoyé, la décision de retrait revient à l'utilisateur |
| Matrice de confusion (seuil 0.5) | — |
| Courbe ROC (points fpr/tpr, pas seulement l'AUC) + AUC | Seuil optimal (indice de Youden) calculé en complément du seuil 0.5, et rapporté séparément |
| Pseudo-R² (McFadden) | — |

```python
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
    roc_curve: list[ROCPoint]   # points complets, pas juste le scalaire
    roc_auc: float
    youden_threshold: float
    mcfadden_pseudo_r2: float
    non_significant_variables: list[str]
    high_vif_variables: list[str]
```

Librairies suggérées : `statsmodels.api.Logit` (pour p-values et IC natifs, plus fiable que `sklearn` sur ce point), `statsmodels.stats.outliers_influence.variance_inflation_factor`, `sklearn.metrics.roc_curve/roc_auc_score`.

---

## 3. Régression linéaire (OLS)

| Sortie obligatoire | Procédure qui en découle immédiatement |
|---|---|
| Coefficients + IC 95% | — |
| p-values par variable (test t) | Idem logistique : signaler, ne pas retirer automatiquement |
| R² et R² ajusté | — |
| Test F global (significativité du modèle) | — |
| VIF par variable | Même règle de seuil (>5) que pour la logistique |
| Test de normalité des résidus (Shapiro-Wilk) | Si p < 0.05, mention explicite que l'hypothèse de normalité est rejetée, avec recommandation (transformation, modèle robuste) |
| Test d'homoscédasticité (Breusch-Pagan) | Si hétéroscédasticité détectée, recommander des erreurs-types robustes (`HC3`) |
| Test d'indépendance des résidus (Durbin-Watson) | Pertinent surtout si structure temporelle dans les données ; signalé sinon comme information secondaire |
| Distance de Cook (points influents) | Points avec distance de Cook élevée listés explicitement, jamais supprimés automatiquement |
| RMSE / MAE (train et test) | Calculés sur un split train/test, jamais uniquement en train |

```python
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
```

Librairies : `statsmodels.api.OLS` (résidus et diagnostics natifs), `statsmodels.stats.diagnostic.het_breuschpagan`, `scipy.stats.shapiro`, `statsmodels.stats.outliers_influence.OLSInfluence` (Cook).

---

## 4. Arbres, Random Forest, Gradient Boosting

| Sortie obligatoire | Procédure qui en découle immédiatement |
|---|---|
| Importance des variables (feature importance) | — |
| Validation croisée k-fold (k=5 par défaut) | Score moyen + écart-type rapportés, jamais un score unique sur un seul split |
| Comparaison score train vs score test | Écart important (> ~15-20 points relatifs) signalé explicitement comme suspicion de surapprentissage |
| Si classification : matrice de confusion + courbe ROC (points fpr/tpr) + AUC | Même règle que pour la régression logistique : l'AUC seule ne suffit pas, les points de la courbe doivent être renvoyés pour permettre l'affichage |
| Si régression : RMSE, MAE, R² | — |
| Hyperparamètres effectivement utilisés | Toujours rapportés, même les valeurs par défaut, pour traçabilité |

```python
class TreeEnsembleOutput(BaseModel):
    feature_importance: dict[str, float]
    cv_scores_mean: float
    cv_scores_std: float
    train_score: float
    test_score: float
    overfitting_warning: bool
    hyperparameters: dict
    # classification uniquement
    confusion_matrix: list[list[int]] | None = None
    roc_curve: list[ROCPoint] | None = None
    roc_auc: float | None = None
    # régression uniquement
    rmse: float | None = None
    mae: float | None = None
    r_squared: float | None = None
```

---

## 5. Clustering (k-means, CAH)

| Sortie obligatoire | Procédure qui en découle immédiatement |
|---|---|
| Nombre de clusters retenu + méthode de choix (coude ou silhouette) | Le code doit tester plusieurs valeurs de k avant de fixer le choix final, pas une valeur arbitraire |
| Score de silhouette global | — |
| Profils moyens par cluster (moyenne des variables par groupe) | — |
| Projection 2D (ACP) des individus colorés par cluster | — |

```python
class ClusteringOutput(BaseModel):
    n_clusters: int
    selection_method: str  # "elbow" | "silhouette"
    silhouette_score: float
    cluster_profiles: dict[str, dict[str, float]]  # cluster_id -> {variable: moyenne}
    pca_explained_variance_2d: tuple[float, float]
```

---

## 6. Analyse factorielle (ACP / AFC / ACM)

| Sortie obligatoire | Procédure qui en découle immédiatement |
|---|---|
| Variance expliquée par axe (valeurs propres) | Nombre d'axes retenus justifié (règle de Kaiser ou coude), pas un nombre fixe arbitraire |
| Contributions et cos² des variables/individus | — |
| Cercle des corrélations (variables) | — |
| Carte des individus sur les 2 premiers axes | — |

```python
class FactorAnalysisOutput(BaseModel):
    explained_variance_ratio: list[float]
    n_axes_retained: int
    retention_rule: str  # "kaiser" | "elbow"
    contributions: dict[str, float]
    cos2: dict[str, float]
```

---

## 7. Points à clarifier avant implémentation

Comme pour la section 10 du document principal, ce qui n'est volontairement pas figé ici :

- Seuil de significativité (0.05) et seuil VIF (5) : valeurs par défaut fixées ci-dessus, mais pourraient être paramétrables via `TrainModelRequest` si tu veux les ajuster par cas d'usage.
- Comportement si le dataset est trop petit pour une validation croisée k=5 (ex. < 30 lignes) : réduire k automatiquement, ou renvoyer une erreur explicite ? Non tranché.
- Détection automatique de la famille de modèle à partir de la requête utilisateur : à la charge du Super Agent (routage vers `SANDBOX_ML`) ou d'un second appel LLM dédié juste avant la génération de code ? La spec actuelle (7.3) ne le précise pas.
- Convention `/workspace/output/metrics.json` : à ajouter explicitement dans `Dockerfile.sandbox` et dans le prompt système de génération de code, sinon le LLM peut structurer sa sortie différemment à chaque appel.
