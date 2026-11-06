from fastapi import APIRouter, HTTPException, Query
from app.database import get_database
from typing import Dict, Any, List
import json

router = APIRouter(prefix="/api/v1/db-inspector", tags=["DB Inspector (Adminer)"])

@router.get("/overview")
async def get_db_overview():
    """Vue globale de la base MongoDB pour la soutenance (type Adminer)."""
    db = get_database()
    collections = await db.list_collection_names()
    
    stats = []
    for col_name in collections:
        count = await db[col_name].count_documents({})
        stats.append({
            "collection": col_name,
            "document_count": count
        })
        
    return {
        "database": "atelier_nova_hr",
        "engine": "MongoDB (Community 7.0/8.0/9.0)",
        "host": "localhost:27017",
        "collections": stats
    }

@router.get("/collection/{col_name}")
async def get_collection_data(col_name: str, limit: int = Query(50, ge=1, le=200)):
    """Affiche les documents bruts d'une collection pour vérification en direct."""
    db = get_database()
    valid_cols = await db.list_collection_names()
    if col_name not in valid_cols:
        raise HTTPException(status_code=404, detail="Collection introuvable.")
        
    cursor = db[col_name].find().sort("_id", -1).limit(limit)
    docs = []
    async for d in cursor:
        d["_id"] = str(d["_id"])
        # Format dates
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        docs.append(d)
        
    return {
        "collection": col_name,
        "total_shown": len(docs),
        "documents": docs
    }
