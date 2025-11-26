"""
Service LLM avec LangChain
Gère l'intégration avec OpenAI et la chaîne conversationnelle avec RAG
"""
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
from typing import Optional, Dict, Any
from app.config import settings
from app.services.vector_store import vector_store_service
from app.services.memory_service import memory_service
from app.services.job_search_service import job_search_service
from app.services.job_intent_detector import job_intent_detector


class LLMService:
    """Service pour gérer les interactions avec le LLM"""
    
    def __init__(self):
        """Initialise le service LLM avec OpenAI"""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key
        )
        self.qa_chain: Optional[ConversationalRetrievalChain] = None
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialise la chaîne conversationnelle avec récupération de contexte"""
        # Template de prompt pour la question-réponse amélioré
        template = """Vous êtes un assistant virtuel intelligent qui utilise un système RAG (Retrieval-Augmented Generation) pour fournir des réponses précises et contextuelles.

INSTRUCTIONS IMPORTANTES:
- Utilisez TOUJOURS les informations du contexte fourni ci-dessous pour répondre à la question
- Si le contexte contient des informations pertinentes, basez votre réponse sur ces informations
- Répondez de manière claire, détaillée et utile en français
- Si le contexte ne contient pas d'informations pertinentes, dites-le poliment mais essayez quand même de répondre avec vos connaissances générales si approprié
- Si des recherches d'emploi sont mentionnées dans le contexte, l'utilisateur peut vous poser des questions sur ces emplois (ex: "Donne-moi plus de détails sur le premier emploi", "Quel est le salaire du poste chez X?", "Montre-moi les emplois en télétravail")
- Référencez les emplois par leur numéro (Emploi 1, Emploi 2, etc.) ou par leur titre/entreprise
- Chaque session utilisateur est isolée : ne mélangez jamais les informations entre différentes sessions

CONTEXTE RÉCUPÉRÉ DEPUIS LA BASE DE CONNAISSANCES:
{context}

QUESTION DE L'UTILISATEUR: {question}

RÉPONSE (en français, détaillée et basée sur le contexte fourni):"""
        
        QA_PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Créer le retriever depuis le vector store
        try:
            retriever = vector_store_service.get_retriever()
            
            # Créer la chaîne conversationnelle avec RAG
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=None,  # La mémoire sera gérée manuellement par session
                combine_docs_chain_kwargs={"prompt": QA_PROMPT},
                return_source_documents=True,
                verbose=False
            )
        except Exception as e:
            print(f"Attention: Impossible d'initialiser le RAG: {e}")
            print("Le système fonctionnera sans récupération de contexte.")
            self.qa_chain = None
    
    def chat(self, question: str, session_id: str) -> Dict[str, Any]:
        """
        Envoie une question au LLM et retourne la réponse avec le contexte
        
        Args:
            question: Question de l'utilisateur
            session_id: Identifiant de la session pour la mémoire
            
        Returns:
            Dictionnaire contenant la réponse, les sources et l'historique
        """
        if self.qa_chain is None:
            self._initialize_chain()
        
        # Récupérer le contexte des recherches d'emploi précédentes pour cette session
        previous_job_context = memory_service.get_job_search_context(session_id)
        
        # Détecter si l'utilisateur demande une recherche d'emploi
        is_job_search, job_params = job_intent_detector.detect_job_search_intent(question)
        job_results_text = ""
        job_search_results = None
        
        if is_job_search and job_params:
            # Effectuer la recherche d'emploi
            try:
                job_search_results = job_search_service.search_jobs(
                    query=job_params.get('query', ''),
                    country=job_params.get('country'),
                    language='fr',
                    num_pages=1,
                    employment_types=job_params.get('employment_type'),
                    remote_jobs_only=job_params.get('remote', False)
                )
                
                if job_search_results and job_search_results.get('jobs'):
                    jobs = job_search_results.get('jobs', [])[:5]  # Limiter à 5 résultats
                    
                    # Mémoriser la recherche d'emploi pour cette session (TOUS les détails des emplois)
                    memory_service.add_job_search(session_id, {
                        'query': job_search_results.get('query', job_params.get('query', '')),
                        'country': job_search_results.get('country', job_params.get('country')),
                        'total': job_search_results.get('total', 0),
                        'jobs': jobs  # Stocker avec tous les détails (description, salaire, etc.)
                    })
                    
                    job_results_text = "\n\nRÉSULTATS DE RECHERCHE D'EMPLOI:\n"
                    job_results_text += f"Recherche: {job_search_results.get('query', '')}\n"
                    if job_search_results.get('country'):
                        job_results_text += f"Pays: {job_search_results.get('country')}\n"
                    job_results_text += f"Nombre d'emplois trouvés: {len(jobs)}\n\n"
                    
                    for i, job in enumerate(jobs, 1):
                        job_results_text += f"{i}. {job.get('job_title', 'N/A')} chez {job.get('employer_name', 'N/A')}\n"
                        location_parts = [job.get('job_city'), job.get('job_state'), job.get('job_country')]
                        location = ', '.join([p for p in location_parts if p])
                        if location:
                            job_results_text += f"   Localisation: {location}\n"
                        if job.get('job_is_remote'):
                            job_results_text += "   Télétravail: Oui\n"
                        if job.get('job_employment_type'):
                            job_results_text += f"   Type: {job.get('job_employment_type')}\n"
                        if job.get('job_apply_link'):
                            job_results_text += f"   Lien: {job.get('job_apply_link')}\n"
                        job_results_text += "\n"
            except Exception as e:
                print(f"Erreur lors de la recherche d'emploi: {e}")
                job_results_text = "\n\nNote: La recherche d'emploi n'a pas pu être effectuée.\n"
        
        # Si le RAG n'est pas disponible, utiliser le fallback
        if self.qa_chain is None:
            return self.chat_without_rag(question, session_id, job_results_text)
        
        # Récupérer la mémoire de la session (charge depuis la DB si nécessaire)
        memory = memory_service.get_memory(session_id)
        
        # Vérifier que l'historique est bien chargé
        chat_history = memory.messages if memory.messages else []
        
        # Debug: afficher le nombre de messages dans l'historique
        if settings.debug:
            print(f"[DEBUG] Session {session_id}: {len(chat_history)} messages dans l'historique")
        
        # Intégrer les résultats d'emploi et le contexte des recherches précédentes dans la question
        enhanced_question = question
        
        # Ajouter le contexte des recherches précédentes si disponible
        if previous_job_context:
            enhanced_question = f"{enhanced_question}\n\n{previous_job_context}"
        
        # Ajouter les résultats de la recherche actuelle si disponibles
        if job_results_text:
            enhanced_question = f"{enhanced_question}\n\n{job_results_text}\n\nVeuillez présenter ces résultats d'emploi de manière claire et organisée dans votre réponse."
        
        # Préparer les inputs avec l'historique
        # ConversationalRetrievalChain attend chat_history comme une liste de messages
        inputs = {
            "question": enhanced_question,
            "chat_history": chat_history
        }
        
        try:
            # Exécuter la chaîne
            result = self.qa_chain.invoke(inputs)
            
            answer = result.get("answer", "Désolé, je n'ai pas pu générer de réponse.")
            source_documents = result.get("source_documents", [])
            
            # Extraire les sources utilisées (dédupliquer par contenu)
            sources = []
            seen_contents = set()
            for doc in source_documents:
                # Normaliser le contenu pour la déduplication
                content_preview = doc.page_content[:200] if len(doc.page_content) > 200 else doc.page_content
                content_hash = hash(doc.page_content.strip())
                
                # Éviter les doublons
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    source_info = {
                        "content": content_preview + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    sources.append(source_info)
            
            # Ajouter à la mémoire
            memory_service.add_message(session_id, question, answer)
            
            response_data = {
                "answer": answer,
                "sources": sources,
                "session_id": session_id
            }
            
            # Ajouter les résultats de recherche d'emploi si disponibles
            if job_search_results:
                response_data["job_search"] = {
                    "query": job_search_results.get("query"),
                    "country": job_search_results.get("country"),
                    "total": job_search_results.get("total", 0),
                    "jobs": job_search_results.get("jobs", [])[:5]  # Limiter à 5 pour la réponse
                }
            
            return response_data
        
        except Exception as e:
            error_message = f"Erreur lors du traitement de la question: {str(e)}"
            print(error_message)
            
            # En cas d'erreur, essayer une réponse simple sans RAG
            try:
                simple_response = self.llm.invoke(question)
                answer = simple_response.content if hasattr(simple_response, 'content') else str(simple_response)
                
                memory_service.add_message(session_id, question, answer)
                
                return {
                    "answer": answer,
                    "sources": [],
                    "session_id": session_id,
                    "error": "RAG non disponible, réponse directe du LLM"
                }
            except Exception as e2:
                return {
                    "answer": "Désolé, une erreur s'est produite. Veuillez réessayer.",
                    "sources": [],
                    "session_id": session_id,
                    "error": str(e2)
                }
    
    def chat_without_rag(self, question: str, session_id: str, job_results: str = "") -> Dict[str, Any]:
        """
        Chat simple sans récupération de contexte (fallback)
        
        Args:
            question: Question de l'utilisateur
            session_id: Identifiant de la session
            job_results: Résultats de recherche d'emploi formatés (optionnel)
            
        Returns:
            Dictionnaire contenant la réponse
        """
        # Récupérer le contexte des recherches d'emploi précédentes
        previous_job_context = memory_service.get_job_search_context(session_id)
        
        # Détecter si l'utilisateur demande une recherche d'emploi (si pas déjà fait)
        if not job_results:
            is_job_search, job_params = job_intent_detector.detect_job_search_intent(question)
            if is_job_search and job_params:
                try:
                    job_search_results = job_search_service.search_jobs(
                        query=job_params.get('query', ''),
                        country=job_params.get('country'),
                        language='fr',
                        num_pages=1,
                        employment_types=job_params.get('employment_type'),
                        remote_jobs_only=job_params.get('remote', False)
                    )
                    
                    # Mémoriser la recherche d'emploi pour cette session
                    if job_search_results:
                        memory_service.add_job_search(session_id, {
                            'query': job_search_results.get('query', job_params.get('query', '')),
                            'country': job_search_results.get('country', job_params.get('country')),
                            'total': job_search_results.get('total', 0),
                            'jobs': job_search_results.get('jobs', [])[:5]
                        })
                    
                    if job_search_results and job_search_results.get('jobs'):
                        jobs = job_search_results.get('jobs', [])[:5]
                        job_results = "\n\nRÉSULTATS DE RECHERCHE D'EMPLOI:\n"
                        job_results += f"Recherche: {job_search_results.get('query', '')}\n"
                        if job_search_results.get('country'):
                            job_results += f"Pays: {job_search_results.get('country')}\n"
                        job_results += f"Nombre d'emplois trouvés: {len(jobs)}\n\n"
                        
                        for i, job in enumerate(jobs, 1):
                            job_results += f"{i}. {job.get('job_title', 'N/A')} chez {job.get('employer_name', 'N/A')}\n"
                            location_parts = [job.get('job_city'), job.get('job_state'), job.get('job_country')]
                            location = ', '.join([p for p in location_parts if p])
                            if location:
                                job_results += f"   Localisation: {location}\n"
                            if job.get('job_is_remote'):
                                job_results += "   Télétravail: Oui\n"
                            if job.get('job_apply_link'):
                                job_results += f"   Lien: {job.get('job_apply_link')}\n"
                            job_results += "\n"
                except Exception as e:
                    print(f"Erreur lors de la recherche d'emploi: {e}")
        
        # Récupérer l'historique
        history = memory_service.get_history(session_id)
        
        # Construire le contexte depuis l'historique
        context = ""
        if history:
            for msg in history[-6:]:  # Derniers 6 messages
                if hasattr(msg, 'content'):
                    role = "Utilisateur" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                    context += f"{role}: {msg.content}\n"
        
        # Construire le prompt avec le contexte des recherches précédentes
        prompt_context = context
        if previous_job_context:
            prompt_context += f"\n{previous_job_context}"
        if job_results:
            prompt_context += f"\n{job_results}"
        
        # Construire le prompt
        prompt = f"{prompt_context}\nUtilisateur: {question}\nAssistant:"
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            memory_service.add_message(session_id, question, answer)
            
            return {
                "answer": answer,
                "sources": [],
                "session_id": session_id
            }
        except Exception as e:
            return {
                "answer": "Désolé, une erreur s'est produite.",
                "sources": [],
                "session_id": session_id,
                "error": str(e)
            }


# Instance globale du service
llm_service = LLMService()

