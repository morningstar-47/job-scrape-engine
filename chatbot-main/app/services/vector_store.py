"""
Service de gestion de la base de données vectorielle
Utilise ChromaDB pour stocker et rechercher des documents
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document
from typing import List, Optional
import os
from app.config import settings


class VectorStoreService:
    """Service pour gérer la base de données vectorielle"""
    
    def __init__(self):
        """Initialise le service avec ChromaDB et OpenAI Embeddings"""
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-ada-002"
        )
        self.persist_directory = settings.chroma_persist_directory
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store: Optional[Chroma] = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialise ou charge la base de données vectorielle"""
        try:
            # Essayer de charger une base existante
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
            else:
                # Créer une nouvelle base vide
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
        except Exception:
            # En cas d'erreur, créer une nouvelle base
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Ajoute des documents à la base vectorielle
        
        Args:
            documents: Liste de documents LangChain à ajouter
            
        Returns:
            Liste des IDs des documents ajoutés
        """
        if not documents:
            return []
        
        # Diviser les documents en chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Ajouter à la base vectorielle
        if self.vector_store is None:
            self._initialize_vector_store()
        
        ids = self.vector_store.add_documents(chunks)
        # La persistance est automatique avec persist_directory dans ChromaDB moderne
        
        return ids
    
    def add_text(self, text: str, metadata: Optional[dict] = None) -> List[str]:
        """
        Ajoute un texte à la base vectorielle
        
        Args:
            text: Texte à ajouter
            metadata: Métadonnées optionnelles
            
        Returns:
            Liste des IDs des documents ajoutés
        """
        document = Document(page_content=text, metadata=metadata or {})
        return self.add_documents([document])
    
    def add_file(self, file_path: str, metadata: Optional[dict] = None) -> List[str]:
        """
        Charge et ajoute un fichier à la base vectorielle
        
        Args:
            file_path: Chemin vers le fichier
            metadata: Métadonnées optionnelles
            
        Returns:
            Liste des IDs des documents ajoutés
        """
        file_metadata = metadata or {}
        file_metadata["source"] = file_path
        
        # Charger le fichier selon son type
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            # Par défaut, traiter comme texte
            loader = TextLoader(file_path, encoding='utf-8')
        
        documents = loader.load()
        
        # Ajouter les métadonnées
        for doc in documents:
            doc.metadata.update(file_metadata)
        
        return self.add_documents(documents)
    
    def search(self, query: str, k: int = None) -> List[Document]:
        """
        Recherche des documents similaires dans la base vectorielle
        
        Args:
            query: Requête de recherche
            k: Nombre de documents à retourner (défaut: settings.retriever_k)
            
        Returns:
            Liste des documents les plus similaires
        """
        if self.vector_store is None:
            return []
        
        k = k or settings.retriever_k
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def search_with_scores(self, query: str, k: int = None) -> List[tuple]:
        """
        Recherche des documents avec leurs scores de similarité
        
        Args:
            query: Requête de recherche
            k: Nombre de documents à retourner
            
        Returns:
            Liste de tuples (document, score)
        """
        if self.vector_store is None:
            return []
        
        k = k or settings.retriever_k
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"Erreur lors de la recherche avec scores: {e}")
            return []
    
    def get_retriever(self, k: int = None):
        """
        Retourne un retriever LangChain pour la récupération de contexte
        
        Args:
            k: Nombre de documents à récupérer
            
        Returns:
            Retriever LangChain
        """
        if self.vector_store is None:
            self._initialize_vector_store()
        
        k = k or settings.retriever_k
        
        return self.vector_store.as_retriever(
            search_kwargs={"k": k}
        )
    
    def delete_collection(self):
        """Supprime toute la collection (pour réinitialisation)"""
        if self.vector_store is None:
            return
        
        try:
            self.vector_store.delete_collection()
            self.vector_store = None
            self._initialize_vector_store()
        except Exception as e:
            print(f"Erreur lors de la suppression: {e}")


# Instance globale du service
vector_store_service = VectorStoreService()

