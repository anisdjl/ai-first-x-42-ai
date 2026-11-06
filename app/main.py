from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import time
import uuid
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import candidates, job_posting, chat, comparator, audit, product_decisions, db_inspector

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

# 1. Middleware de Traçabilité & Performance (X-Process-Time, X-Request-ID)
@app.middleware("http")
async def add_timing_and_tracing_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Request-ID"] = request_id
    return response

# 2. Middleware d'En-têtes de Sécurité (Protection contre clickjacking, MIME sniffing)
@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# 3. CORS permissif
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
app.include_router(db_inspector.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")
ADMINER_PATH = os.path.join(STATIC_DIR, "adminer.html")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

@app.get("/", tags=["Interface Web"])
async def serve_ui():
    """Sert l'interface Web minimaliste pour Sarah et le Manager."""
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"status": "online", "docs": "/docs"}

@app.get("/adminer", tags=["Interface Web"])
async def serve_adminer():
    """Interface Adminer / DB Inspector pour vérifier la base MongoDB lors de la soutenance."""
    if os.path.exists(ADMINER_PATH):
        return FileResponse(ADMINER_PATH)
    return {"error": "Interface Adminer introuvable"}

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


