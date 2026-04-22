import React, { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useChatStore } from '../stores/chatStore'
import { useDocumentStore } from '../stores/documentStore'
import { useAuthStore } from '../stores/authStore'
import { chatAPI } from '../services/api'
import { Send, Plus, Trash2, Edit2, Check, X, RefreshCcw, FileText, MessageSquare, LogOut, Search } from 'lucide-react'
import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatInterface({ isWidget = false }) {
    const [input, setInput] = useState('')
    const [sessions, setSessions] = useState([])
    const [currentSessionId, setCurrentSessionId] = useState(null)
    const [editingSessionId, setEditingSessionId] = useState(null)
    const [newTitle, setNewTitle] = useState('')
    const messagesEndRef = useRef(null)
    const { user, logout } = useAuthStore()
    const { messages, loading, error, addMessage, setMessages, setLoading, setError, clearMessages } = useChatStore()
    const { documents } = useDocumentStore()

    // Fetch initial sessions
    useEffect(() => {
        const fetchSessions = async () => {
            try {
                if (isWidget) {
                    // En modo widget, siempre crear sesión nueva al inicio
                    const response = await chatAPI.createSession('Consulta Widget')
                    setCurrentSessionId(response.data.data.id)
                    return
                }

                const response = await chatAPI.getSessions()
                if (response.data?.data?.sessions) {
                    const fetchedSessions = response.data.data.sessions
                    setSessions(fetchedSessions)
                    if (fetchedSessions.length > 0 && !currentSessionId) {
                        setCurrentSessionId(fetchedSessions[0].id)
                    }
                } else if (Array.isArray(response.data?.data)) {
                    const fetchedSessions = response.data.data
                    setSessions(fetchedSessions)
                    if (fetchedSessions.length > 0 && !currentSessionId) {
                        setCurrentSessionId(fetchedSessions[0].id)
                    }
                }
            } catch (err) {
                console.error("Error al cargar sesiones", err)
            }
        }
        fetchSessions()
    }, [isWidget])

    // Fetch session messages when changing session
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

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

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
                documents.map(d => d.id)
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

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim() || !currentSessionId) return

        const activeSessionId = currentSessionId;
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
                documents.map(d => d.id)
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
            {/* Unified Sidebar - Hidden in widget mode */}
            {!isWidget && (
                <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col shrink-0">
                    {/* Header with Logo */}
                    <div className="p-6 border-b border-gray-100 bg-white">
                        <div className="flex items-center space-x-3">
                            <img src="/src/assets/logo.svg" alt="Logo" className="w-10 h-10 rounded-xl shadow-sm" />
                            <div>
                                <h1 className="text-xl font-bold text-slate-800 tracking-tight">ConsultaRPP</h1>
                                <p className="text-[10px] text-blue-600 font-bold uppercase tracking-widest">Universal RAG</p>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={createSession}
                        className="m-6 flex items-center justify-center space-x-2 px-4 py-4 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-all shadow-lg active:scale-95"
                    >
                        <Plus size={20} />
                        <span className="font-bold">Nueva Sesión</span>
                    </button>

                    {/* Admin Quick Links */}
                    {user?.role === 'admin' && (
                        <div className="px-6 mb-4 space-y-1">
                            <Link
                                to="/documentos"
                                className={clsx(
                                    "flex items-center space-x-3 px-4 py-3 rounded-xl transition-all font-medium text-sm",
                                    location.pathname === '/documentos' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-gray-100'
                                )}
                            >
                                <FileText size={18} />
                                <span>Base de Conocimiento</span>
                            </Link>
                            <Link
                                to="/resultados"
                                className={clsx(
                                    "flex items-center space-x-3 px-4 py-3 rounded-xl transition-all font-medium text-sm",
                                    location.pathname === '/resultados' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-gray-100'
                                )}
                            >
                                <Search size={18} />
                                <span>Búsqueda Inteligente</span>
                            </Link>
                        </div>
                    )}

                    <div className="px-6 mb-2">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tus Sesiones</p>
                    </div>

                    <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
                            {sessions.map(session => (
                                <div
                                    key={session.id}
                                    className={clsx(
                                        'p-4 rounded-xl cursor-pointer transition-all group border',
                                        currentSessionId === session.id
                                            ? 'bg-blue-600 text-white border-blue-700 shadow-sm'
                                            : 'bg-white text-gray-700 border-gray-100 hover:border-blue-200 hover:bg-blue-50'
                                    )}
                                    onClick={() => editingSessionId !== session.id && setCurrentSessionId(session.id)}
                                >
                                    <div className="flex items-center justify-between">
                                        {editingSessionId === session.id ? (
                                            <div className="flex items-center w-full space-x-1" onClick={e => e.stopPropagation()}>
                                                <input
                                                    type="text"
                                                    value={newTitle}
                                                    onChange={e => setNewTitle(e.target.value)}
                                                    className="w-full px-2 py-1 text-sm text-black rounded border-none focus:ring-0"
                                                    autoFocus
                                                    onKeyDown={e => {
                                                        if (e.key === 'Enter') handleSaveTitle(session.id)
                                                        if (e.key === 'Escape') setEditingSessionId(null)
                                                    }}
                                                />
                                                <button onClick={() => handleSaveTitle(session.id)} className="p-1 hover:text-green-500"><Check size={14} /></button>
                                                <button onClick={() => setEditingSessionId(null)} className="p-1 hover:text-red-500"><X size={14} /></button>
                                            </div>
                                        ) : (
                                            <>
                                                <span className="truncate text-sm font-medium pr-2">{session.title}</span>
                                                <div className="flex opacity-0 group-hover:opacity-100 transition-all space-x-1">
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            setEditingSessionId(session.id)
                                                            setNewTitle(session.title)
                                                        }}
                                                        className="p-1 hover:bg-blue-400 rounded"
                                                    >
                                                        <Edit2 size={14} />
                                                    </button>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            deleteSession(session.id)
                                                        }}
                                                        className="p-1 hover:bg-red-400 rounded"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Footer User Section */}
                        <div className="p-6 border-t border-gray-100 bg-white">
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0 mr-3">
                                    <p className="text-sm font-bold text-slate-800 truncate">
                                        {user?.username || 'Usuario'}
                                    </p>
                                    <p className="text-[11px] text-slate-400 truncate uppercase tracking-tighter">
                                        {user?.role || 'User'}
                                    </p>
                                </div>
                                <button
                                    onClick={logout}
                                    className="p-3 bg-slate-50 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all shadow-sm group"
                                    title="Cerrar sesión"
                                >
                                    <LogOut size={20} className="group-hover:scale-110 transition-transform" />
                                </button>
                            </div>
                        </div>
                    </div>
            )}

            {/* Chat Area - Ocupa todo si no hay sidebar */}
            <div className="flex-1 flex flex-col bg-slate-50 relative">
                <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth">
                    {!currentSessionId ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-6">
                            <div className="relative">
                                <div className="p-8 bg-white rounded-3xl shadow-xl animate-bounce duration-[3000ms]">
                                    <img src="/consultarpp/assets/logos/consulta-rpp-logo.svg" alt="Logo" className="w-24 h-24" />
                                </div>
                                <span className="absolute -top-4 -right-4 text-5xl animate-pulse">🏛️</span>
                            </div>
                            <div className="text-center">
                                <h2 className="text-2xl font-bold text-slate-800">Bienvenido a ConsultaRPP</h2>
                                <p className="text-slate-500">Inicie una sesión para asesoría registral inteligente</p>
                            </div>
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-300 space-y-2">
                            <span className="text-6xl">🏛️</span>
                            <p className="text-xl">¿En qué trámite del IRCEP/RPP puedo apoyarle hoy?</p>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={idx} className={clsx('flex w-full', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                                <div className={clsx(
                                    'max-w-[90%] px-4 py-3 rounded-xl shadow-md border animate-in fade-in slide-in-from-bottom-2 duration-300',
                                    msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none border-blue-700'
                                        : 'bg-white text-slate-800 rounded-bl-none border-slate-200'
                                )}>
                                    <div className="text-[14px] whitespace-pre-wrap leading-tight tabular-nums markdown-content prose prose-slate prose-sm max-w-none text-slate-800">
                                        <ReactMarkdown 
                                            remarkPlugins={[remarkGfm]}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                    {msg.sources && msg.sources.length > 0 && (
                                        <div className={clsx('mt-6 pt-4 border-t text-xs', msg.role === 'user' ? 'border-blue-500 text-blue-100' : 'border-slate-100 text-slate-400')}>
                                            <p className="font-bold mb-2 uppercase tracking-wider">Fuentes Oficiales:</p>
                                            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                {msg.sources.map((src, i) => (
                                                    <li key={i} className="flex items-center space-x-1">
                                                        <FileText size={10} />
                                                        <span className="truncate">{src}</span>
                                                    </li>
                                                ))}
                                            </ul>
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
                                <span>Consultando normativa registral...</span>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="max-w-2xl mx-auto bg-red-50 border border-red-100 text-red-600 px-6 py-4 rounded-2xl flex justify-between items-center shadow-lg">
                            <div className="flex items-center space-x-3">
                                <X size={20} className="text-red-400" />
                                <span className="font-medium">{error}</span>
                            </div>
                            <button onClick={handleRetry} className="bg-red-600 text-white px-4 py-2 rounded-xl hover:bg-red-700 transition shadow-sm font-bold">
                                Reintentar
                            </button>
                        </div>
                    )}
                    <div ref={messagesEndRef} className="h-4" />
                </div>

                {/* Unified Input Bar */}
                {currentSessionId && (
                    <div className="p-4 md:p-5 bg-white border-t border-slate-200 shadow-2xl">
                        <form onSubmit={sendMessage} className="max-w-6xl mx-auto relative group">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Escriba aquí su consulta sobre trámites, requisitos o derechos..."
                                disabled={loading}
                                className="w-full px-6 py-3.5 text-lg bg-slate-50 border-2 border-slate-100 rounded-[1.5rem] focus:outline-none focus:border-blue-500 focus:bg-white transition-all shadow-inner disabled:opacity-50 pr-16"
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                className="absolute right-2 top-2 bottom-2 px-5 bg-blue-600 text-white rounded-[1.2rem] hover:bg-blue-700 disabled:opacity-50 transition-all shadow-lg active:scale-95 flex items-center justify-center"
                            >
                                <Send size={22} />
                            </button>
                        </form>
                        <p className="text-center text-[9px] text-slate-400 mt-3 uppercase tracking-[0.2em]">
                            Sistema de Asesoría Legal Basado en Normativa Vigente 2026
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
