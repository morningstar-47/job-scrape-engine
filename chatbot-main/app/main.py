"""
Application principale FastAPI
Point d'entrée de l'API REST pour l'assistant virtuel
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import chat
from app.routers import jobs
import uvicorn


# Créer l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(chat.router)
app.include_router(chat.router_knowledge)
app.include_router(jobs.router)


@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "Bienvenue sur l'API de l'Assistant Virtuel LangChain",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat",
            "knowledge": "/knowledge",
            "jobs": "/jobs"
        }
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'application"""
    try:
        # Vérifier que les services sont initialisés
        from app.services.llm_service import llm_service
        from app.services.memory_service import memory_service
        from app.services.vector_store import vector_store_service
        
        return {
            "status": "healthy",
            "services": {
                "llm": llm_service.llm is not None,
                "memory": memory_service is not None,
                "vector_store": vector_store_service.vector_store is not None
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Gestionnaire d'exceptions HTTP personnalisé"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Gestionnaire d'exceptions générales"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Une erreur interne s'est produite",
            "detail": str(exc) if settings.debug else None
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

