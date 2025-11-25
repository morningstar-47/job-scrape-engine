"""
Exemple d'utilisation de l'API de l'assistant virtuel
Ce script montre comment interagir avec l'API REST
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
SESSION_ID = "example-session-123"


def test_chat():
    """Test de l'endpoint de chat"""
    print("=" * 50)
    print("Test de l'endpoint /chat")
    print("=" * 50)
    
    url = f"{BASE_URL}/chat"
    payload = {
        "message": "Bonjour, pouvez-vous me présenter l'assistant ?",
        "session_id": SESSION_ID
    }
    
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_chat_with_context():
    """Test avec plusieurs messages pour vérifier le contexte"""
    print("=" * 50)
    print("Test du contexte conversationnel")
    print("=" * 50)
    
    messages = [
        "Je m'appelle Alice",
        "Quel est mon nom ?",
        "Peux-tu me donner des informations sur l'assistant ?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\nMessage {i}: {message}")
        url = f"{BASE_URL}/chat"
        payload = {
            "message": message,
            "session_id": SESSION_ID
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse: {data['answer'][:200]}...")
        else:
            print(f"Erreur: {response.status_code}")
    print()


def test_history():
    """Test de récupération de l'historique"""
    print("=" * 50)
    print("Test de l'historique de session")
    print("=" * 50)
    
    url = f"{BASE_URL}/chat/session/{SESSION_ID}/history"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Session ID: {data['session_id']}")
        print(f"Nombre de messages: {data['count']}")
        print("\nMessages:")
        for msg in data['messages']:
            print(f"  [{msg['role']}]: {msg['content'][:100]}...")
    else:
        print(f"Erreur: {response.status_code}")
    print()


def test_upload_text():
    """Test d'upload de texte à la base de connaissances"""
    print("=" * 50)
    print("Test d'upload de texte")
    print("=" * 50)
    
    url = f"{BASE_URL}/knowledge/upload-text"
    payload = {
        "text": "L'assistant virtuel est un système intelligent qui utilise LangChain et OpenAI pour fournir des réponses pertinentes.",
        "metadata": {
            "source": "exemple",
            "type": "documentation"
        }
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Succès: {data['message']}")
        print(f"IDs des documents: {data['document_ids']}")
    else:
        print(f"Erreur: {response.status_code} - {response.text}")
    print()


def test_health():
    """Test de l'endpoint de santé"""
    print("=" * 50)
    print("Test de l'endpoint /health")
    print("=" * 50)
    
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Services: {json.dumps(data['services'], indent=2)}")
    else:
        print(f"Erreur: {response.status_code}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Exemples d'utilisation de l'API Assistant Virtuel")
    print("=" * 50 + "\n")
    
    try:
        # Vérifier que le serveur est accessible
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("⚠️  Le serveur ne semble pas être démarré.")
            print(f"   Démarrez-le avec: uvicorn app.main:app --reload")
            exit(1)
        
        # Exécuter les tests
        test_health()
        test_chat()
        test_chat_with_context()
        test_history()
        test_upload_text()
        
        print("=" * 50)
        print("Tests terminés avec succès!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur.")
        print(f"   Assurez-vous que le serveur est démarré sur {BASE_URL}")
        print(f"   Démarrez-le avec: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Erreur: {e}")

