"""
Exemple de test pour la recherche d'emploi dans le chat
"""
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "test-job-search-123"


def test_job_search_in_chat():
    """Test de recherche d'emploi via le chat"""
    print("=" * 60)
    print("Test de recherche d'emploi dans le chat")
    print("=" * 60)
    
    test_messages = [
        "Je cherche un emploi de développeur Python en France",
        "Trouve-moi des postes de data scientist en télétravail",
        "Y a-t-il des offres d'emploi pour ingénieur logiciel à Paris ?",
        "Recherche des emplois de designer UX remote"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {message}")
        print('='*60)
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={
                    "message": message,
                    "session_id": SESSION_ID
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Réponse de l'assistant:")
                print(f"{data.get('answer', 'N/A')[:500]}...")
                
                if data.get('job_search'):
                    job_data = data['job_search']
                    print(f"\n📊 Résultats de recherche d'emploi:")
                    print(f"   - Recherche: {job_data.get('query')}")
                    print(f"   - Pays: {job_data.get('country', 'N/A')}")
                    print(f"   - Total trouvé: {job_data.get('total', 0)}")
                    print(f"   - Emplois retournés: {len(job_data.get('jobs', []))}")
                    
                    if job_data.get('jobs'):
                        print(f"\n   Emplois trouvés:")
                        for j, job in enumerate(job_data.get('jobs', [])[:3], 1):
                            print(f"   {j}. {job.get('job_title')} chez {job.get('employer_name')}")
                else:
                    print("\nℹ️  Aucune recherche d'emploi détectée dans cette requête")
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print(response.text)
        
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter au serveur")
            print("   Assurez-vous que le serveur est démarré: uvicorn app.main:app --reload")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Test de recherche d'emploi intégrée dans le chat")
    print("=" * 60 + "\n")
    
    try:
        # Vérifier que le serveur est accessible
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("⚠️  Le serveur ne semble pas être démarré.")
            print(f"   Démarrez-le avec: uvicorn app.main:app --reload")
            exit(1)
        
        test_job_search_in_chat()
        
        print("=" * 60)
        print("Tests terminés!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur.")
        print(f"   Assurez-vous que le serveur est démarré sur {BASE_URL}")
        print(f"   Démarrez-le avec: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Erreur: {e}")

