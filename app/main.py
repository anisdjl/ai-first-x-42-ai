from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import candidates, job_posting, chat, comparator, audit, product_decisions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Atelier Nova - Assistant RH Local (Souverain & RGPD)",
    description="Backend FastAPI pour l'analyse locale de CVs, conforme RGPD et IA Act (sans score ni classement).",
    version="1.0.0",
    lifespan=lifespan
)

# CORS permissif
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes API
app.include_router(candidates.router)
app.include_router(job_posting.router)
app.include_router(chat.router)
app.include_router(comparator.router)
app.include_router(audit.router)
app.include_router(product_decisions.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

@app.get("/", tags=["Interface Web"])
async def serve_ui():
    """Sert l'interface Web minimaliste pour Sarah et le Manager."""
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"status": "online", "docs": "/docs"}

@app.get("/cv-exemple-agent.md", tags=["Interface Web"])
async def serve_example_cv():
    example_path = os.path.join(ROOT_DIR, "cv-exemple-agent.md")
    if os.path.exists(example_path):
        return FileResponse(example_path, media_type="text/markdown")
    return {"error": "Fichier introuvable"}

@app.get("/api/health", tags=["Santé"])
async def health_check():
    return {
        "app": "Atelier Nova - Assistant RH Local",
        "status": "online",
        "mode": "100% Local / Air-Gapped",
        "model": "ministral-3:3b via Ollama"
    }

