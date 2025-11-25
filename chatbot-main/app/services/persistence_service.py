"""
Service de persistance pour les conversations et sessions
Utilise SQLite pour stocker les données de manière persistante
"""
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from app.config import settings


class PersistenceService:
    """Service pour gérer la persistance des conversations et sessions dans SQLite"""
    
    def __init__(self, db_path: str = None):
        """
        Initialise le service de persistance
        
        Args:
            db_path: Chemin vers la base de données SQLite (par défaut: ./sessions.db)
        """
        self.db_path = db_path or os.getenv("SESSIONS_DB_PATH", "./sessions.db")
        self._initialize_database()
    
    def _initialize_database(self):
        """Crée les tables nécessaires si elles n'existent pas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table pour les sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Table pour les messages de conversation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Table pour les recherches d'emploi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                query TEXT NOT NULL,
                country TEXT,
                total INTEGER,
                jobs_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Table pour le contexte de session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_context (
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (session_id, key),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Index pour améliorer les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_searches_session ON job_searches(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Crée une nouvelle session
        
        Args:
            session_id: Identifiant de la session
            metadata: Métadonnées optionnelles de la session
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?)
        """, (session_id, now, now, metadata_json))
        
        conn.commit()
        conn.close()
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Ajoute un message à une session
        
        Args:
            session_id: Identifiant de la session
            role: Rôle du message ('human' ou 'ai')
            content: Contenu du message
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # S'assurer que la session existe
        self.create_session(session_id)
        
        # Mettre à jour updated_at de la session
        cursor.execute("""
            UPDATE sessions SET updated_at = ? WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        
        # Ajouter le message
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les messages d'une session
        
        Args:
            session_id: Identifiant de la session
            
        Returns:
            Liste des messages avec role et content
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {"role": row[0], "content": row[1], "timestamp": row[2]}
            for row in rows
        ]
    
    def add_job_search(self, session_id: str, job_search_data: Dict[str, Any]):
        """
        Ajoute une recherche d'emploi à une session
        
        Args:
            session_id: Identifiant de la session
            job_search_data: Données de la recherche d'emploi
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # S'assurer que la session existe
        self.create_session(session_id)
        
        # Mettre à jour updated_at de la session
        cursor.execute("""
            UPDATE sessions SET updated_at = ? WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        
        # Ajouter la recherche d'emploi
        jobs_json = json.dumps(job_search_data.get('jobs', []))
        timestamp = job_search_data.get('timestamp', datetime.now().isoformat())
        
        cursor.execute("""
            INSERT INTO job_searches (session_id, query, country, total, jobs_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            job_search_data.get('query', ''),
            job_search_data.get('country'),
            job_search_data.get('total', 0),
            jobs_json,
            timestamp
        ))
        
        conn.commit()
        conn.close()
    
    def get_job_searches(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Récupère toutes les recherches d'emploi d'une session
        
        Args:
            session_id: Identifiant de la session
            
        Returns:
            Liste des recherches d'emploi
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT query, country, total, jobs_data, timestamp
            FROM job_searches
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'query': row[0],
                'country': row[1],
                'total': row[2],
                'jobs': json.loads(row[3]) if row[3] else [],
                'timestamp': row[4]
            })
        
        return results
    
    def update_session_context(self, session_id: str, key: str, value: Any):
        """
        Met à jour une valeur de contexte pour une session
        
        Args:
            session_id: Identifiant de la session
            key: Clé du contexte
            value: Valeur à stocker (sera sérialisée en JSON)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # S'assurer que la session existe
        self.create_session(session_id)
        
        value_json = json.dumps(value)
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO session_context (session_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, key, value_json, now))
        
        conn.commit()
        conn.close()
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Récupère tout le contexte d'une session
        
        Args:
            session_id: Identifiant de la session
            
        Returns:
            Dictionnaire du contexte
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, value
            FROM session_context
            WHERE session_id = ?
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        context = {}
        for row in rows:
            try:
                context[row[0]] = json.loads(row[1])
            except json.JSONDecodeError:
                context[row[0]] = row[1]
        
        return context
    
    def delete_session(self, session_id: str):
        """
        Supprime une session et toutes ses données associées
        
        Args:
            session_id: Identifiant de la session
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        # Les messages, job_searches et session_context seront supprimés automatiquement
        # grâce à ON DELETE CASCADE
        
        conn.commit()
        conn.close()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les sessions
        
        Returns:
            Liste des sessions avec leurs métadonnées
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, created_at, updated_at, metadata
            FROM sessions
            ORDER BY updated_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            metadata = None
            if row[3]:
                try:
                    metadata = json.loads(row[3])
                except json.JSONDecodeError:
                    pass
            
            sessions.append({
                'session_id': row[0],
                'created_at': row[1],
                'updated_at': row[2],
                'metadata': metadata
            })
        
        return sessions
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'une session
        
        Args:
            session_id: Identifiant de la session
            
        Returns:
            Informations de la session ou None si elle n'existe pas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, created_at, updated_at, metadata
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        metadata = None
        if row[3]:
            try:
                metadata = json.loads(row[3])
            except json.JSONDecodeError:
                pass
        
        return {
            'session_id': row[0],
            'created_at': row[1],
            'updated_at': row[2],
            'metadata': metadata
        }


# Instance globale du service de persistance
persistence_service = PersistenceService()

