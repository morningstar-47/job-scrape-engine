from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile, os, asyncio, json, uuid, requests
from pathlib import Path
from Cv_reader import read_cv, ask_vision, call_chatbot_api
from typing import List

app = FastAPI(
    title="CV Reader Agent API",
    description="API permettant d'exposer l'agent CV Reader et ses capacités.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cv_analyses_cache = {}
# Liste des agents subscribers (webhooks)
subscribers = []

def _write_temp_file(content: bytes, suffix: str):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return tmp.name

async def notify_subscribers(analysis_data: dict):
    """
    Notifie tous les agents subscribés qu'une nouvelle analyse est disponible.
    """
    for webhook_url in subscribers:
        try:
            # Appel asynchrone au webhook du subscriber
            await asyncio.to_thread(
                requests.post,
                webhook_url,
                json=analysis_data,
                timeout=5
            )
        except Exception as e:
            print(f"Erreur lors de la notification à {webhook_url}: {e}")

@app.post("/cv-reader")
async def cv_reader_endpoint(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    content = await file.read()
    tmp_path = _write_temp_file(content, suffix=ext)
    try:
        if ext in [".pdf", ".docx"]:
            result = await asyncio.to_thread(read_cv, tmp_path)
            
            analysis_id = str(uuid.uuid4())
            
            analysis_data = {
                "filename": file.filename,
                "type": "cv",
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            cv_analyses_cache[analysis_id] = analysis_data
            
            # Notifier tous les subscribers
            await notify_subscribers({
                "event": "cv_analyzed",
                "analysis_id": analysis_id,
                "filename": file.filename,
                "data": result
            })
            
            return JSONResponse(content={
                "status": "ok",
                "type": "cv",
                "analysis_id": analysis_id,
                "result": result
            })
        elif ext in [".png", ".jpg", ".jpeg"]:
            result = await asyncio.to_thread(ask_vision, tmp_path)
            
            analysis_id = str(uuid.uuid4())
            analysis_data = {
                "filename": file.filename,
                "type": "image",
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            cv_analyses_cache[analysis_id] = analysis_data
            
            await notify_subscribers({
                "event": "image_analyzed",
                "analysis_id": analysis_id,
                "filename": file.filename,
                "data": result
            })
            
            return JSONResponse(content={
                "status": "ok",
                "type": "image",
                "analysis_id": analysis_id,
                "result": result
            })
        else:
            raise HTTPException(status_code=400, detail="Format non supporté")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.post("/subscribe")
async def subscribe(webhook_url: str):
    """
    S'abonner aux notifications d'analyses.
    L'agent classifier envoie son URL webhook ici.
    """
    if webhook_url not in subscribers:
        subscribers.append(webhook_url)
        return JSONResponse(content={
            "status": "ok",
            "message": f"Souscrit à {webhook_url}",
            "subscribers": len(subscribers)
        })
    return JSONResponse(content={
        "status": "already_subscribed",
        "message": f"{webhook_url} est déjà enregistré"
    })


@app.delete("/unsubscribe")
async def unsubscribe(webhook_url: str):
    """
    Se désabonner des notifications.
    """
    if webhook_url in subscribers:
        subscribers.remove(webhook_url)
        return JSONResponse(content={
            "status": "ok",
            "message": f"Désabonné de {webhook_url}",
            "subscribers": len(subscribers)
        })
    return JSONResponse(content={
        "status": "not_found",
        "message": f"{webhook_url} n'était pas enregistré"
    })


@app.get("/subscribers")
async def list_subscribers():
    """
    Liste les agents subscribés.
    """
    return JSONResponse(content={
        "status": "ok",
        "count": len(subscribers),
        "subscribers": subscribers
    })


@app.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Récupère l'analyse stockée par son ID.
    """
    if analysis_id not in cv_analyses_cache:
        raise HTTPException(status_code=404, detail=f"Analyse {analysis_id} introuvable")
    
    analysis = cv_analyses_cache[analysis_id]
    return JSONResponse(content={
        "status": "ok",
        "analysis_id": analysis_id,
        "filename": analysis["filename"],
        "type": analysis["type"],
        "result": analysis["result"]
    })


@app.get("/analyses")
async def list_analyses():
    """
    Liste toutes les analyses disponibles en cache.
    """
    analyses_list = [
        {
            "analysis_id": aid,
            "filename": data["filename"],
            "type": data["type"]
        }
        for aid, data in cv_analyses_cache.items()
    ]
    return JSONResponse(content={
        "status": "ok",
        "count": len(analyses_list),
        "analyses": analyses_list
    })

@app.get("/results/lastest")
async def get_latest_result():
    """
    Retourne le dernier résultat analysé avec son analysis_id.
    """
    if not cv_analyses_cache:
        raise HTTPException(status_code=404, detail="Aucune analyse disponible")
    
    latest_id = list(cv_analyses_cache.keys())[-1]
    latest_data = cv_analyses_cache[latest_id]
    
    return JSONResponse(content={
        "status": "ok",
        "analysis_id": latest_id,  # ✅ L'ID est fourni
        "filename": latest_data["filename"],
        "type": latest_data["type"],
        "result": latest_data["result"]
    })


@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Supprime une analyse du cache après utilisation.
    """
    if analysis_id not in cv_analyses_cache:
        raise HTTPException(status_code=404, detail=f"Analyse {analysis_id} introuvable")
    
    del cv_analyses_cache[analysis_id]
    return JSONResponse(content={
        "status": "ok",
        "message": f"Analyse {analysis_id} supprimée"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)