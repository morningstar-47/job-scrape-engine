# Documentation API Frontend - Assistant Virtuel LangChain

Documentation simple et claire pour intégrer l'API dans votre application frontend.

## 📋 Table des matières

1. [Configuration de base](#configuration-de-base)
2. [Chat conversationnel](#chat-conversationnel)
3. [Recherche d'emploi](#recherche-demploi)
4. [Gestion de la base de connaissances](#gestion-de-la-base-de-connaissances)
5. [Gestion des erreurs](#gestion-des-erreurs)
6. [Exemples complets](#exemples-complets)

---

## 🔧 Configuration de base

### URL de base

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Headers par défaut

```javascript
const headers = {
  'Content-Type': 'application/json',
};
```

---

## 💬 Chat conversationnel

### 1. Envoyer un message

**Endpoint:** `POST /chat`

**Requête:**
```javascript
async function sendMessage(message, sessionId = 'default') {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      message: message,
      session_id: sessionId
    })
  });
  
  return await response.json();
}

// Utilisation
const result = await sendMessage('Bonjour, comment ça va ?', 'user-123');
console.log(result.answer); // Réponse de l'assistant
console.log(result.sources); // Sources utilisées (si RAG)

// Recherche d'emploi dans le chat (détection automatique)
const jobResult = await sendMessage('Je cherche un emploi de développeur Python en France', 'user-123');
console.log(jobResult.answer); // Réponse avec résultats d'emploi
if (jobResult.job_search) {
  console.log(`Emplois trouvés: ${jobResult.job_search.total}`);
  jobResult.job_search.jobs.forEach(job => {
    console.log(`- ${job.job_title} chez ${job.employer_name}`);
  });
}
```

**Réponse (chat normal):**
```json
{
  "answer": "Bonjour ! Je vais bien, merci. Comment puis-je vous aider ?",
  "sources": [],
  "session_id": "user-123",
  "error": null,
  "job_search": null
}
```

**Réponse (avec recherche d'emploi):**
```json
{
  "answer": "Voici les résultats de ma recherche d'emploi pour développeur Python en France...",
  "sources": [],
  "session_id": "user-123",
  "error": null,
  "job_search": {
    "query": "développeur Python",
    "country": "France",
    "total": 15,
    "jobs": [
      {
        "job_id": "abc123",
        "job_title": "Développeur Python",
        "employer_name": "TechCorp",
        "job_city": "Paris",
        "job_country": "France",
        "job_apply_link": "https://example.com/apply"
      }
    ]
  }
}
```

### 2. Récupérer l'historique d'une session

**Endpoint:** `GET /chat/session/{session_id}/history`

```javascript
async function getChatHistory(sessionId) {
  const response = await fetch(
    `${API_BASE_URL}/chat/session/${sessionId}/history`
  );
  return await response.json();
}

// Utilisation
const history = await getChatHistory('user-123');
console.log(history.messages); // Array de messages
console.log(history.count); // Nombre de messages
```

**Réponse:**
```json
{
  "session_id": "user-123",
  "messages": [
    {
      "role": "user",
      "content": "Bonjour",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "role": "assistant",
      "content": "Bonjour ! Comment puis-je vous aider ?",
      "timestamp": "2024-01-01T12:00:01"
    }
  ],
  "count": 2
}
```

### 3. Réinitialiser une session

**Endpoint:** `DELETE /chat/session/{session_id}`

```javascript
async function resetSession(sessionId) {
  const response = await fetch(
    `${API_BASE_URL}/chat/session/${sessionId}`,
    { method: 'DELETE' }
  );
  return await response.json();
}
```

---

## 🔍 Recherche d'emploi

### 1. Recherche basique

**Endpoint:** `GET /jobs/search`

```javascript
async function searchJobs(query, options = {}) {
  const params = new URLSearchParams({
    query: query,
    ...options // country, language, num_pages, etc.
  });
  
  const response = await fetch(
    `${API_BASE_URL}/jobs/search?${params}`
  );
  return await response.json();
}

// Utilisation
const jobs = await searchJobs('développeur Python', {
  country: 'France',
  language: 'fr',
  num_pages: 1
});

console.log(jobs.total); // Nombre d'emplois trouvés
console.log(jobs.jobs); // Array d'emplois
```

**Réponse:**
```json
{
  "jobs": [
    {
      "job_id": "abc123",
      "job_title": "Développeur Python",
      "employer_name": "TechCorp",
      "job_city": "Paris",
      "job_state": "Île-de-France",
      "job_country": "France",
      "job_employment_type": "FULLTIME",
      "job_is_remote": false,
      "job_posted_at_datetime_utc": "2024-01-01T10:00:00",
      "job_apply_link": "https://example.com/apply"
    }
  ],
  "total": 1,
  "query": "développeur Python",
  "country": "France",
  "language": "fr"
}
```

### 2. Recherche avec résumé formaté

**Endpoint:** `GET /jobs/search/summary`

```javascript
async function searchJobsSummary(query, country = null, limit = 5) {
  const params = new URLSearchParams({
    query: query,
    limit: limit.toString()
  });
  
  if (country) {
    params.append('country', country);
  }
  
  const response = await fetch(
    `${API_BASE_URL}/jobs/search/summary?${params}`
  );
  return await response.json();
}

// Utilisation
const summary = await searchJobsSummary('data scientist', 'France', 10);
summary.results.forEach(job => {
  console.log(job.summary); // Résumé formaté
  console.log(job.job_apply_link); // Lien de candidature
});
```

**Réponse:**
```json
{
  "query": "data scientist",
  "country": "France",
  "total_found": 15,
  "results": [
    {
      "summary": "**Data Scientist** chez DataCorp - Paris, Île-de-France, France (FULLTIME)\nPublié le: 2024-01-01T10:00:00",
      "job_id": "xyz789",
      "job_apply_link": "https://example.com/apply"
    }
  ]
}
```

### 3. Récupérer les détails d'un emploi

**Endpoint:** `GET /jobs/{job_id}`

```javascript
async function getJobDetails(jobId) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}`
  );
  return await response.json();
}
```

### Paramètres de recherche disponibles

| Paramètre | Type | Description | Valeurs possibles |
|-----------|------|-------------|-------------------|
| `query` | string | Termes de recherche (requis) | Ex: "développeur Python" |
| `country` | string | Pays | Ex: "France", "Germany" |
| `language` | string | Langue | "fr", "en", "es", etc. |
| `num_pages` | number | Nombre de pages | 1-10 (défaut: 1) |
| `employment_types` | string | Type d'emploi | FULLTIME, PARTTIME, CONTRACTOR, INTERN |
| `job_requirements` | string | Exigences | under_3_years_experience, more_than_3_years_experience, no_experience, no_degree |
| `date_posted` | string | Date de publication | today, 3days, week, month |
| `remote_jobs_only` | boolean | Emplois à distance | true/false |

---

## 📚 Gestion de la base de connaissances

### Ajouter du texte à la base de connaissances

**Endpoint:** `POST /knowledge/upload-text`

```javascript
async function addKnowledge(text, metadata = {}) {
  const response = await fetch(`${API_BASE_URL}/knowledge/upload-text`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      text: text,
      metadata: metadata
    })
  });
  return await response.json();
}

// Utilisation
const result = await addKnowledge(
  'LangChain est un framework pour applications LLM.',
  { source: 'documentation', type: 'info' }
);
```

### Uploader un fichier

**Endpoint:** `POST /knowledge/upload`

```javascript
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
    method: 'POST',
    body: formData
  });
  return await response.json();
}

// Utilisation avec un input file
const fileInput = document.querySelector('input[type="file"]');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    const result = await uploadFile(file);
    console.log(result.message);
  }
});
```

---

## ⚠️ Gestion des erreurs

### Fonction utilitaire pour gérer les erreurs

```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `Erreur HTTP: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Erreur API:', error);
    throw error;
  }
}

// Utilisation
try {
  const result = await apiCall(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ message: 'Hello' })
  });
} catch (error) {
  // Afficher l'erreur à l'utilisateur
  alert('Erreur: ' + error.message);
}
```

### Codes d'erreur HTTP

- `200` - Succès
- `400` - Requête invalide (paramètres manquants ou incorrects)
- `500` - Erreur serveur
- `503` - Service non disponible

---

## 🎯 Exemples complets

### Exemple 1: Chat simple avec React

```jsx
import React, { useState } from 'react';

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const sessionId = 'user-' + Date.now();

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId
        })
      });

      const data = await response.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer
      }]);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        placeholder="Tapez votre message..."
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Envoi...' : 'Envoyer'}
      </button>
    </div>
  );
}
```

### Exemple 2: Recherche d'emploi avec Vue.js

```vue
<template>
  <div>
    <input v-model="searchQuery" placeholder="Rechercher un emploi..." />
    <select v-model="selectedCountry">
      <option value="">Tous les pays</option>
      <option value="France">France</option>
      <option value="Germany">Allemagne</option>
    </select>
    <button @click="searchJobs">Rechercher</button>

    <div v-if="loading">Chargement...</div>
    <div v-else>
      <div v-for="job in jobs" :key="job.job_id" class="job-card">
        <h3>{{ job.job_title }}</h3>
        <p>{{ job.employer_name }}</p>
        <p>{{ job.job_city }}, {{ job.job_country }}</p>
        <a :href="job.job_apply_link" target="_blank">Postuler</a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: '',
      selectedCountry: '',
      jobs: [],
      loading: false
    };
  },
  methods: {
    async searchJobs() {
      this.loading = true;
      try {
        const params = new URLSearchParams({
          query: this.searchQuery,
          language: 'fr'
        });
        if (this.selectedCountry) {
          params.append('country', this.selectedCountry);
        }

        const response = await fetch(
          `http://localhost:8000/jobs/search?${params}`
        );
        const data = await response.json();
        this.jobs = data.jobs || [];
      } catch (error) {
        console.error('Erreur:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### Exemple 3: Service TypeScript complet

```typescript
// api.ts
const API_BASE_URL = 'http://localhost:8000';

interface ChatRequest {
  message: string;
  session_id?: string;
}

interface ChatResponse {
  answer: string;
  sources: Array<{ content: string; metadata: any }>;
  session_id: string;
  error: string | null;
}

interface JobSearchParams {
  query: string;
  country?: string;
  language?: string;
  num_pages?: number;
  employment_types?: string;
  remote_jobs_only?: boolean;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async chat(message: string, sessionId: string = 'default'): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async searchJobs(params: JobSearchParams) {
    const queryParams = new URLSearchParams({
      query: params.query,
      ...(params.country && { country: params.country }),
      ...(params.language && { language: params.language }),
      ...(params.num_pages && { num_pages: params.num_pages.toString() }),
      ...(params.employment_types && { employment_types: params.employment_types }),
      ...(params.remote_jobs_only && { remote_jobs_only: 'true' })
    });

    const response = await fetch(
      `${this.baseUrl}/jobs/search?${queryParams}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async getChatHistory(sessionId: string) {
    const response = await fetch(
      `${this.baseUrl}/chat/session/${sessionId}/history`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }
}

// Utilisation
const api = new ApiService();

// Chat
const chatResponse = await api.chat('Bonjour', 'user-123');
console.log(chatResponse.answer);

// Recherche d'emploi
const jobs = await api.searchJobs({
  query: 'développeur Python',
  country: 'France',
  language: 'fr'
});
console.log(jobs.jobs);
```

---

## 🔗 Liens utiles

- **Documentation interactive (Swagger):** http://localhost:8000/docs
- **Documentation alternative (ReDoc):** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

---

## 💡 Conseils

1. **Gestion des sessions:** Utilisez un identifiant unique par utilisateur pour maintenir le contexte
2. **Gestion du loading:** Affichez toujours un indicateur de chargement pendant les requêtes
3. **Gestion des erreurs:** Toujours gérer les erreurs et informer l'utilisateur
4. **CORS:** En production, configurez CORS correctement dans le backend
5. **Rate limiting:** Respectez les limites de l'API RapidAPI pour la recherche d'emploi

---

## 📝 Notes importantes

- Tous les endpoints retournent du JSON
- Les sessions sont persistantes jusqu'à réinitialisation
- La recherche d'emploi nécessite une clé API RapidAPI configurée
- Le chat utilise RAG (Récupération de contexte) pour des réponses plus précises

