import os
import json
import uuid
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List

from app.core.database import get_db_connection
import joblib

router = APIRouter(
    prefix="/models",
    tags=["models"]
)

class PredictRequest(BaseModel):
    features: Dict[str, Any]

@router.get("/{session_id}")
async def list_models(session_id: str):
    """Liste tous les modèles entraînés pour une session donnée."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, type, features, metrics, created_at FROM models WHERE session_id = ? ORDER BY created_at DESC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    models_list = []
    for r in rows:
        models_list.append({
            "id": r["id"],
            "name": r["name"],
            "type": r["type"],
            "features": json.loads(r["features"]) if r["features"] else [],
            "metrics": json.loads(r["metrics"]) if r["metrics"] else {},
            "created_at": r["created_at"]
        })
    
    return {"models": models_list}

@router.get("/info/{model_id}")
async def get_model_info(model_id: str):
    """Récupère les informations d'un modèle spécifique."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, type, features, metrics, created_at FROM models WHERE id = ?",
        (model_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Modèle introuvable")
        
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "features": json.loads(row["features"]) if row["features"] else [],
        "metrics": json.loads(row["metrics"]) if row["metrics"] else {},
        "created_at": row["created_at"]
    }

@router.get("/{model_id}/download")
async def download_model(model_id: str):
    """Télécharge le fichier .pkl du modèle."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, file_path FROM models WHERE id = ?", (model_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row["file_path"] or not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="Modèle introuvable")
        
    return FileResponse(
        path=row["file_path"],
        filename=f"{row['name']}.pkl",
        media_type="application/octet-stream"
    )

@router.post("/{model_id}/predict")
async def predict(model_id: str, request: PredictRequest):
    """Fait une prédiction à partir des features fournies."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, features, type FROM models WHERE id = ?", (model_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row["file_path"] or not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="Modèle introuvable")
        
    try:
        expected_features = json.loads(row["features"]) if row["features"] else []
        model = joblib.load(row["file_path"])
        
        # Prepare DataFrame for prediction (models usually expect 2D arrays/DataFrames)
        input_data = {}
        if expected_features:
            for feat in expected_features:
                val = request.features.get(feat)
                if val is None:
                    raise HTTPException(status_code=400, detail=f"Caractéristique manquante : {feat}")
                input_data[feat] = [val]
            df = pd.DataFrame(input_data)
        else:
            # S'il n'y a pas de features explicites, on utilise tout ce qu'on reçoit
            input_data = {k: [v] for k, v in request.features.items()}
            df = pd.DataFrame(input_data)
            
        # Predict
        prediction = model.predict(df)
        
        # Return prediction as list
        return {"prediction": prediction.tolist()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction : {str(e)}")
