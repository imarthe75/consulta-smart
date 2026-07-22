import React, { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from 'react-oidc-context'
import { useChatStore } from '../stores/chatStore'
import { useDocumentStore } from '../stores/documentStore'
import { useAuthStore } from '../stores/authStore'
import api, { chatAPI } from '../services/api'
import { Send, Plus, Trash2, Edit2, Check, X, RefreshCcw, FileText, MessageSquare, LogOut, Search, Settings, BookOpen, Hash, ThumbsUp, ThumbsDown } from 'lucide-react'
import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * ChatInterface — Componente principal del Chatbot Inteligente (RAG).
 * Maneja el historial de conversaciones, la selección dinámica de perfiles/tenants,
 * el renderizado de respuestas en formato Markdown con Fuentes Oficiales citadas,
 * y los controles de retroalimentación (thumbs up / thumbs down).
 *
 * @param {boolean} isWidget - Si es true, el chat se renderiza en modo compacto sin barra lateral para widgets flotantes.
 */
export default function ChatInterface({ isWidget = false }) {
    // Texto escrito por el usuario en el campo de entrada
    const [input, setInput] = useState('')
    // Lista de sesiones de chat asociadas al usuario
    const [sessions, setSessions] = useState([])
    // ID de la sesión de chat seleccionada actualmente
    const [currentSessionId, setCurrentSessionId] = useState(null)
    // ID de la sesión que está siendo editada en línea (renombrada)
    const [editingSessionId, setEditingSessionId] = useState(null)
    // Nuevo título asignado durante el renombrado de sesión
    const [newTitle, setNewTitle] = useState('')
    // Referencia al final del contenedor de mensajes para autoscroll
    const messagesEndRef = useRef(null)

    // Store global de autenticación de usuario
    const { user, logout: storeLogout } = useAuthStore()
    const auth = useAuth()

    // Store global de Zustand para administrar los mensajes e hiperparámetros del chat
    const { messages, loading, error, addMessage, setMessages, setLoading, setError, clearMessages } = useChatStore()
    // Documentos indexados cargados en el store global
    const { documents } = useDocumentStore()

    // Estado para la lista de perfiles/tenants disponibles en la BD
    const [availableProfiles, setAvailableProfiles] = useState([])
    // Tenant y Perfil activos en la sesión del usuario
    const [tenantId, setTenantId] = useState('general')
    const [profileId, setProfileId] = useState('general')
    
    // Configuración estética y de branding del perfil activo (título, logo, color principal)
    const [profileConfig, setProfileConfig] = useState({
        title: 'Asistente',
        subtitle: '',
        logo_url: '',
        icon: 'Bot',
        welcome_message: '¡Hola! ¿En qué puedo apoyarle hoy?',
        primary_color: '#3b82f6'
    })
    
    // Estado local para recordar las valoraciones de feedback (thumbs up/down) enviadas
    const [feedbackState, setFeedbackState] = useState({})

    /**
     * Envia la valoración del usuario (👍 / 👎) al backend para el mensaje especificado.
     * @param {string} msgId - ID del mensaje calificado.
     * @param {string} rating - Valoración ('up' o 'down').
     */
    const handleFeedback = async (msgId, rating) => {
        if (!msgId) return
        setFeedbackState(prev => ({ ...prev, [msgId]: rating }))
        try {
            await api.post(`chat/messages/${msgId}/feedback`, { rating })
        } catch (err) {
            console.error("Error al enviar feedback:", err)
        }
    }

    /**
     * Efecto inicial: Carga los query params de la URL y consulta los perfiles activos en BD.
     */
    useEffect(() => {
        const queryParams = new URLSearchParams(window.location.search);
        const tid = queryParams.get('tenantId') || queryParams.get('tenant') || 'general';
        const pid = queryParams.get('profile_id') || tid;
        const customColor = queryParams.get('themeColor');
        const customTitle = queryParams.get('title');

        setTenantId(tid);
        setProfileId(pid);

        const fetchProfilesAndActive = async () => {
            try {
                // Obtener catálogo de perfiles públicos
                const listRes = await api.get('admin/chatbot/profiles')
                if (listRes.data && Array.isArray(listRes.data)) {
                    setAvailableProfiles(listRes.data)
                }

                // Cargar configuración de theming para el perfil activo
                const response = await api.get(`chat/profiles/${pid}`);
                if (response.data) {
                    setProfileConfig({
                        title: customTitle || response.data.title || response.data.name || 'Asistente',
                        subtitle: response.data.subtitle || '',
                        logo_url: response.data.logo_url || '',
                        icon: response.data.icon || 'Bot',
                        welcome_message: response.data.welcome_message || '¡Hola! ¿En qué puedo apoyarle hoy?',
                        primary_color: customColor || response.data.primary_color || '#3b82f6'
                    });
                }
            } catch (err) {
                console.error("Error al cargar perfiles:", err);
                setProfileConfig(prev => ({
                    ...prev,
                    title: customTitle || prev.title,
                    primary_color: customColor || prev.primary_color
                }));
            }
        };
        fetchProfilesAndActive();
    }, []);

    /**
     * Cambia dinámicamente el perfil activo del chatbot y recarga su configuración.
     * @param {string} newPid - ID del nuevo perfil seleccionado.
     */
    const handleSelectProfile = async (newPid) => {
        setProfileId(newPid)
        setTenantId(newPid)
        clearMessages()
        setCurrentSessionId(null)
        try {
            const res = await api.get(`chat/profiles/${newPid}`)
            if (res.data) {
                setProfileConfig({
                    title: res.data.title || res.data.name || 'Asistente',
                    subtitle: res.data.subtitle || '',
                    logo_url: res.data.logo_url || '',
                    icon: res.data.icon || 'Bot',
                    welcome_message: res.data.welcome_message || '¡Hola! ¿En qué puedo apoyarle hoy?',
                    primary_color: res.data.primary_color || '#3b82f6'
                })
            }
        } catch (e) {
            console.error("Error cambiando de perfil:", e)
        }
    }

    /**
     * Ejecuta el cierre de sesión seguro desvinculando la sesión local y redirigiendo a Authentik.
     */
    const handleLogout = async () => {
        try {
            storeLogout();
            localStorage.clear();
            sessionStorage.clear();

            const logoutRedirectUri = window.location.origin + import.meta.env.BASE_URL
            const logoutUrl = new URL(window.location.origin + "/application/o/consulta-smart/end-session/");
            logoutUrl.searchParams.append("post_logout_redirect_uri", logoutRedirectUri);

            if (auth.user?.id_token) {
                logoutUrl.searchParams.append("id_token_hint", auth.user.id_token);
            }
            if (auth.user?.state) {
                logoutUrl.searchParams.append("state", auth.user.state);
            }

            window.location.href = logoutUrl.toString();

            setTimeout(() => {
                window.location.href = logoutRedirectUri;
            }, 3000);

        } catch (error) {
            console.error("Error en logout:", error);
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = window.location.origin + import.meta.env.BASE_URL;
        }
    }

    /**
     * Carga el historial inicial de sesiones desde la API (omitido en modo widget).
     */
    useEffect(() => {
        const fetchSessions = async () => {
            try {
                if (isWidget) return

                const response = await chatAPI.getSessions()
                const rawSessions = response.data?.data?.sessions || response.data?.data || []
                if (Array.isArray(rawSessions)) {
                    const filteredSessions = rawSessions.filter(s => s.title !== 'Consulta Widget' && s.title !== 'Widget Guest Session')
                    setSessions(filteredSessions)
                    if (filteredSessions.length > 0 && !currentSessionId) {
                        setCurrentSessionId(filteredSessions[0].id)
                    }
                }
            } catch (err) {
                console.error("Error al cargar sesiones", err)
            }
        }
        fetchSessions()
    }, [isWidget])

    /**
     * Carga los mensajes de la sesión activa al cambiar de conversación.
     */
    useEffect(() => {
        if (currentSessionId) {
            const fetchHistory = async () => {
                try {
                    const response = await chatAPI.getSession(currentSessionId)
                    if (response.data?.data?.messages) {
                        setMessages(response.data.data.messages)
                    } else {
                        clearMessages()
                    }
                } catch (err) {
                    console.error("Error al cargar historial", err)
                    clearMessages()
                }
            }
            fetchHistory()
        }
    }, [currentSessionId])

    /**
     * Hace autoscroll hacia abajo al recibir un nuevo mensaje.
     */
    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    /**
     * Inicia una nueva conversación vacía.
     */
    const createSession = async () => {
        try {
            const response = await chatAPI.createSession('Nueva Sesión')
            const newSession = response.data.data
            setSessions([...sessions, newSession])
            setCurrentSessionId(newSession.id)
            clearMessages()
        } catch (err) {
            setError('Error al crear sesión: ' + err.message)
        }
    }

    /**
     * Reintenta el envío de la última pregunta efectuada por el usuario.
     */
    const handleRetry = async () => {
        const lastUserMessage = [...messages].reverse().find(m => m.role === 'user');
        if (!lastUserMessage || !currentSessionId) return;

        const activeSessionId = currentSessionId;
        setError(null);
        setLoading(true);

        try {
            const response = await chatAPI.sendQuery(
                activeSessionId,
                lastUserMessage.content,
                documents.map(d => d.id),
                { "category": profileId }
            )

            if (activeSessionId === currentSessionId) {
                const assistantMessage = {
                    role: 'assistant',
                    content: response.data.data.response,
                    sources: response.data.data.sources || [],
                    timestamp: new Date().toISOString(),
                }
                addMessage(assistantMessage)
            }
        } catch (err) {
            if (activeSessionId === currentSessionId) {
                setError('Error al enviar mensaje: ' + err.message)
            }
        } finally {
            if (activeSessionId === currentSessionId) {
                setLoading(false)
            }
        }
    }

    /**
     * Envía la consulta ingresada por el usuario hacia el backend RAG.
     */
    const sendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim()) return

        let activeSessionId = currentSessionId;
        
        // Crear sesión dinámica en la primera interacción si no existe
        if (!activeSessionId) {
            try {
                const sessionRes = await chatAPI.createSession('Consulta Widget')
                activeSessionId = sessionRes.data.data.id
                setCurrentSessionId(activeSessionId)
            } catch (err) {
                setError('Error al iniciar sesión de chat: ' + err.message)
                return
            }
        }
        const userMessage = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString(),
        }

        addMessage(userMessage)
        setInput('')
        setLoading(true)
        setError(null);

        try {
            const response = await chatAPI.sendQuery(
                activeSessionId,
                input,
                documents.map(d => d.id),
                { "category": profileId }
            )

            if (activeSessionId === currentSessionId) {
                const assistantMessage = {
                    role: 'assistant',
                    content: response.data.data.response,
                    sources: response.data.data.sources || [],
                    timestamp: new Date().toISOString(),
                }
                addMessage(assistantMessage)
            }
        } catch (err) {
            if (activeSessionId === currentSessionId) {
                setError('Error al enviar mensaje: ' + err.message)
            }
        } finally {
            if (activeSessionId === currentSessionId) {
                setLoading(false)
            }
        }
    }

    /**
     * Elimina la sesión especificada.
     */
    const deleteSession = async (sessionId) => {
        try {
            await chatAPI.deleteSession(sessionId)
            setSessions(sessions.filter(s => s.id !== sessionId))
            if (currentSessionId === sessionId) {
                setCurrentSessionId(null)
                clearMessages()
            }
        } catch (err) {
            setError('Error al eliminar sesión: ' + err.message)
        }
    }

    /**
     * Guarda el nuevo título otorgado a una sesión.
     */
    const handleSaveTitle = async (sessionId) => {
        if (!newTitle.trim()) {
            setEditingSessionId(null)
            return
        }
        try {
            await chatAPI.renameSession(sessionId, newTitle)
            setSessions(sessions.map(s => s.id === sessionId ? { ...s, title: newTitle } : s))
            setEditingSessionId(null)
        } catch (err) {
            setError('Error al renombrar sesión: ' + err.message)
        }
    }

    const location = useLocation()

    return (
        <div className="flex h-full w-full bg-white overflow-hidden">
            {/* Barra lateral unificada — Oculta en modo widget */}
            {!isWidget && (
                <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col shrink-0">
                    {/* Header con Logo y Selector de Perfiles */}
                    <div className="p-5 border-b border-gray-100 bg-white space-y-3">
                        <div className="flex items-center space-x-3">
                            <div 
                                className="w-10 h-10 rounded-xl shadow-sm flex items-center justify-center text-white font-bold transition-colors"
                                style={{ backgroundColor: profileConfig.primary_color }}
                            >
                                {profileConfig.logo_url ? (
                                    <img src={profileConfig.logo_url} alt="Logo" className="w-full h-full object-cover rounded-xl" />
                                ) : (
                                    <span className="text-lg">🤖</span>
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <h1 className="text-base font-bold text-slate-800 tracking-tight truncate">{profileConfig.title}</h1>
                                <p className="text-[10px] text-blue-600 font-bold uppercase tracking-wider truncate">Tenant: {profileId}</p>
                            </div>
                        </div>

                        {/* Selector dinámico de Perfiles de la BD */}
                        <div>
                            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                                Asistente Activo
                            </label>
                            <select
                                value={profileId}
                                onChange={(e) => handleSelectProfile(e.target.value)}
                                className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                            >
                                {availableProfiles.map(p => (
                                    <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
                                ))}
                            </select>
                        </div>

                        {/* Botón de Nueva Sesión */}
                        <button
                            onClick={createSession}
                            className="w-full py-2.5 px-4 text-white font-semibold rounded-xl shadow-sm hover:opacity-95 transition flex items-center justify-center space-x-2 text-sm"
                            style={{ backgroundColor: profileConfig.primary_color }}
                        >
                            <Plus size={18} />
                            <span>Nueva Sesión</span>
                        </button>
                    </div>

                    {/* Lista de Sesiones de Chat */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-1">
                        <div className="px-3 py-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                            Historial de Sesiones
                        </div>
                        {sessions.map((s) => (
                            <div
                                key={s.id}
                                className={clsx(
                                    'group flex items-center justify-between p-3 rounded-xl cursor-pointer text-sm transition-all',
                                    currentSessionId === s.id
                                        ? 'bg-white shadow-sm border border-gray-100 text-blue-600 font-semibold'
                                        : 'text-gray-600 hover:bg-gray-100/60'
                                )}
                                onClick={() => setCurrentSessionId(s.id)}
                            >
                                <div className="flex items-center space-x-3 flex-1 min-w-0">
                                    <MessageSquare size={16} className={currentSessionId === s.id ? 'text-blue-600' : 'text-gray-400'} />
                                    {editingSessionId === s.id ? (
                                        <input
                                            type="text"
                                            value={newTitle}
                                            onChange={(e) => setNewTitle(e.target.value)}
                                            onBlur={() => handleSaveTitle(s.id)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleSaveTitle(s.id)}
                                            className="w-full bg-transparent border-b border-blue-500 text-sm focus:outline-none"
                                            autoFocus
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    ) : (
                                        <span className="truncate">{s.title}</span>
                                    )}
                                </div>
                                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            setEditingSessionId(s.id)
                                            setNewTitle(s.title)
                                        }}
                                        className="p-1 hover:bg-gray-200 rounded text-gray-500"
                                    >
                                        <Edit2 size={14} />
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            deleteSession(s.id)
                                        }}
                                        className="p-1 hover:bg-red-50 text-red-500 rounded"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Footer de la Barra Lateral */}
                    <div className="p-4 border-t border-gray-200 bg-white space-y-2">
                        <Link
                            to="/admin"
                            className="flex items-center space-x-3 text-xs font-semibold text-gray-600 hover:text-blue-600 p-2 rounded-lg hover:bg-gray-50 transition"
                        >
                            <Settings size={16} />
                            <span>Panel de Administración</span>
                        </Link>
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center space-x-3 text-xs font-semibold text-red-600 hover:bg-red-50 p-2 rounded-lg transition"
                        >
                            <LogOut size={16} />
                            <span>Cerrar Sesión</span>
                        </button>
                    </div>
                </div>
            )}

            {/* Ventana de Mensajes del Chat */}
            <div className="flex-1 flex flex-col h-full bg-white relative">
                {/* Banner de Bienvenida o Estado */}
                <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
                    <div>
                        <h2 className="text-sm font-bold text-slate-800">{profileConfig.title}</h2>
                        <p className="text-xs text-slate-500">{profileConfig.welcome_message}</p>
                    </div>
                    {loading && (
                        <div className="flex items-center space-x-2 text-xs text-blue-600 font-semibold animate-pulse">
                            <RefreshCcw size={14} className="animate-spin" />
                            <span>Consultando RAG...</span>
                        </div>
                    )}
                </div>

                {/* Contenedor de Conversación */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-4">
                            <div 
                                className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shadow-sm"
                                style={{ backgroundColor: `${profileConfig.primary_color}15`, color: profileConfig.primary_color }}
                            >
                                🤖
                            </div>
                            <div className="max-w-md">
                                <h3 className="text-base font-bold text-slate-800 mb-1">{profileConfig.welcome_message}</h3>
                                <p className="text-xs text-slate-500">
                                    Haz una consulta en lenguaje natural sobre trámites, requisitos o normativa oficial.
                                </p>
                            </div>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={idx} className={clsx('flex w-full', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                                <div 
                                    className={clsx(
                                        'max-w-[90%] px-4 py-3 rounded-xl shadow-md border animate-in fade-in slide-in-from-bottom-2 duration-300',
                                        msg.role === 'user'
                                            ? 'text-white rounded-br-none'
                                            : 'bg-white text-slate-800 rounded-bl-none border-slate-200'
                                    )}
                                    style={msg.role === 'user' ? { backgroundColor: profileConfig.primary_color, borderColor: profileConfig.primary_color } : {}}
                                >
                                    <div className="text-[14px] whitespace-pre-wrap leading-tight tabular-nums markdown-content prose prose-slate prose-sm max-w-none text-slate-800">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>

                                    {/* Renderizado de Fuentes Oficiales Citas */}
                                    {msg.sources && msg.sources.length > 0 && (() => {
                                        const normalizeSources = (srcs) =>
                                            srcs.map(s =>
                                                typeof s === 'string'
                                                    ? { title: s, filename: s, chunk_number: null, version_label: null }
                                                    : s
                                            )
                                        const sources = normalizeSources(msg.sources)
                                        return (
                                            <div className={clsx(
                                                'mt-5 pt-4 border-t text-xs',
                                                msg.role === 'user'
                                                    ? 'border-white/20 text-blue-50'
                                                    : 'border-slate-100 text-slate-500'
                                            )}>
                                                <div className="flex items-center gap-1.5 mb-3">
                                                    <BookOpen size={11} className="opacity-60" />
                                                    <span className="font-bold uppercase tracking-wider text-[10px]">Fuentes Oficiales</span>
                                                    <span className="ml-auto font-mono text-[10px] opacity-50">{sources.length} doc{sources.length !== 1 ? 's' : ''}</span>
                                                </div>
                                                <ul className="space-y-1.5">
                                                    {sources.map((src, i) => (
                                                        <li key={i} className="flex items-start gap-2">
                                                            <div
                                                                className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium flex-1 min-w-0"
                                                                style={{
                                                                    backgroundColor: msg.role === 'user'
                                                                        ? 'rgba(255,255,255,0.15)'
                                                                        : 'var(--cs-info-bg)',
                                                                    color: msg.role === 'user'
                                                                        ? 'inherit'
                                                                        : 'var(--cs-info)',
                                                                }}
                                                            >
                                                                <FileText size={9} className="shrink-0 opacity-70" />
                                                                <span className="truncate">
                                                                    {src.title || src.filename || 'Documento oficial'}
                                                                </span>
                                                                {src.version_label && (
                                                                    <span className="shrink-0 opacity-60 font-mono">({src.version_label})</span>
                                                                )}
                                                            </div>
                                                            {src.chunk_number != null && (
                                                                <div
                                                                    className="flex items-center gap-0.5 px-1.5 py-1 rounded-md text-[10px] font-mono shrink-0 opacity-70"
                                                                    style={{
                                                                        backgroundColor: msg.role === 'user'
                                                                            ? 'rgba(255,255,255,0.12)'
                                                                            : 'var(--cs-info-bg)',
                                                                        color: msg.role === 'user' ? 'inherit' : 'var(--cs-info)'
                                                                    }}
                                                                    title={`Fragmento #${src.chunk_number}`}
                                                                >
                                                                    <Hash size={8} />{src.chunk_number}
                                                                </div>
                                                            )}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )
                                    })()}

                                    {/* Botones de Feedback (Thumbs Up / Thumbs Down) */}
                                    {msg.role === 'assistant' && (
                                        <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end space-x-2 text-xs text-slate-400">
                                            <span className="text-[10px] mr-1">¿Fue útil esta respuesta?</span>
                                            <button
                                                onClick={() => handleFeedback(msg.id, 'up')}
                                                className={clsx(
                                                    'p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors',
                                                    (feedbackState[msg.id] === 'up' || msg.feedback_rating === 'up') ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'
                                                )}
                                                title="Respuesta útil"
                                            >
                                                <ThumbsUp size={13} />
                                            </button>
                                            <button
                                                onClick={() => handleFeedback(msg.id, 'down')}
                                                className={clsx(
                                                    'p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors',
                                                    (feedbackState[msg.id] === 'down' || msg.feedback_rating === 'down') ? 'text-rose-600 dark:text-rose-400 font-bold' : 'text-slate-400'
                                                )}
                                                title="Respuesta no útil"
                                            >
                                                <ThumbsDown size={13} />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}

                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-white border border-slate-200 text-slate-400 px-8 py-4 rounded-3xl shadow-sm italic flex items-center space-x-3">
                                <RefreshCcw size={16} className="animate-spin" />
                                <span>Procesando consulta...</span>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="p-4 bg-red-50 text-red-600 text-xs rounded-xl border border-red-200 flex items-center justify-between">
                            <span>{error}</span>
                            <button onClick={handleRetry} className="underline font-bold hover:text-red-700">Reintentar</button>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Formulario de Entrada de Mensaje */}
                <div className="p-4 bg-white border-t border-gray-100">
                    <form onSubmit={sendMessage} className="flex items-center space-x-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Escribe tu consulta aquí..."
                            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="p-3 text-white rounded-xl shadow-sm hover:opacity-95 transition disabled:opacity-50 flex items-center justify-center shrink-0"
                            style={{ backgroundColor: profileConfig.primary_color }}
                        >
                            <Send size={18} />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    )
}
