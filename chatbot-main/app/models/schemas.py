"""
Modèles Pydantic pour les requêtes et réponses de l'API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Modèle pour une requête de chat"""
    message: str = Field(..., description="Message de l'utilisateur", min_length=1)
    session_id: str = Field(default="default", description="Identifiant de la session")


class ChatResponse(BaseModel):
    """Modèle pour une réponse de chat"""
    answer: str = Field(..., description="Réponse de l'assistant")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Sources utilisées pour la réponse")
    session_id: str = Field(..., description="Identifiant de la session")
    error: Optional[str] = Field(None, description="Message d'erreur éventuel")
    job_search: Optional[Dict[str, Any]] = Field(None, description="Résultats de recherche d'emploi si applicable")


class Message(BaseModel):
    """Modèle pour un message dans l'historique"""
    role: str = Field(..., description="Rôle (user ou assistant)")
    content: str = Field(..., description="Contenu du message")
    timestamp: Optional[str] = Field(None, description="Horodatage du message")


class ChatHistoryResponse(BaseModel):
    """Modèle pour l'historique d'une session"""
    session_id: str = Field(..., description="Identifiant de la session")
    messages: List[Message] = Field(default_factory=list, description="Liste des messages")
    count: int = Field(..., description="Nombre de messages")


class DocumentUpload(BaseModel):
    """Modèle pour l'upload de document"""
    text: Optional[str] = Field(None, description="Texte à ajouter directement")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Métadonnées du document")


class DocumentUploadResponse(BaseModel):
    """Modèle pour la réponse après upload de document"""
    success: bool = Field(..., description="Indique si l'upload a réussi")
    document_ids: List[str] = Field(default_factory=list, description="IDs des documents ajoutés")
    message: str = Field(..., description="Message de confirmation")


class SessionInfo(BaseModel):
    """Modèle pour les informations d'une session"""
    session_id: str = Field(..., description="Identifiant de la session")
    message_count: int = Field(..., description="Nombre de messages dans la session")


class ErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur"""
    error: str = Field(..., description="Message d'erreur")
    detail: Optional[str] = Field(None, description="Détails supplémentaires de l'erreur")

