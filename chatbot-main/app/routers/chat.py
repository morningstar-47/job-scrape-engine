"""
Routes API pour le chat et la gestion des sessions
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import os
from datetime import datetime

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    DocumentUpload,
    DocumentUploadResponse,
    SessionInfo,
    Message
)
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.services.vector_store import vector_store_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Envoie un message à l'assistant et reçoit une réponse
    
    - **message**: Le message de l'utilisateur
    - **session_id**: Identifiant de la session (optionnel, "default" par défaut)
    """
    try:
        result = llm_service.chat(
            question=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du message: {str(e)}"
        )


@router.post("/session/{session_id}", response_model=ChatResponse)
async def chat_with_session(session_id: str, request: ChatRequest):
    """
    Envoie un message pour une session spécifique
    
    - **session_id**: Identifiant de la session dans l'URL
    - **message**: Le message de l'utilisateur
    """
    try:
        # Utiliser le session_id de l'URL plutôt que celui du body
        result = llm_service.chat(
            question=request.message,
            session_id=session_id
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du message: {str(e)}"
        )


@router.get("/session/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    Récupère l'historique de conversation d'une session
    
    - **session_id**: Identifiant de la session
    """
    try:
        history = memory_service.get_history(session_id)
        
        messages = []
        for msg in history:
            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            messages.append(Message(
                role=role,
                content=content,
                timestamp=datetime.now().isoformat()
            ))
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            count=len(messages)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )


@router.get("/session/{session_id}/job-searches")
async def get_job_search_history(session_id: str):
    """
    Récupère l'historique des recherches d'emploi d'une session
    
    Returns:
        Liste des recherches d'emploi effectuées dans cette session
    """
    try:
        from app.services.memory_service import memory_service
        
        searches = memory_service.get_job_search_history(session_id)
        
        return {
            "session_id": session_id,
            "job_searches": searches,
            "count": len(searches)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Réinitialise la mémoire d'une session
    
    - **session_id**: Identifiant de la session à réinitialiser
    """
    try:
        memory_service.clear_session(session_id)
        
        return {
            "message": f"Session {session_id} réinitialisée avec succès",
            "session_id": session_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la réinitialisation de la session: {str(e)}"
        )


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    Liste toutes les sessions actives avec leur nombre de messages
    """
    try:
        sessions = []
        for session_id in memory_service.memories.keys():
            history = memory_service.get_history(session_id)
            sessions.append(SessionInfo(
                session_id=session_id,
                message_count=len(history)
            ))
        
        return sessions
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des sessions: {str(e)}"
        )


# Routes pour la base de connaissances
router_knowledge = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router_knowledge.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Ajoute un document à la base de connaissances
    
    Vous pouvez soit:
    - Uploader un fichier (PDF, TXT)
    - Envoyer du texte directement via le paramètre 'text'
    """
    try:
        document_ids = []
        
        if file and file.filename:
            # Sauvegarder le fichier temporairement
            upload_dir = "data/knowledge_base"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, file.filename)
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Ajouter à la base vectorielle
            ids = vector_store_service.add_file(file_path)
            document_ids.extend(ids)
            
            message = f"Fichier {file.filename} ajouté avec succès"
        
        elif text:
            # Ajouter le texte directement
            ids = vector_store_service.add_text(text)
            document_ids.extend(ids)
            message = "Texte ajouté avec succès"
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Vous devez fournir soit un fichier, soit du texte"
            )
        
        return DocumentUploadResponse(
            success=True,
            document_ids=document_ids,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload du document: {str(e)}"
        )


@router_knowledge.post("/upload-text", response_model=DocumentUploadResponse)
async def upload_text(request: DocumentUpload):
    """
    Ajoute du texte directement à la base de connaissances
    
    - **text**: Le texte à ajouter
    - **metadata**: Métadonnées optionnelles
    """
    try:
        if not request.text:
            raise HTTPException(
                status_code=400,
                detail="Le champ 'text' est requis"
            )
        
        ids = vector_store_service.add_text(
            text=request.text,
            metadata=request.metadata
        )
        
        return DocumentUploadResponse(
            success=True,
            document_ids=ids,
            message=f"Texte ajouté avec succès ({len(ids)} chunks créés)"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'ajout du texte: {str(e)}"
        )


@router_knowledge.delete("/reset")
async def reset_knowledge_base():
    """
    Réinitialise complètement la base de connaissances
    ⚠️ Attention: Cette action supprime toutes les données!
    """
    try:
        vector_store_service.delete_collection()
        
        return {
            "message": "Base de connaissances réinitialisée avec succès"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la réinitialisation: {str(e)}"
        )

