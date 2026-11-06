from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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

# CORS permissif pour le frontend de ton pote (React, Vue, Streamlit, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes
app.include_router(candidates.router)
app.include_router(job_posting.router)
app.include_router(chat.router)
app.include_router(comparator.router)
app.include_router(audit.router)
app.include_router(product_decisions.router)

@app.get("/", tags=["Santé"])
async def root():
    return {
        "app": "Atelier Nova - Assistant RH Local",
        "status": "online",
        "mode": "100% Local / Air-Gapped",
        "model": "ministral-3:3b via Ollama",
        "docs": "/docs"
    }
