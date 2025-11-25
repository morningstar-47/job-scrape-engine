# consumer_agent_v2.py
import requests
import json

NGROK_URL = "https://advantageous-nonrhetorically-tommie.ngrok-free.dev/" 
ENDPOINT = f"{NGROK_URL}/results/lastest"

def get_json_from_parser():
    """
    Fait une requête GET à l'API de l'Agent 1 pour recevoir le JSON.
    """
    print(f"Tentative de récupération du JSON depuis: **{ENDPOINT}**")
    
    try:
        # Faire la requête GET
        response = requests.get(ENDPOINT)

        # Vérifier le statut de la requête
        if response.status_code == 200:
            print("\n✅ JSON reçu avec succès!")
            
            cv_json_data = response.json()
            print("--- JSON reçu ---")
            print(json.dumps(cv_json_data, indent=4))
            print("------------------")
            
            return cv_json_data
        else:
            print(f"\n❌ Échec de la requête. Code de statut: {response.status_code}")
            print("Détails de l'erreur:", response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erreur de connexion (ngrok ou API non disponible): {e}")