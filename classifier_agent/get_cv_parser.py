# File to connect agents to resume parser

import requests


NGROK_URL = "https://advantageous-nonrhetorically-tommie.ngrok-free.dev/" 
ENDPOINT = f"{NGROK_URL}/results/lastest"

def get_json_from_parser():
    """
    Fait une requête GET à l'API du CV Parser pour recevoir le JSON.
    """    
    try:
        # Faire la requête GET
        response = requests.get(ENDPOINT)

        # Vérifier le statut de la requête
        if response.status_code == 200:
            print("\n✅ JSON reçu avec succès!")
            
            cv_json_data = response.json()
            
            return cv_json_data
        else:
            print(f"\n❌ Échec de la requête. Code de statut: {response.status_code}")
            print("Détails de l'erreur:", response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erreur de connexion (ngrok ou API non disponible): {e}")