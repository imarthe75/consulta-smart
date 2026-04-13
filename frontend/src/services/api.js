import axios from 'axios'

// Detectar URL del API dinámicamente basado en dónde se ejecuta
const getApiBaseUrl = () => {
    // En desarrollo (Vite), usar variable de entorno
    if (import.meta.env.DEV) {
        return import.meta.env.VITE_API_URL || '/api/v1'  // Usa proxy de Vite en desarrollo
    }

    // En producción, construir dinámicamente usando el host actual
    // El frontend se ejecuta en el mismo servidor que el backend
    // Frontend: puerto 3000, Backend: puerto 3001
    const protocol = window.location.protocol  // http: o https:
    const hostname = window.location.hostname  // IP del servidor o dominio
    const port = 3001                           // Puerto del backend

    return `${protocol}//${hostname}:${port}/api/v1`
}

const API_BASE_URL = getApiBaseUrl()
const API_TIMEOUT = import.meta.env.VITE_API_TIMEOUT || 30000

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Interceptor para agregar token a todas las solicitudes
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Interceptor para manejo de errores
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export const authAPI = {
    login: (email, password) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },

    register: (email, username, password) =>
        api.post('/auth/register', { email, username, password }),

    getProfile: () =>
        api.get('/auth/profile'),
}

export const documentsAPI = {
    upload: (file, category, onUploadProgress) =>
        api.post('/documents/upload',
            { file, category },
            {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress,
            }
        ),

    list: (page = 1, limit = 10) =>
        api.get('/documents', { params: { page, limit } }),

    get: (documentId) =>
        api.get(`/documents/${documentId}`),

    delete: (documentId) =>
        api.delete(`/documents/${documentId}`),

    getStatus: (documentId) =>
        api.get(`/documents/${documentId}/status`),
}

export const chatAPI = {
    createSession: (title) =>
        api.post('/chat/sessions', { title }),

    getSessions: () =>
        api.get('/chat/sessions'),

    getSession: (sessionId) =>
        api.get(`/chat/sessions/${sessionId}`),

    renameSession: (sessionId, title) =>
        api.put(`/chat/sessions/${sessionId}`, { title }),

    deleteSession: (sessionId) =>
        api.delete(`/chat/sessions/${sessionId}`),

    sendQuery: (sessionId, query, documentIds = []) =>
        api.post('/chat/query', {
            session_id: sessionId,
            message: query,
            document_ids: documentIds,
        }),
}

export const searchAPI = {
    search: (query, limit = 10) =>
        api.post('/search', { query, limit }),

    searchByCategory: (category, limit = 10) =>
        api.get('/search/category', { params: { category, limit } }),
}

export default api
