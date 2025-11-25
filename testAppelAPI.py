from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import time
import json

classifier_app = FastAPI(title="Classifier Agent")

CV_READER_API = "https://advantageous-nonrhetorically-tommie.ngrok-free.dev"
WEBHOOK_URL = "http://localhost:8001/webhook/cv-analyzed"

last_analysis = {}

@classifier_app.on_event("startup")
async def subscribe_to_cv_reader():
    """
    Au démarrage, s'abonner aux notifications du CV Reader avec retry.
    """
    max_retries = 6
    delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                f"{CV_READER_API}/subscribe",
                params={"webhook_url": WEBHOOK_URL}
            )
            print(f"✅ Subscribé au CV Reader: {response.json()}")
            return
        except Exception as e:
            print(f"Tentative {attempt}/{max_retries} échouée: {e}")
            if attempt < max_retries:
                time.sleep(delay)

@classifier_app.post("/webhook/cv-analyzed")
async def handle_cv_analyzed(request: Request):
    """
    Webhook appelé automatiquement quand un CV est analysé.
    Reçoit l'analyse JSON directement.
    """
    event = await request.json()
    
    print(f"\n🔔 Nouvelle analyse reçue !")
    print(f"📄 Fichier: {event.get('filename')}")
    
    # Récupérer les données de l'analyse
    analysis_data = event.get("data", {})
    analysis_id = event.get("analysis_id")
    
    # Parser si c'est une string JSON
    if isinstance(analysis_data, str):
        try:
            analysis_data = json.loads(analysis_data)
        except Exception:
            analysis_data = {}
    
    # Appliquer la logique de classification
    classification_result = classify_cv(analysis_data, analysis_id)
    
    # Stocker la dernière analyse
    last_analysis.clear()
    last_analysis.update({
        "analysis_id": analysis_id,
        "filename": event.get("filename"),
        "classification": classification_result
    })
    
    print(f"✅ Classification effectuée:")
    print(json.dumps(classification_result, indent=2, ensure_ascii=False))
    
    return JSONResponse(content={
        "status": "ok",
        "classification": classification_result
    })


def classify_cv(analysis_data: dict, analysis_id: str) -> dict:
    """
    Classifie le CV analysé.
    """
    return {
        "analysis_id": analysis_id,
        "processed_at": time.time(),
        "type_poste": analysis_data.get("type_poste", []),
        "ville_candidat": analysis_data.get("ville_candidat", []),
        "description_candidat": analysis_data.get("description_candidat", []),
        "competences": analysis_data.get("competences", []),
        "experience": analysis_data.get("experience", []),
        "query": analysis_data.get("Query", "")
    }


@classifier_app.get("/last")
async def get_last_analysis():
    """
    Retourne la dernière analyse reçue.
    """
    return JSONResponse(content={"status": "ok", "last_analysis": last_analysis})


@classifier_app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Classifier Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("testAppelAPI:classifier_app", host="0.0.0.0", port=8001, reload=True)