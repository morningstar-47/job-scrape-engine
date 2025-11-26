import http.client
import urllib.parse
import os
import json
from dotenv import load_dotenv
load_dotenv()

def search_jobs(query, city, num_pages, country="fr", date_posted="all", language="fr", remote_jobs_only=False):
    """
    Recherche des offres d'emploi via RapidAPI JSearch.
    
    Args:
        query: Requête de recherche (ex: "data scientist à Paris")
        city: Ville pour la recherche
        num_pages: Nombre de pages de résultats
        country: Code pays (défaut: "fr")
        date_posted: Date de publication ("all", "today", "3days", "week", "month")
        language: Langue de la recherche (défaut: "fr")
        remote_jobs_only: Rechercher uniquement les offres en télétravail (défaut: False)
    
    Returns:
        str: Réponse JSON en string
    """
    try:
        conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")

        # Utiliser directement la query générée par le LLM
        # La query doit contenir uniquement le poste/métier (ex: "comptabilité", "comptable")
        # On ajoute la ville seulement si elle n'est pas déjà présente dans la query
        search_query = query.strip()
        
        # Si la query contient "à" suivi d'une ville, on la garde telle quelle
        # Sinon, on ajoute la ville pour la recherche
        if " à " in search_query.lower() or search_query.lower().endswith(f" à {city.lower()}"):
            # La ville est déjà dans la query, on la garde
            pass
        elif city and city.lower() not in search_query.lower():
            # Ajouter la ville pour affiner la recherche
            search_query = f"{search_query} {city}"

        params = {
            "query": search_query,
            "num_pages": num_pages,
            "country": country,
            "language": language,
            "remote_jobs_only": str(remote_jobs_only).lower(),
            "date_posted": date_posted
        }

        query_string = urllib.parse.urlencode(params)

        headers = {
            'x-rapidapi-key': os.getenv("JOB_SCRAPPER_API_KEY"),
            'x-rapidapi-host': "jsearch.p.rapidapi.com"
        }

        print(f"🔍 Recherche d'offres avec la requête: {search_query}")
        print(f"📋 Paramètres: pages={num_pages}, country={country}, language={language}, remote_jobs_only={remote_jobs_only}")
        print(f"🌐 URL complète: /search?{query_string}")

        conn.request("GET", f"/search?{query_string}", headers=headers)
        res = conn.getresponse()
        
        # Vérifier le status code
        status_code = res.status
        print(f"📡 Status code API: {status_code}")
        
        if status_code != 200:
            error_data = res.read().decode("utf-8")
            print(f"❌ Erreur API: {error_data}")
            raise Exception(f"Erreur API JSearch (status {status_code}): {error_data}")
        
        data = res.read()
        response_text = data.decode("utf-8")
        
        # Vérifier que c'est du JSON valide
        try:
            json_data = json.loads(response_text)
            print(f"✅ Réponse reçue: {len(json_data.get('data', []))} offres trouvées")
            return response_text
        except json.JSONDecodeError as e:
            print(f"❌ Réponse non-JSON reçue: {response_text[:200]}")
            raise Exception(f"Réponse invalide de l'API (non-JSON): {str(e)}")
            
    except http.client.HTTPException as e:
        print(f"❌ Erreur HTTP: {e}")
        raise Exception(f"Erreur de connexion HTTP: {str(e)}")
    except Exception as e:
        print(f"❌ Erreur lors de la recherche d'offres: {e}")
        raise