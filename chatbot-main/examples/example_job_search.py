"""
Exemple d'utilisation de l'API de recherche d'emploi
"""
import requests

# Configuration
BASE_URL = "http://localhost:8000"


def test_job_search():
    """Test de recherche d'emploi basique"""
    print("=" * 50)
    print("Test de recherche d'emploi")
    print("=" * 50)
    
    url = f"{BASE_URL}/jobs/search"
    params = {
        "query": "développeur Python",
        "location": "Paris, France",
        "num_pages": 1
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Nombre d'emplois trouvés: {data.get('total', 0)}")
        
        jobs = data.get("jobs", [])[:3]  # Afficher les 3 premiers
        for i, job in enumerate(jobs, 1):
            print(f"\n--- Emploi {i} ---")
            print(f"Titre: {job.get('job_title', 'N/A')}")
            print(f"Entreprise: {job.get('employer_name', 'N/A')}")
            print(f"Localisation: {job.get('job_city', 'N/A')}, {job.get('job_state', 'N/A')}")
            print(f"Type: {job.get('job_employment_type', 'N/A')}")
            if job.get('job_is_remote'):
                print("Télétravail: Oui")
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)
    print()


def test_job_search_summary():
    """Test de recherche avec résumé formaté"""
    print("=" * 50)
    print("Test de recherche avec résumé")
    print("=" * 50)
    
    url = f"{BASE_URL}/jobs/search/summary"
    params = {
        "query": "data scientist",
        "location": "Lyon, France",
        "limit": 5
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Recherche: {data.get('query')}")
        print(f"Localisation: {data.get('location', 'Toutes')}")
        print(f"Total trouvé: {data.get('total_found', 0)}")
        print("\nRésultats:")
        
        for i, result in enumerate(data.get("results", []), 1):
            print(f"\n{i}. {result.get('summary', 'N/A')}")
            if result.get('job_apply_link'):
                print(f"   Lien: {result.get('job_apply_link')}")
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)
    print()


def test_job_search_remote():
    """Test de recherche d'emplois à distance"""
    print("=" * 50)
    print("Test de recherche d'emplois à distance")
    print("=" * 50)
    
    url = f"{BASE_URL}/jobs/search"
    params = {
        "query": "développeur web",
        "remote_jobs_only": True,
        "num_pages": 1
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Nombre d'emplois à distance trouvés: {data.get('total', 0)}")
        
        jobs = data.get("jobs", [])[:3]
        for i, job in enumerate(jobs, 1):
            print(f"\n--- Emploi {i} ---")
            print(f"Titre: {job.get('job_title', 'N/A')}")
            print(f"Entreprise: {job.get('employer_name', 'N/A')}")
            print(f"Télétravail: {'Oui' if job.get('job_is_remote') else 'Non'}")
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Exemples d'utilisation de l'API de recherche d'emploi")
    print("=" * 50 + "\n")
    
    try:
        # Vérifier que le serveur est accessible
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("⚠️  Le serveur ne semble pas être démarré.")
            print(f"   Démarrez-le avec: uvicorn app.main:app --reload")
            exit(1)
        
        # Exécuter les tests
        test_job_search()
        test_job_search_summary()
        test_job_search_remote()
        
        print("=" * 50)
        print("Tests terminés avec succès!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur.")
        print(f"   Assurez-vous que le serveur est démarré sur {BASE_URL}")
        print(f"   Démarrez-le avec: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Erreur: {e}")

