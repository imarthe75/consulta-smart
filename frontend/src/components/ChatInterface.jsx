import React, { useState, useEffect, useRef } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useDocumentStore } from '../stores/documentStore'
import { chatAPI } from '../services/api'
import { Send, Plus, Trash2, Edit2, Check, X, RefreshCcw } from 'lucide-react'
import clsx from 'clsx'

export default function ChatInterface() {
    const [input, setInput] = useState('')
    const [sessions, setSessions] = useState([])
    const [currentSessionId, setCurrentSessionId] = useState(null)
    const [editingSessionId, setEditingSessionId] = useState(null)
    const [newTitle, setNewTitle] = useState('')
    const messagesEndRef = useRef(null)

    const { messages, loading, error, addMessage, setMessages, setLoading, setError, clearMessages } = useChatStore()
    const { documents } = useDocumentStore()

    // Fetch initial sessions
    useEffect(() => {
        const fetchSessions = async () => {
            try {
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
    }, [])

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
        
        setError(null);
        setLoading(true);

        try {
            const response = await chatAPI.sendQuery(
                currentSessionId,
                lastUserMessage.content,
                documents.map(d => d.id)
            )

            const assistantMessage = {
                role: 'assistant',
                content: response.data.data.response,
                sources: response.data.data.sources || [],
                timestamp: new Date().toISOString(),
            }

            addMessage(assistantMessage)
        } catch (err) {
            setError('Error al enviar mensaje: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim() || !currentSessionId) return

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
                currentSessionId,
                input,
                documents.map(d => d.id)
            )

            const assistantMessage = {
                role: 'assistant',
                content: response.data.data.response,
                sources: response.data.data.sources || [],
                timestamp: new Date().toISOString(),
            }

            addMessage(assistantMessage)
        } catch (err) {
            setError('Error al enviar mensaje: ' + err.message)
        } finally {
            setLoading(false)
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

    return (
        <div className="flex h-full">
            {/* Sidebar Sessions */}
            <div className="w-64 bg-gray-100 border-r border-gray-300 flex flex-col">
                <button
                    onClick={createSession}
                    className="m-4 flex items-center justify-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={20} />
                    <span>Nueva Sesión</span>
                </button>

                <div className="flex-1 overflow-y-auto">
                    {sessions.map(session => (
                        <div
                            key={session.id}
                            className={clsx(
                                'mx-2 my-1 p-3 rounded-lg cursor-pointer transition-colors group',
                                currentSessionId === session.id
                                    ? 'bg-primary text-white'
                                    : 'bg-white text-gray-800 hover:bg-gray-200'
                            )}
                            onClick={() => {
                                if (editingSessionId !== session.id) {
                                    setCurrentSessionId(session.id)
                                }
                            }}
                        >
                            <div className="flex items-center justify-between">
                                {editingSessionId === session.id ? (
                                    <div className="flex items-center w-full space-x-1" onClick={e => e.stopPropagation()}>
                                        <input
                                            type="text"
                                            value={newTitle}
                                            onChange={e => setNewTitle(e.target.value)}
                                            className="w-full px-2 py-1 text-sm text-black rounded"
                                            autoFocus
                                            onKeyDown={e => {
                                                if (e.key === 'Enter') handleSaveTitle(session.id)
                                                if (e.key === 'Escape') setEditingSessionId(null)
                                            }}
                                        />
                                        <button onClick={() => handleSaveTitle(session.id)} className="p-1 hover:bg-green-500 rounded"><Check size={14} /></button>
                                        <button onClick={() => setEditingSessionId(null)} className="p-1 hover:bg-red-500 rounded"><X size={14} /></button>
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
                                                className="p-1 hover:bg-blue-500 rounded transition-all"
                                                title="Renombrar sesión"
                                            >
                                                <Edit2 size={16} />
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    deleteSession(session.id)
                                                }}
                                                className="p-1 hover:bg-red-500 rounded transition-all"
                                                title="Eliminar sesión"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {!currentSessionId ? (
                        <div className="flex items-center justify-center h-full text-gray-400">
                            <p>Selecciona o crea una nueva sesión para comenzar</p>
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-gray-400">
                            <p>¿Cómo puedo ayudarte hoy?</p>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={clsx(
                                    'flex',
                                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                                )}
                            >
                                <div
                                    className={clsx(
                                        'max-w-md px-4 py-2 rounded-lg',
                                        msg.role === 'user'
                                            ? 'bg-primary text-white'
                                            : 'bg-gray-200 text-gray-800'
                                    )}
                                >
                                    <p className="text-sm">{msg.content}</p>
                                    {msg.sources && msg.sources.length > 0 && (
                                        <div className="mt-2 text-xs opacity-75">
                                            <p className="font-semibold">Fuentes:</p>
                                            <ul className="list-disc list-inside">
                                                {msg.sources.map((src, i) => (
                                                    <li key={i}>{src}</li>
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
                            <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
                                <p className="text-sm">Escribiendo...</p>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded flex justify-between items-center">
                            <span>{error}</span>
                            <button
                                onClick={handleRetry}
                                className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition ml-4 shrink-0"
                            >
                                <RefreshCcw size={14} />
                                <span>Reintentar</span>
                            </button>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                {currentSessionId && (
                    <form onSubmit={sendMessage} className="p-4 border-t border-gray-200">
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Escribe tu pregunta aquí..."
                                disabled={loading}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            >
                                <Send size={20} />
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    )
}
