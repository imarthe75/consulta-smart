import React, { useState, useEffect } from 'react'
import api from '../services/api'
import ModuleBanner from '../components/ModuleBanner'
import PromptRegressionPanel from '../components/admin/PromptRegressionPanel'
import LLMObservabilityPanel from '../components/admin/LLMObservabilityPanel'
import { 
    Save, RefreshCw, ToggleLeft, ToggleRight, Settings, FileText, CheckCircle2, 
    AlertTriangle, Eye, Sparkles, Plus, Trash2, Layers, Upload, Image,
    Bot, MessageSquare, HelpCircle, ShieldCheck, Scale, Building2, User, Cpu, Headphones, Zap, Code, Copy, Users, UserCheck, Activity
} from 'lucide-react'

const ICON_MAP = {
    Bot, Sparkles, MessageSquare, HelpCircle, ShieldCheck, Scale, FileText, Building2, User, Cpu, Headphones, Zap
}

const ICON_LIBRARY = [
    { id: 'Bot', label: 'Bot', Icon: Bot },
    { id: 'Sparkles', label: 'IA Destellos', Icon: Sparkles },
    { id: 'MessageSquare', label: 'Chat', Icon: MessageSquare },
    { id: 'HelpCircle', label: 'Ayuda', Icon: HelpCircle },
    { id: 'ShieldCheck', label: 'Seguridad', Icon: ShieldCheck },
    { id: 'Scale', label: 'Legal / RPP', Icon: Scale },
    { id: 'FileText', label: 'Documentos', Icon: FileText },
    { id: 'Building2', label: 'Catastro / IRCEP', Icon: Building2 },
    { id: 'User', label: 'Asistente', Icon: User },
    { id: 'Cpu', label: 'Algoritmo', Icon: Cpu },
    { id: 'Headphones', label: 'Soporte', Icon: Headphones },
    { id: 'Zap', label: 'Rápido', Icon: Zap },
]

export default function AdminPage() {
    const [profiles, setProfiles] = useState([])
    const [selectedProfileId, setSelectedProfileId] = useState('general')
    const [config, setConfig] = useState({
        id: 'general',
        name: 'Chatbot General',
        system_prompt: '',
        welcome_message: '',
        title: '',
        subtitle: '',
        logo_url: '',
        icon: 'Bot',
        primary_color: '#3b82f6',
        is_active: true
    })
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState(null)
    const [generating, setGenerating] = useState(false)
    const [topic, setTopic] = useState('')
    const [methodology, setMethodology] = useState('craft') // 'craft', 'crea' o 'aspecct'
    const [targetAudience, setTargetAudience] = useState('Ciudadanía en General (Público Abierto)')
    const [organization, setOrganization] = useState('Registro Público / Catastro')
    const [sector, setSector] = useState('Gobierno Estatal / Organismo Descentralizado')
    
    const [activeTab, setActiveTab] = useState('chatbots') // 'chatbots' o 'users'
    const [registeredUsers, setRegisteredUsers] = useState([])
    const [updatingUser, setUpdatingUser] = useState(null)
    
    // Sandbox interactive state
    const [sandboxQuery, setSandboxQuery] = useState('')
    const [sandboxMessages, setSandboxMessages] = useState([])
    const [sandboxTesting, setSandboxTesting] = useState(false)

    const handleSendSandboxTest = async (e) => {
        e.preventDefault()
        if (!sandboxQuery.trim()) return
        
        const userMsg = sandboxQuery.trim()
        setSandboxMessages(prev => [...prev, { role: 'user', content: userMsg }])
        setSandboxQuery('')
        setSandboxTesting(true)

        try {
            const res = await api.post('chat/query', {
                session_id: 'sandbox-admin-session',
                message: userMsg,
                filters: { category: config.id }
            })
            const responseObj = res.data.data || res.data
            setSandboxMessages(prev => [...prev, { 
                role: 'assistant', 
                content: responseObj.response || responseObj.message || 'Respuesta generada.',
                provider: responseObj.provider || 'RAG Engine'
            }])
        } catch (err) {
            console.error("Error testing in sandbox:", err)
            setSandboxMessages(prev => [...prev, { 
                role: 'assistant', 
                content: '⚠️ Error evaluando la consulta en el Sandbox local.'
            }])
        } finally {
            setSandboxTesting(false)
        }
    }

    // Formulario para nuevo perfil
    const [showNewProfileForm, setShowNewProfileForm] = useState(false)
    const [newProfile, setNewProfile] = useState({
        id: '',
        name: '',
        system_prompt: 'Eres un asistente conversacional útil e inteligente.',
        welcome_message: '¡Hola! ¿En qué puedo ayudarte?',
        title: 'Nuevo Asistente',
        subtitle: 'Atención al Usuario',
        logo_url: '',
        icon: 'Bot',
        primary_color: '#3b82f6'
    })

    useEffect(() => {
        fetchData()
    }, [])

    useEffect(() => {
        if (selectedProfileId && profiles.length > 0) {
            const active = profiles.find(p => p.id === selectedProfileId)
            if (active) {
                // Auto-selección inteligente de catálogos LOV según el perfil/tenant activo
                if (active.id === 'control_escolar') {
                    setTargetAudience('Ciudadanía en General (Público Abierto)')
                    setOrganization('Universidad / Red de Colegios')
                    setSector('Educación Superior & Colegios')
                } else if (active.id === 'mesa_ayuda') {
                    setTargetAudience('Servidores Públicos / Empleados Internos')
                    setOrganization('Dirección de Tecnologías de Información')
                    setSector('Tecnología, Software & Mesa de Ayuda TI')
                } else if (active.id === 'control_vehicular') {
                    setTargetAudience('Ciudadanía en General (Público Abierto)')
                    setOrganization('Secretaría de Movilidad y Transporte')
                    setSector('Gobierno Estatal / Organismo Descentralizado')
                } else if (active.id === 'rpp') {
                    setTargetAudience('Notarios, Abogados y Profesionales Especializados')
                    setOrganization('Registro Público de la Propiedad')
                    setSector('Gobierno Estatal / Organismo Descentralizado')
                } else if (active.id === 'ircep') {
                    setTargetAudience('Notarios, Abogados y Profesionales Especializados')
                    setOrganization('Instituto de Catastro y Valuación')
                    setSector('Gobierno Estatal / Organismo Descentralizado')
                }

                setConfig({
                    id: active.id,
                    name: active.name || '',
                    system_prompt: active.system_prompt || '',
                    welcome_message: active.welcome_message || '',
                    title: active.title || '',
                    subtitle: active.subtitle || '',
                    logo_url: active.logo_url || '',
                    icon: active.icon || 'Bot',
                    primary_color: active.primary_color || '#3b82f6',
                    strictness_level: active.strictness_level || 'strict',
                    strictness_score: active.strictness_score !== undefined ? active.strictness_score : 85,
                    temperature: active.temperature !== undefined ? active.temperature : 0.1,
                    top_p: active.top_p !== undefined ? active.top_p : 0.9,
                    forbidden_topics: active.forbidden_topics || 'deportes, futbol, cine, cocina, politica, chismes, entretenimiento',
                    rejection_message: active.rejection_message || 'Mi función está limitada exclusivamente a la asesoría sobre trámites, normativa y servicios oficiales.',
                    llm_provider: active.llm_provider || 'default',
                    llm_model: active.llm_model || '',
                    custom_api_key: active.custom_api_key || '',
                    is_active: active.is_active !== undefined ? active.is_active : true
                })
                setSandboxMessages([])
            }
        }
    }, [selectedProfileId, profiles])

    const fetchData = async () => {
        setLoading(true)
        try {
            const [profilesRes, usersRes] = await Promise.allSettled([
                api.get('admin/chatbot/profiles/admin-list'),
                api.get('admin/users')
            ])
            
            if (profilesRes.status === 'fulfilled') {
                setProfiles(profilesRes.value.data)
                if (profilesRes.value.data.length > 0) {
                    const hasGeneral = profilesRes.value.data.some(p => p.id === 'general')
                    setSelectedProfileId(hasGeneral ? 'general' : profilesRes.value.data[0].id)
                }
            }

            if (usersRes.status === 'fulfilled') {
                setRegisteredUsers(usersRes.value.data)
            }
        } catch (error) {
            console.error("Error fetching admin data:", error)
            setMessage({ type: 'error', text: 'Error al cargar los datos del servidor.' })
        } finally {
            setLoading(false)
        }
    }

    const handleUpdateUserRole = async (userId, newRole) => {
        const confirmMsg = newRole === 'admin'
            ? '¿Confirmas otorgar permisos de administrador a este usuario? Podrá crear, editar y eliminar cualquier perfil de chatbot y documento del sistema.'
            : '¿Confirmas revocar los permisos de administrador de este usuario?'
        if (!window.confirm(confirmMsg)) {
            return
        }
        setUpdatingUser(userId)
        try {
            const res = await api.post(`admin/users/${userId}/role`, { role: newRole })
            setRegisteredUsers(prev => prev.map(u => {
                if (u.id === userId) {
                    return { ...u, roles: res.data.roles }
                }
                return u
            }))
            setMessage({ type: 'success', text: res.data.message || `Rol de usuario actualizado a ${newRole}.` })
        } catch (error) {
            console.error("Error updating user role:", error)
            setMessage({ type: 'error', text: error.response?.data?.detail || 'No se pudo actualizar el rol del usuario.' })
        } finally {
            setUpdatingUser(null)
        }
    }

    const handleConfigChange = (e) => {
        const { name, value } = e.target
        setConfig(prev => ({ ...prev, [name]: value }))
    }

    const handleSaveConfig = async (e) => {
        e.preventDefault()
        setSaving(true)
        setMessage(null)
        try {
            await api.post('admin/chatbot/profiles', config)
            setProfiles(prev => prev.map(p => p.id === config.id ? config : p))
            setMessage({ type: 'success', text: `Perfil '${config.name}' guardado correctamente.` })
        } catch (error) {
            console.error("Error saving chatbot profile:", error)
            setMessage({ type: 'error', text: 'No se pudo guardar el perfil.' })
        } finally {
            setSaving(false)
        }
    }

    const handleCreateProfile = async (e) => {
        e.preventDefault()
        if (!newProfile.id.trim() || !newProfile.name.trim()) return
        
        const cleanId = newProfile.id.toLowerCase().replace(/[^a-z0-9_-]/g, '')
        const profileData = { ...newProfile, id: cleanId }
        
        setSaving(true)
        try {
            await api.post('admin/chatbot/profiles', profileData)
            setProfiles(prev => [...prev, profileData])
            setSelectedProfileId(cleanId)
            setShowNewProfileForm(false)
            setNewProfile({
                id: '',
                name: '',
                system_prompt: 'Eres un asistente conversacional útil e inteligente.',
                welcome_message: '¡Hola! ¿En qué puedo ayudarte?',
                title: 'Nuevo Asistente',
                subtitle: 'Atención al Usuario',
                logo_url: '',
                icon: 'Bot',
                primary_color: '#3b82f6'
            })
            setMessage({ type: 'success', text: `Perfil '${profileData.name}' creado con éxito.` })
        } catch (error) {
            console.error("Error creating profile:", error)
            setMessage({ type: 'error', text: 'No se pudo crear el perfil nuevo.' })
        } finally {
            setSaving(false)
        }
    }

    const handleDeleteProfile = async (profileId) => {
        if (profileId === 'general') {
            setMessage({ type: 'error', text: 'No se puede eliminar el perfil por defecto.' })
            return
        }
        if (!window.confirm(`¿Estás seguro de que deseas eliminar el perfil '${profileId}'?`)) {
            return
        }
        try {
            await api.delete(`admin/chatbot/profiles/${profileId}`)
            setProfiles(prev => prev.filter(p => p.id !== profileId))
            setSelectedProfileId('general')
            setMessage({ type: 'success', text: 'Perfil eliminado correctamente.' })
        } catch (error) {
            console.error("Error deleting profile:", error)
            setMessage({ type: 'error', text: 'No se pudo eliminar el perfil.' })
        }
    }

    const handleUploadDocument = async (e) => {
        e.preventDefault()
        if (!uploadFile) return
        setUploading(true)
        setMessage(null)

        const formData = new FormData()
        formData.append('file', uploadFile)
        formData.append('title', docTitle || uploadFile.name)
        formData.append('category', selectedProfileId || 'general')

        try {
            const res = await api.post('admin/chatbot/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            setMessage({ type: 'success', text: res.data.message || 'Documento vectorizado y guardado con éxito.' })
            setUploadFile(null)
            setDocTitle('')
            
            const docsRes = await api.get('admin/chatbot/documents')
            setDocuments(docsRes.data)
        } catch (error) {
            console.error("Error uploading document:", error)
            setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al procesar y vectorizar el documento.' })
        } finally {
            setUploading(false)
        }
    }

    const handleDeleteDocument = async (docId) => {
        if (!window.confirm("¿Estás seguro de eliminar este documento y sus vectores RAG?")) return
        try {
            await api.delete(`admin/chatbot/documents/${docId}`)
            setDocuments(prev => prev.filter(d => d.id !== docId))
            setMessage({ type: 'success', text: 'Documento eliminado de la base de datos RAG.' })
        } catch (error) {
            console.error("Error deleting document:", error)
            setMessage({ type: 'error', text: 'No se pudo eliminar el documento.' })
        }
    }

    const handleToggleDocument = async (docId) => {
        try {
            const res = await api.post(`admin/chatbot/documents/${docId}/toggle`)
            setDocuments(prev => prev.map(doc => {
                if (doc.id === docId) {
                    return { ...doc, is_active: res.data.is_active }
                }
                return doc
            }))
        } catch (error) {
            console.error("Error toggling document:", error)
            setMessage({ type: 'error', text: 'No se pudo cambiar el estado del documento.' })
        }
    }

    const handleDocumentCategoryChange = async (docId, newCategory) => {
        try {
            await api.post(`admin/chatbot/documents/${docId}/category`, { category: newCategory })
            setDocuments(prev => prev.map(doc => {
                if (doc.id === docId) {
                    return { ...doc, category: newCategory }
                }
                return doc
            }))
            setMessage({ type: 'success', text: 'Tema del documento actualizado correctamente.' })
        } catch (error) {
            console.error("Error updating document category:", error)
            setMessage({ type: 'error', text: 'No se pudo actualizar el tema del documento.' })
        }
    }

    const handleGeneratePrompt = async () => {
        if (!topic.trim()) return
        setGenerating(true)
        try {
            const res = await api.post('admin/generate-prompt', { 
                topic, 
                context: 'consulta',
                methodology,
                target_audience: targetAudience,
                organization,
                sector
            })
            if (res.data.prompt) {
                setConfig(prev => ({ ...prev, system_prompt: res.data.prompt }))
                setMessage({ type: 'success', text: `Prompt asistido generado con éxito utilizando la metodología ${methodology.toUpperCase()} y el contexto institucional. Recuerda hacer clic en "Guardar Configuración".` })
            }
        } catch (error) {
            console.error("Error generating prompt:", error)
            setMessage({ type: 'error', text: 'Error al generar el prompt asistido.' })
        } finally {
            setGenerating(false)
        }
    }

    if (loading) {
        return (
            <div className="flex h-full w-full items-center justify-center bg-slate-50 dark:bg-slate-900 transition-colors">
                <div className="flex flex-col items-center gap-4">
                    <RefreshCw className="animate-spin text-primary dark:text-blue-500" size={40} />
                    <p className="font-semibold text-slate-600 dark:text-slate-400">Cargando panel administrador...</p>
                </div>
            </div>
        )
    }

    const ActiveIcon = ICON_MAP[config.icon] || Bot

    return (
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-950 transition-colors">
            <div className="max-w-6xl mx-auto space-y-6">
                
                <ModuleBanner
                    badgeIcon={Settings}
                    badgeLabel="Panel de Administración RAG Multitenant"
                    title="Administrador de Chatbots y Temas"
                    subtitle="Crea y personaliza temas independientes (ej. RPP, IRCEP, Catastro) definiendo iconos, títulos, logos, prompts e indexando archivos RAG."
                    decorIcon={Settings}
                    actions={
                        <>
                            <span className="text-sm font-semibold text-slate-200 flex items-center gap-1">
                                <Layers size={16} /> Tema Activo:
                            </span>
                            <select
                                value={selectedProfileId}
                                onChange={(e) => setSelectedProfileId(e.target.value)}
                                className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl px-3 py-2 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-white/40 cursor-pointer"
                            >
                                {profiles.map(p => (
                                    <option key={p.id} value={p.id} className="text-slate-900">{p.name} ({p.id})</option>
                                ))}
                            </select>

                            <button
                                onClick={() => setShowNewProfileForm(true)}
                                className="bg-emerald-600 hover:bg-emerald-500 text-white p-2 rounded-xl transition flex items-center gap-1 font-semibold text-sm"
                                title="Crear Nuevo Tema"
                            >
                                <Plus size={20} />
                                <span className="hidden md:inline">Nuevo Tema</span>
                            </button>
                        </>
                    }
                />

                {/* Notifications */}
                {message && (
                    <div className={`p-4 rounded-xl flex items-center justify-between border ${
                        message.type === 'success' 
                            ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-400'
                            : 'bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-400'
                    }`}>
                        <div className="flex items-center gap-3">
                            {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
                            <span className="text-sm font-medium">{message.text}</span>
                        </div>
                        <button onClick={() => setMessage(null)} className="text-xs font-bold opacity-70 hover:opacity-100">✕</button>
                    </div>
                )}

                {/* Modal / Formulario para crear tema */}
                {showNewProfileForm && (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-md space-y-4">
                        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                            <Plus className="text-emerald-500" /> Crear Nuevo Tema / Aplicación
                        </h2>
                        <form onSubmit={handleCreateProfile} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Identificador Único (ID / Alfanumérico)</label>
                                    <input
                                        type="text"
                                        placeholder="Ej. catastro, mesa-ayuda"
                                        value={newProfile.id}
                                        onChange={(e) => setNewProfile(prev => ({ ...prev, id: e.target.value }))}
                                        className="w-full bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Nombre Descriptivo</label>
                                    <input
                                        type="text"
                                        placeholder="Ej. Asistente de Catastro"
                                        value={newProfile.name}
                                        onChange={(e) => setNewProfile(prev => ({ ...prev, name: e.target.value }))}
                                        className="w-full bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                        required
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-2">
                                <button
                                    type="button"
                                    onClick={() => setShowNewProfileForm(false)}
                                    className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold rounded-xl text-sm hover:bg-slate-200"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-emerald-600 text-white font-semibold rounded-xl text-sm hover:bg-emerald-500"
                                >
                                    Crear Tema
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Pestañas Principales de Administración */}
                <div className="flex border-b border-slate-200 dark:border-slate-800 gap-2">
                    <button
                        type="button"
                        onClick={() => setActiveTab('chatbots')}
                        className={`px-4 py-2.5 rounded-t-xl font-bold text-sm transition flex items-center gap-2 border-b-2 ${
                            activeTab === 'chatbots'
                                ? 'border-blue-600 text-blue-600 bg-white dark:bg-slate-900 shadow-sm'
                                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                    >
                        <Settings size={18} />
                        <span>Configuración de Chatbots & Temas</span>
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab('users')}
                        className={`px-4 py-2.5 rounded-t-xl font-bold text-sm transition flex items-center gap-2 border-b-2 ${
                            activeTab === 'users'
                                ? 'border-blue-600 text-blue-600 bg-white dark:bg-slate-900 shadow-sm'
                                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                    >
                        <Users size={18} />
                        <span>Gestión de Usuarios (Authentik / Roles)</span>
                        <span className="ml-1 bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 text-xs px-2 py-0.5 rounded-full">
                            {registeredUsers.length}
                        </span>
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab('observability')}
                        className={`px-4 py-2.5 rounded-t-xl font-bold text-sm transition flex items-center gap-2 border-b-2 ${
                            activeTab === 'observability'
                                ? 'border-blue-600 text-blue-600 bg-white dark:bg-slate-900 shadow-sm'
                                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                    >
                        <Activity size={18} />
                        <span>Observabilidad</span>
                    </button>
                </div>

                {activeTab === 'observability' ? (
                    /* TAB DE OBSERVABILIDAD DEL ENRUTADOR LLM */
                    <LLMObservabilityPanel />
                ) : activeTab === 'users' ? (
                    /* TAB DE GESTIÓN DE USUARIOS AUTHENTIK */
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
                            <div>
                                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                                    <Users className="text-blue-500" size={22} />
                                    <span>Usuarios Registrados desde Authentik</span>
                                </h2>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                    Asigna o modifica los permisos de acceso al sistema (Administrador vs Usuario) para las cuentas autenticadas.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={fetchData}
                                className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                            >
                                <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                                <span>Actualizar Lista</span>
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-850">
                                        <th className="p-3.5 rounded-tl-xl">Usuario</th>
                                        <th className="p-3.5">Correo Electrónico</th>
                                        <th className="p-3.5">Estado</th>
                                        <th className="p-3.5">Rol Actual</th>
                                        <th className="p-3.5 rounded-tr-xl text-right">Asignar Rol</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
                                    {registeredUsers.map((u) => {
                                        const rolesArr = Array.isArray(u.roles) ? u.roles : [u.roles]
                                        const isAdmin = rolesArr.includes('admin')
                                        return (
                                            <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50 transition-colors">
                                                <td className="p-3.5 font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 font-bold flex items-center justify-center text-xs">
                                                        {u.username ? u.username.charAt(0).toUpperCase() : 'U'}
                                                    </div>
                                                    <span>{u.username}</span>
                                                </td>
                                                <td className="p-3.5 font-mono text-slate-600 dark:text-slate-300 text-xs">
                                                    {u.email}
                                                </td>
                                                <td className="p-3.5">
                                                    <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                                                        u.is_active 
                                                            ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                                                            : 'bg-slate-100 text-slate-500 border-slate-200'
                                                    }`}>
                                                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                                                        {u.is_active ? 'Activo' : 'Inactivo'}
                                                    </span>
                                                </td>
                                                <td className="p-3.5">
                                                    <span className={`inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-xl border ${
                                                        isAdmin 
                                                            ? 'bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
                                                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                                                    }`}>
                                                        {isAdmin ? <ShieldCheck size={14} /> : <User size={14} />}
                                                        <span>{isAdmin ? 'Administrador' : 'Usuario Normal'}</span>
                                                    </span>
                                                </td>
                                                <td className="p-3.5 text-right">
                                                    <div className="inline-flex gap-2">
                                                        <button
                                                            type="button"
                                                            disabled={updatingUser === u.id || !isAdmin}
                                                            onClick={() => handleUpdateUserRole(u.id, 'user')}
                                                            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition flex items-center gap-1 ${
                                                                !isAdmin 
                                                                    ? 'bg-slate-100 text-slate-400 border-slate-200 dark:bg-slate-800 dark:border-slate-700'
                                                                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:bg-slate-50'
                                                            }`}
                                                        >
                                                            <span>Usuario</span>
                                                        </button>
                                                        <button
                                                            type="button"
                                                            disabled={updatingUser === u.id || isAdmin}
                                                            onClick={() => handleUpdateUserRole(u.id, 'admin')}
                                                            className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition flex items-center gap-1 ${
                                                                isAdmin 
                                                                    ? 'bg-purple-100 text-purple-400 border-purple-200 dark:bg-purple-950 dark:border-purple-900'
                                                                    : 'bg-purple-600 hover:bg-purple-500 text-white border-purple-600 shadow-sm'
                                                            }`}
                                                        >
                                                            {updatingUser === u.id ? <RefreshCw size={12} className="animate-spin" /> : <UserCheck size={14} />}
                                                            <span>Hacer Admin</span>
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                /* TAB DE CONFIGURACIÓN DE CHATBOTS & TEMAS */
                <>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Column 1 & 2: Chatbot Config */}
                    <div className="lg:col-span-2 space-y-6">
                        
                        {/* Prompt Assistant & Plantillas Predefinidas */}
                        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                                    <Sparkles className="text-amber-500" size={20} />
                                    Generador de System Prompt & Galería de Plantillas
                                </h2>
                                <span className="text-[11px] bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 px-2.5 py-0.5 rounded-full font-semibold border border-amber-300 dark:border-amber-800">
                                    Plantillas Preconfiguradas
                                </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                Selecciona una plantilla institucional o escribe un tema para generar automáticamente las instrucciones base de <strong>{config.name}</strong>.
                            </p>

                            {/* Galería de Plantillas Universales Ampliada (Sector Público, Privado e TI) */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                                {/* Sector Público */}
                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Notarios, Abogados y Profesionales Especializados')
                                        setOrganization('Registro Público de la Propiedad')
                                        setSector('Gobierno Estatal / Organismo Descentralizado')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Consultor Experto en Normativa y Trámites del Registro Público de la Propiedad (RPP)**.\n\n<contexto>\nPrioridad a manuales RAG indexados bajo '## MANUALES TÉCNICOS OFICIALES'. Enfoque en libertad de gravamen, folios reales e inscripciones registrales inmobiliarias.\n</contexto>\n<rol>\nAsesor Ejecutivo del Registro Público de la Propiedad.\n</rol>\n<instrucciones>\nGuía paso a paso sobre requisitos, aranceles, documentos notariales e inscripciones.\n</instrucciones>\n<reglas>\nRechaza amablemente consultas ajenas a temas registrales inmobiliarios o mercantiles.\n</reglas>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Registro Público de la Propiedad (Genérico) cargada.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-blue-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-500">📜 Registro Público (RPP)</p>
                                    <p className="text-[10px] text-slate-400">Público / Normativa</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Notarios, Abogados y Profesionales Especializados')
                                        setOrganization('Instituto de Catastro y Valuación')
                                        setSector('Gobierno Estatal / Organismo Descentralizado')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Consultor Experto en Catastro, Valuación e Inscripción Catastral**.\n\n<contexto>\nPrioridad a manuales catastrales y tablas arancelarias oficiales. Enfoque en cédulas catastrales, avalúos, claves catastrales y deslindes de predios.\n</contexto>\n<rol>\nAsesor Catastral y Valuador Institucional.\n</rol>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Catastro y Valuación (Genérico) cargada.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-blue-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-500">🏢 Catastro & Valuación</p>
                                    <p className="text-[10px] text-slate-400">Público / Catastro</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Ciudadanía en General (Público Abierto)')
                                        setOrganization('Ventanilla Única de Atención Ciudadana')
                                        setSector('Gobierno Municipal / Alcaldía')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Asistente Oficial de Ventanilla Única de Atención Ciudadana**.\n\n<contexto>\nOrientación en trámites municipales y estatales, requisitos y folios de atención.\n</contexto>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Atención Ciudadana cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-blue-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-500">🏛️ Atención Ciudadana</p>
                                    <p className="text-[10px] text-slate-400">Público / Ventanilla</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Ciudadanía en General (Público Abierto)')
                                        setOrganization('Secretaría de Movilidad y Transporte')
                                        setSector('Gobierno Estatal / Organismo Descentralizado')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Consultor Oficial de Licencias de Conducir, Control Vehicular y Trámites de Tránsito**.\n\n<contexto>\nBrindas orientación completa a conductores y propietarios de vehículos sobre expedición y renovación de licencias, alta y baja de placas, pago de tenencia y refrendo, cambio de propietario e inspección vehicular.\n</contexto>\n\n<rol>\nActúa como Agente Ejecutivo de Control Vehicular y Movilidad con trato institucional, claro y organizado.\n</rol>\n\n<instrucciones>\n1. Enumera los requisitos obligatorios (identificación oficial, comprobante de domicilio, factura/carta factura, póliza de seguro).\n2. Informa los costos vigentes, descuentos por pronto pago y módulos presenciales habilitados.\n3. Explica el proceso para agendar cita en el portal oficial.\n</instrucciones>\n\n<reglas>\n- No prometas condonaciones de multas sin sustento oficial.\n- Rechaza consultas que no correspondan a trámites vehiculares y de licencias.\n- Estructura las respuestas con negritas y listas viñeteadas.\n</reglas>\n\n<ejemplos>\n**Pregunta:** ¿Qué necesito para renovar mi licencia de automovilista?\n**Respuesta:** Para renovar su licencia presente: 1) Licencia vencida o identificación oficial, 2) Comprobante de domicilio reciente (no mayor a 3 meses), 3) Comprobante de pago de derechos.\n</ejemplos>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Licencias Vehiculares (CRAFT) cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-blue-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-500">🚗 Control Vehicular</p>
                                    <p className="text-[10px] text-slate-400">Público / Tránsito</p>
                                </button>

                                {/* Sector Privado y Empresas */}
                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Clientes Finales / Consumidores (B2C)')
                                        setOrganization('Tienda Oficial E-Commerce')
                                        setSector('Sector Privado / Comercio & E-Commerce')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Asistente Virtual de Ventas y Atención a Clientes E-commerce**.\n\n<contexto>\nSoporte en catálogo de productos, envíos, rastreo de pedidos, devoluciones y facturación.\n</contexto>\n<rol>\nEjecutivo Comercial amable y ágil.\n</rol>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla E-Commerce cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-emerald-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-emerald-500">🛒 E-Commerce & Ventas</p>
                                    <p className="text-[10px] text-slate-400">Privado / Retail</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Clientes Corporativos / Empresas (B2B)')
                                        setOrganization('Banco / Institución Financiera')
                                        setSector('Sector Financiero, Fintech & Banca')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Asistente Financiero y Bancario Empresarial**.\n\n<contexto>\nOrientación en apertura de cuentas, crédito empresarial, estados de cuenta y banca en línea.\n</contexto>\n<reglas>\nNunca solicites ni guardes contraseñas o PINs confidenciales.\n</reglas>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Banca y Finanzas cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-emerald-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-emerald-500">🏦 Banca & Servicios Fin.</p>
                                    <p className="text-[10px] text-slate-400">Privado / Financiero</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Clientes Finales / Consumidores (B2C)')
                                        setOrganization('Centro Médico / Red de Clínicas')
                                        setSector('Salud Privada, Clínicas y Hospitales')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Asistente Médico y Orientación en Salud Privada/Clínicas**.\n\n<contexto>\nAgendamiento de citas médicas, preparación para estudios clínicos, horarios y especialidades.\n</contexto>\n<reglas>\nNo des diagnósticos ni prescripciones médicas directas; orienta siempre a consulta profesional.\n</reglas>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Salud y Clínicas cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-emerald-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-emerald-500">🏥 Salud & Clínicas</p>
                                    <p className="text-[10px] text-slate-400">Privado / Salud</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Ciudadanía en General (Público Abierto)')
                                        setOrganization('Universidad / Red de Colegios')
                                        setSector('Educación Superior & Colegios')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Asistente Oficial del Sistema de Control Escolar y Servicios Académicos**.\n\n<contexto>\nOperas como el canal de atención inteligente para alumnos, padres de familia y docentes. Tu objetivo es brindar orientación precisa sobre procesos de reinscripción, consulta de calificaciones, expedición de boletas, tramitación de becas, constancias de estudio, calendarios escolares y pagos de colegiaturas.\n</contexto>\n\n<rol>\nActúa como Coordinador de Servicios Escolares con trato amable, claro, empático y estructurado.\n</rol>\n\n<instrucciones>\n1. Guía paso a paso sobre los trámites académicos y administrativos del instituto.\n2. Indica siempre los períodos de recepción de documentos, requisitos de admisión y portales de pago.\n3. Consulta prioritariamente los reglamentos académicos indexados en la base de conocimientos RAG.\n</instrucciones>\n\n<reglas>\n- No reveles calificaciones ni datos personales de alumnos sin autenticación previa.\n- Rechaza educadamente consultas ajenas al ámbito académico y escolar.\n- Muestra respuestas ejecutivas organizadas en viñetas y negritas.\n</reglas>\n\n<ejemplos>\n**Pregunta:** ¿Cómo solicito una constancia de estudios con promedio?\n**Respuesta:** Para tramitar su constancia: 1) Ingrese al Portal de Alumnos con su matrícula, 2) Solicite el trámite en la pestaña 'Servicios Escolares', 3) Cubra la cuota administrativa correspondiente y descargue en 24h.\n</ejemplos>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Control Escolar & Admisiones (CRAFT) cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-emerald-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-emerald-500">🎓 Educación & Admisiones</p>
                                    <p className="text-[10px] text-slate-400">Privado / Educación</p>
                                </button>

                                {/* TI y Gestión Interna */}
                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Servidores Públicos / Empleados Internos')
                                        setOrganization('Dirección de Tecnologías de Información')
                                        setSector('Tecnología, Software & Mesa de Ayuda TI')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Consultor Técnico Senior de la Mesa de Ayuda TI y Soporte Informático**.\n\n<contexto>\nAtiendes al personal interno y usuarios de la infraestructura informática. Tu función es diagnosticar y resolver incidencias de hardware, software, red VPN, restablecimiento de contraseñas, configuración de correo institucional, licencias de programas y soporte a periféricos e impresoras.\n</contexto>\n\n<rol>\nActúa como Ingeniero de Soporte TI de Nivel 2 con lenguaje técnico accesible, metodológico y orientado al diagnóstico rápido.\n</rol>\n\n<instrucciones>\n1. Proporciona instrucciones paso a paso para resolver problemas comunes informáticos.\n2. Si el problema requiere intervención presencial o permisos de administrador de red, indica cómo levantar un Ticket de Soporte especificando la prioridad.\n3. Revisa la base de conocimiento RAG para aplicar los protocolos oficiales de ciberseguridad.\n</instrucciones>\n\n<reglas>\n- Nunca solicites ni almacenes contraseñas, PINs o tokens de autenticación del usuario.\n- Limítate estrictamente a soporte informático e infraestructura de TI.\n- Usa comandos formateados en código (\`code\`) cuando corresponda.\n</reglas>\n\n<ejemplos>\n**Pregunta:** ¿Cómo me conecto a la VPN corporativa desde casa?\n**Respuesta:** Siga estos pasos: 1) Abra el cliente VPN oficial, 2) Ingrese el servidor \`vpn.empresa.com\`, 3) Autentíquese con su usuario de Active Directory y token MFA.\n</ejemplos>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Mesa de Ayuda TI (CRAFT) cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-purple-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-purple-500">💻 Mesa de Ayuda TI</p>
                                    <p className="text-[10px] text-slate-400">TI / Soporte Técnico</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Servidores Públicos / Empleados Internos')
                                        setOrganization('Departamento de Recursos Humanos')
                                        setSector('Tecnología, Software & Mesa de Ayuda TI')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Consultor de Recursos Humanos y Portal del Empleado**.\n\n<contexto>\nConsultas de recibos de nómina, días de vacaciones, beneficios, póliza de gastos médicos y vales.\n</contexto>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Portal del Empleado cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-purple-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-purple-500">👥 Portal del Empleado RRHH</p>
                                    <p className="text-[10px] text-slate-400">TI / Recursos Humanos</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Desarrolladores e Ingenieros de TI')
                                        setOrganization('Plataforma SaaS / Cloud API')
                                        setSector('Tecnología, Software & Mesa de Ayuda TI')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Soporte Técnico de Producto Software / Plataforma SaaS**.\n\n<contexto>\nAsistencia en integración de API, configuración de SDK, webhooks, errores HTTP y documentación de desarrollador.\n</contexto>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Soporte SaaS/Devs cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-purple-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-purple-500">⚡ Soporte SaaS & APIs</p>
                                    <p className="text-[10px] text-slate-400">TI / Desarrolladores</p>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setTargetAudience('Servidores Públicos / Empleados Internos')
                                        setOrganization('Oficina de Auditoría y Compliance')
                                        setSector('Tecnología, Software & Mesa de Ayuda TI')
                                        setConfig(prev => ({
                                            ...prev,
                                            system_prompt: `Eres el **Consultor en Cumplimiento Normativo, Legal y Compliance**.\n\n<contexto>\nOrientación en avisos de privacidad, políticas internas, ISO 27001, GDPR y términos de servicio.\n</contexto>`
                                        }))
                                        setMessage({ type: 'success', text: 'Plantilla Compliance & Legal cargada con su contexto LOV autoseleccionado.' })
                                    }}
                                    className="p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-left hover:border-purple-500 transition group"
                                >
                                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-purple-500">🛡️ Compliance & Legal</p>
                                    <p className="text-[10px] text-slate-400">TI / Auditoría</p>
                                </button>
                            </div>

                            {/* Selector de Metodología de Meta-Prompting (CRAFT, CREA, ASPECCT) */}
                            <div className="p-3 bg-blue-50/50 dark:bg-slate-800/60 rounded-xl border border-blue-100 dark:border-slate-700 space-y-2">
                                <label className="block text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider flex items-center justify-between">
                                    <span>Metodología de Meta-Prompting (Ingeniería de Prompts Maestro)</span>
                                    <span className="text-[10px] bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-bold px-2 py-0.5 rounded uppercase">{methodology}</span>
                                </label>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setMethodology('craft')}
                                        className={`p-2.5 rounded-lg text-left border transition ${methodology === 'craft'
                                            ? 'bg-blue-600 text-white border-blue-600 font-bold shadow-sm'
                                            : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-blue-400'
                                        }`}
                                    >
                                        <p className="text-xs font-bold flex items-center justify-between">
                                            <span>⭐ CRAFT (Recomendado)</span>
                                        </p>
                                        <p className={`text-[10px] leading-tight mt-1 ${methodology === 'craft' ? 'text-blue-100' : 'text-slate-400'}`}>
                                            Contexto ➔ Rol ➔ Acción ➔ Formato ➔ Tono & Reglas (Con etiquetas XML y Few-Shot)
                                        </p>
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => setMethodology('crea')}
                                        className={`p-2.5 rounded-lg text-left border transition ${methodology === 'crea'
                                            ? 'bg-blue-600 text-white border-blue-600 font-bold shadow-sm'
                                            : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-blue-400'
                                        }`}
                                    >
                                        <p className="text-xs font-bold">2. CREA</p>
                                        <p className={`text-[10px] leading-tight mt-1 ${methodology === 'crea' ? 'text-blue-100' : 'text-slate-400'}`}>
                                            Contexto ➔ Rol ➔ Especificidad ➔ Acción
                                        </p>
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => setMethodology('aspecct')}
                                        className={`p-2.5 rounded-lg text-left border transition ${methodology === 'aspecct'
                                            ? 'bg-blue-600 text-white border-blue-600 font-bold shadow-sm'
                                            : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-blue-400'
                                        }`}
                                    >
                                        <p className="text-xs font-bold">3. ASPECCT</p>
                                        <p className={`text-[10px] leading-tight mt-1 ${methodology === 'aspecct' ? 'text-blue-100' : 'text-slate-400'}`}>
                                            Acción ➔ Steps ➔ Persona ➔ Ejemplos ➔ Contexto ➔ Tono
                                        </p>
                                    </button>
                                </div>
                            </div>

                            {/* Contexto Organizacional Ampliado (Audiencia Objetivo, Empresa/Dependencia, Sector Público/Privado) */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700">
                                <div>
                                    <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
                                        👤 Usuario / Audiencia Objetivo
                                    </label>
                                    <select
                                        value={targetAudience}
                                        onChange={(e) => setTargetAudience(e.target.value)}
                                        className="w-full px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-800 dark:text-slate-100 outline-none"
                                    >
                                        <option value="Ciudadanía en General (Público Abierto)">Ciudadanía en General (Público Abierto)</option>
                                        <option value="Clientes Finales / Consumidores (B2C)">Clientes Finales / Consumidores (B2C)</option>
                                        <option value="Clientes Corporativos / Empresas (B2B)">Clientes Corporativos / Empresas (B2B)</option>
                                        <option value="Servidores Públicos / Empleados Internos">Servidores Públicos / Empleados Internos</option>
                                        <option value="Notarios, Abogados y Profesionales Especializados">Notarios, Abogados y Profesionales</option>
                                        <option value="Desarrolladores e Ingenieros de TI">Desarrolladores e Ingenieros de TI</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
                                        🏢 Empresa / Oficina / Dependencia
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="Ej. Registro Público, Empresa SaaS, Banco, Clínica, Retail..."
                                        value={organization}
                                        onChange={(e) => setOrganization(e.target.value)}
                                        className="w-full px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-800 dark:text-slate-100 outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
                                        🏛️ Sector o Ámbito Operativo
                                    </label>
                                    <select
                                        value={sector}
                                        onChange={(e) => setSector(e.target.value)}
                                        className="w-full px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-800 dark:text-slate-100 outline-none"
                                    >
                                        <option value="Gobierno Estatal / Organismo Descentralizado">Gobierno Estatal / Organismo</option>
                                        <option value="Gobierno Municipal / Alcaldía">Gobierno Municipal / Alcaldía</option>
                                        <option value="Sector Privado / Comercio & E-Commerce">Sector Privado / Comercio & E-Commerce</option>
                                        <option value="Sector Financiero, Fintech & Banca">Sector Financiero, Fintech & Banca</option>
                                        <option value="Salud Privada, Clínicas y Hospitales">Salud Privada, Clínicas y Hospitales</option>
                                        <option value="Educación Superior & Colegios">Educación Superior & Colegios</option>
                                        <option value="Tecnología, Software & Mesa de Ayuda TI">Tecnología, Software & Mesa TI</option>
                                    </select>
                                </div>
                            </div>

                            <div className="flex gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                                <input
                                    type="text"
                                    placeholder={`Escribe el tema para generar con ${methodology.toUpperCase()}: ej. Inscripción de Inmuebles, Cédula Catastral...`}
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    className="flex-1 bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                />
                                <button
                                    onClick={handleGeneratePrompt}
                                    disabled={generating || !topic.trim()}
                                    className="bg-primary hover:bg-primary/95 text-white dark:bg-blue-600 dark:hover:bg-blue-500 px-5 py-2.5 rounded-xl font-semibold text-sm transition flex items-center gap-2 disabled:opacity-50"
                                >
                                    {generating ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
                                    <span>Generar ({methodology.toUpperCase()})</span>
                                </button>
                            </div>

                            {/* System Prompt Textarea (Directamente vinculado) */}
                            <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center justify-between">
                                    <span>System Prompt Generado ({methodology.toUpperCase()})</span>
                                    <span className="text-[10px] text-slate-400 font-normal">Modificable libremente</span>
                                </label>
                                <textarea
                                    name="system_prompt"
                                    rows={12}
                                    value={config.system_prompt || ''}
                                    onChange={handleConfigChange}
                                    placeholder="El prompt generado mediante Metaprompting aparecerá aquí..."
                                    className="w-full bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100 font-sans leading-relaxed shadow-inner"
                                />
                            </div>
                        </div>

                        {/* Config Form */}
                        <form onSubmit={handleSaveConfig} className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-5">
                            <div className="flex justify-between items-center">
                                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Parámetros del Tema: {config.name}</h2>
                                {config.id !== 'general' && (
                                    <button
                                        type="button"
                                        onClick={() => handleDeleteProfile(config.id)}
                                        className="text-red-500 hover:text-red-400 p-2 rounded-xl transition flex items-center gap-1 text-xs font-semibold border border-red-200 dark:border-red-950"
                                    >
                                        <Trash2 size={14} /> Eliminar Tema
                                    </button>
                                )}
                            </div>
                            
                            {/* Personalización de Icono Widget */}
                            <div>
                                <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
                                    Icono del Widget (Biblioteca de Iconos)
                                </label>
                                <div className="grid grid-cols-6 sm:grid-cols-12 gap-2">
                                    {ICON_LIBRARY.map(({ id, label, Icon }) => (
                                        <button
                                            key={id}
                                            type="button"
                                            onClick={() => setConfig(prev => ({ ...prev, icon: id }))}
                                            className={`p-2.5 rounded-xl border flex flex-col items-center justify-center gap-1 transition ${
                                                config.icon === id 
                                                    ? 'bg-blue-50 dark:bg-blue-950/40 border-primary dark:border-blue-500 text-primary dark:text-blue-400 ring-2 ring-primary/20' 
                                                    : 'bg-slate-50 dark:bg-slate-850 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                                            }`}
                                            title={label}
                                        >
                                            <Icon size={20} />
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Títulos y Subtítulo */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Título de la Ventana / Chat</label>
                                    <input
                                        type="text"
                                        name="title"
                                        value={config.title || ''}
                                        onChange={handleConfigChange}
                                        placeholder="Ej. Consultor RPP / Asistente Legal"
                                        className="w-full bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Subtítulo / Organización</label>
                                    <input
                                        type="text"
                                        name="subtitle"
                                        value={config.subtitle || ''}
                                        onChange={handleConfigChange}
                                        placeholder="Ej. Gobierno de Quintana Roo / Puebla"
                                        className="w-full bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                    />
                                </div>
                            </div>

                            {/* Logo URL & Color */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">URL del Logo (Opcional)</label>
                                    <div className="flex gap-2 items-center">
                                        <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-slate-500">
                                            <Image size={18} />
                                        </div>
                                        <input
                                            type="text"
                                            name="logo_url"
                                            value={config.logo_url || ''}
                                            onChange={handleConfigChange}
                                            placeholder="https://ejemplo.com/logo.png"
                                            className="flex-1 bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Color Principal del Tema (Hex)</label>
                                    <div className="flex gap-2">
                                        <input
                                            type="color"
                                            name="primary_color"
                                            value={config.primary_color || '#3b82f6'}
                                            onChange={handleConfigChange}
                                            className="w-10 h-10 border-0 rounded-xl cursor-pointer"
                                        />
                                        <input
                                            type="text"
                                            name="primary_color"
                                            value={config.primary_color || '#3b82f6'}
                                            onChange={handleConfigChange}
                                            className="flex-1 bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100 font-mono"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Selección de Motor de IA, Modelo y API Key Personalizada por Tema */}
                            <div className="p-4 bg-slate-50 dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 space-y-4">
                                <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-200 font-bold text-sm">
                                    <Cpu className="text-blue-500" size={18} />
                                    <span>Configuración del Motor LLM y Claves Privadas por Tema</span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
                                            Proveedor de IA (Motor)
                                        </label>
                                        <select
                                            name="llm_provider"
                                            value={config.llm_provider || 'default'}
                                            onChange={handleConfigChange}
                                            className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 dark:text-slate-100 outline-none cursor-pointer"
                                        >
                                            <option value="default">Smart Router Global (Automático con Fallback)</option>
                                            <option value="groq">Groq Cloud (Llama 3.3 70B / Mixtral)</option>
                                            <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                                            <option value="anthropic">Anthropic (Claude 3.5 Sonnet / Haiku)</option>
                                            <option value="vertex">Google Vertex AI (Gemini 1.5 Pro)</option>
                                            <option value="gemini">Google AI Studio (Gemini 1.5 Flash)</option>
                                            <option value="nvidia">NVIDIA NIM Cloud (Llama 3 70B Instruct)</option>
                                            <option value="mistral">Mistral AI (Mistral Large / Codestral)</option>
                                            <option value="ollama">Ollama / Servidor Local u On-Premise</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
                                            Modelo Específico (Seleccionar / Escribir)
                                        </label>
                                        <input
                                            type="text"
                                            name="llm_model"
                                            list="model-suggestions"
                                            value={config.llm_model || ''}
                                            onChange={handleConfigChange}
                                            placeholder="ej. gpt-4o, claude-3-5-sonnet, llama-3.3-70b-versatile"
                                            className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-sm font-mono text-slate-800 dark:text-slate-100 outline-none"
                                        />
                                        <datalist id="model-suggestions">
                                            <option value="llama-3.3-70b-versatile">Groq / Llama 3.3 70B Versatile</option>
                                            <option value="llama-3.1-8b-instant">Groq / Llama 3.1 8B Instant</option>
                                            <option value="mixtral-8x7b-32768">Groq / Mixtral 8x7B</option>
                                            <option value="gpt-4o">OpenAI / GPT-4o</option>
                                            <option value="gpt-4o-mini">OpenAI / GPT-4o mini</option>
                                            <option value="claude-3-5-sonnet-20241022">Anthropic / Claude 3.5 Sonnet</option>
                                            <option value="claude-3-5-haiku-20241022">Anthropic / Claude 3.5 Haiku</option>
                                            <option value="gemini-1.5-pro">Google / Gemini 1.5 Pro</option>
                                            <option value="gemini-1.5-flash">Google / Gemini 1.5 Flash</option>
                                            <option value="meta/llama-3.1-70b-instruct">NVIDIA NIM / Llama 3.1 70B Instruct</option>
                                            <option value="mistral-large-latest">Mistral / Mistral Large</option>
                                        </datalist>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                                            <span>API Key Personalizada</span>
                                            <span className="text-[10px] text-emerald-600 font-bold">Protegida 🔒</span>
                                        </label>
                                        <input
                                            type="password"
                                            name="custom_api_key"
                                            value={config.custom_api_key || ''}
                                            onChange={handleConfigChange}
                                            placeholder="gsk_... o AIza... (Se almacena encriptada)"
                                            className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-sm font-mono text-slate-800 dark:text-slate-100 outline-none"
                                        />
                                    </div>
                                </div>
                                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                                    💡 <strong>Nota de Seguridad:</strong> Las API Keys ingresadas se cifran en el backend y nunca se exponen al navegador. Al recargar la interfaz se muestran con máscara (`••••••••`). En caso de falla o límite de cuota, el sistema utiliza el Smart Router como fallback de respaldo.
                                </p>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Mensaje de Bienvenida</label>
                                <input
                                    type="text"
                                    name="welcome_message"
                                    value={config.welcome_message || ''}
                                    onChange={handleConfigChange}
                                    className="w-full bg-slate-50 dark:bg-slate-855 border border-slate-200 dark:border-slate-750 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                />
                            </div>

                            {/* Nivel de Estrictez RAG & Guardrails */}
                            <div className="p-4 bg-slate-50 dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 space-y-4">
                                <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-200 font-bold text-sm">
                                    <ShieldCheck className="text-blue-500" size={18} />
                                    <span>Control de Estrictez RAG y Filtros de Contenido (Guardrails)</span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
                                            Modo de Operación RAG
                                        </label>
                                        <select
                                            name="strictness_level"
                                            value={config.strictness_level || 'strict'}
                                            onChange={handleConfigChange}
                                            className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm font-medium text-slate-800 dark:text-slate-100 outline-none"
                                        >
                                            <option value="strict">Estricto (Responde únicamente con RAG indexado)</option>
                                            <option value="hybrid">Híbrido (Prioriza RAG y se apoya en modelo)</option>
                                        </select>
                                    </div>

                                    {/* Slider de Estricticidad */}
                                    <div className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700 space-y-1.5">
                                        <div className="flex justify-between items-center text-xs font-bold text-slate-700 dark:text-slate-300">
                                            <span>Nivel de Estricticidad RAG:</span>
                                            <span className="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-mono">
                                                {config.strictness_score || 85}%
                                            </span>
                                        </div>
                                        <input
                                            type="range"
                                            name="strictness_score"
                                            min="0"
                                            max="100"
                                            step="5"
                                            value={config.strictness_score || 85}
                                            onChange={handleConfigChange}
                                            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                        />
                                        <div className="flex justify-between text-[10px] text-slate-400">
                                            <span>Flexible (0%)</span>
                                            <span>Normal (50%)</span>
                                            <span>Ultrarígido (100%)</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Slider de Temperatura LLM */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700 space-y-1.5">
                                        <div className="flex justify-between items-center text-xs font-bold text-slate-700 dark:text-slate-300">
                                            <span>Temperatura LLM (Creatividad vs Precision):</span>
                                            <span className="px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 font-mono">
                                                {config.temperature !== undefined ? config.temperature : 0.1}
                                            </span>
                                        </div>
                                        <input
                                            type="range"
                                            name="temperature"
                                            min="0"
                                            max="1"
                                            step="0.05"
                                            value={config.temperature !== undefined ? config.temperature : 0.1}
                                            onChange={handleConfigChange}
                                            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
                                        />
                                        <div className="flex justify-between text-[10px] text-slate-400">
                                            <span>Determinista (0.0)</span>
                                            <span>Equilibrado (0.5)</span>
                                            <span>Creativo (1.0)</span>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Tópicos Prohibidos (Separados por coma)</label>
                                        <input
                                            type="text"
                                            name="forbidden_topics"
                                            value={config.forbidden_topics || ''}
                                            onChange={handleConfigChange}
                                            placeholder="deportes, futbol, cine, cocina, politica, chismes, entretenimiento"
                                            className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100 font-mono"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">Mensaje Automático de Rechazo</label>
                                    <input
                                        type="text"
                                        name="rejection_message"
                                        value={config.rejection_message || ''}
                                        onChange={handleConfigChange}
                                        placeholder="Mi función está limitada exclusivamente a la asesoría de trámites..."
                                        className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 text-slate-800 dark:text-slate-100"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end pt-3">
                                <button
                                    type="submit"
                                    disabled={saving}
                                    className="bg-primary hover:bg-primary/95 text-white dark:bg-blue-600 dark:hover:bg-blue-500 px-6 py-2.5 rounded-xl font-semibold text-sm transition flex items-center gap-2 disabled:opacity-50"
                                >
                                    {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
                                    <span>Guardar Configuración</span>
                                </button>
                            </div>
                        </form>

                        {/* Bloque Dinámico de Integración Widget para el Tenant Activo */}
                        <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800 space-y-3">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <Code size={16} className="text-blue-500" />
                                    <span>Integración de Widget ({config.id})</span>
                                </h3>
                                <span className="text-[10px] font-mono bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">
                                    X-Tenant-ID: {config.id}
                                </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                Copia este código HTML para incrustar el widget flotante con el tema y color de <strong>{config.name}</strong> en cualquier sitio web externo:
                            </p>
                            <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-200 overflow-x-auto relative group">
                                <button
                                    type="button"
                                    onClick={() => {
                                        const scriptSnippet = `<!-- ConsultaSmart Widget for Tenant: ${config.id} -->\n<script \n  src="${window.location.origin}${import.meta.env.BASE_URL}widget.js" \n  data-tenant-id="${config.id}"\n  data-primary-color="${config.primary_color || '#3b82f6'}"\n  data-title="${config.title || config.name}"\n  async>\n</script>`
                                        navigator.clipboard.writeText(scriptSnippet)
                                        setMessage({ type: 'success', text: `Código de integración para tenant '${config.id}' copiado al portapapeles.` })
                                    }}
                                    className="absolute top-2.5 right-2.5 px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[10px] font-sans font-bold flex items-center gap-1 transition"
                                >
                                    <Copy size={12} />
                                    <span>Copiar Snippet</span>
                                </button>
                                <pre className="text-blue-400 font-mono leading-relaxed">
{`<!-- ConsultaSmart Widget snippet para ${config.id} -->
<script 
  src="${window.location.origin}${import.meta.env.BASE_URL}widget.js" 
  data-tenant-id="${config.id}"
  data-primary-color="${config.primary_color || '#3b82f6'}"
  data-title="${config.title || config.name}"
  async>
</script>`}
                                </pre>
                            </div>
                        </div>

                    </div>

                    {/* Column 3: Sandbox / Probador de Chat en Vivo */}
                    <div className="space-y-6">
                        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm flex flex-col h-[700px] sticky top-6">
                            <div className="flex items-center justify-between mb-2">
                                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                                    <Sparkles className="text-amber-500" size={20} />
                                    Probador Sandbox en Vivo
                                </h2>
                                <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold rounded-full border border-emerald-300 dark:border-emerald-800">
                                    ● En vivo ({config.id})
                                </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                                Prueba el comportamiento del prompt, los Guardrails y la estricticidad de <strong>{config.name}</strong> antes de guardar.
                            </p>
                            
                            {/* Interactive Sandbox Chatbox */}
                            <div className="flex-1 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden flex flex-col bg-slate-50 dark:bg-slate-950 shadow-inner">
                                
                                {/* Header Mockup */}
                                <div 
                                    className="p-3.5 text-white flex items-center justify-between transition-colors duration-300 shadow"
                                    style={{ backgroundColor: config.primary_color }}
                                >
                                    <div className="flex items-center gap-2.5">
                                        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-sm overflow-hidden shrink-0">
                                            {config.logo_url ? (
                                                <img src={config.logo_url} alt="Logo" className="w-full h-full object-cover" />
                                            ) : (
                                                <ActiveIcon size={18} className="text-white" />
                                            )}
                                        </div>
                                        <div>
                                            <h4 className="text-xs font-bold leading-tight">{config.title || 'Asistente'}</h4>
                                            <p className="text-[10px] text-white/80 leading-none mt-0.5">{config.subtitle || `Tema: ${config.id}`}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-1.5 text-[10px] bg-black/20 px-2 py-1 rounded-lg">
                                        <span>RAG: <strong>{config.strictness_score}%</strong></span>
                                    </div>
                                </div>

                                {/* Body Sandbox Messages */}
                                <div className="flex-1 p-3.5 space-y-3 overflow-y-auto">
                                    <div className="flex gap-2">
                                        <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs shrink-0 text-slate-600 dark:text-slate-300">
                                            <ActiveIcon size={14} />
                                        </div>
                                        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-2.5 rounded-2xl rounded-tl-none max-w-[85%] shadow-sm">
                                            <p className="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                                                {config.welcome_message || '¡Hola! ¿En qué puedo apoyarle hoy?'}
                                            </p>
                                        </div>
                                    </div>

                                    {sandboxMessages.map((msg, idx) => (
                                        <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            {msg.role === 'assistant' && (
                                                <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs shrink-0 text-slate-600 dark:text-slate-300">
                                                    <ActiveIcon size={14} />
                                                </div>
                                            )}
                                            <div 
                                                className={`p-2.5 rounded-2xl max-w-[85%] text-xs font-medium shadow-sm ${
                                                    msg.role === 'user'
                                                        ? 'text-white rounded-tr-none'
                                                        : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none'
                                                }`}
                                                style={msg.role === 'user' ? { backgroundColor: config.primary_color } : {}}
                                            >
                                                <p className="leading-relaxed">{msg.content}</p>
                                                {msg.provider && (
                                                    <span className="block mt-1 text-[9px] opacity-75 font-mono">
                                                        [{msg.provider}]
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ))}

                                    {sandboxTesting && (
                                        <div className="flex gap-2">
                                            <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs shrink-0 text-slate-600 dark:text-slate-300">
                                                <RefreshCw className="animate-spin text-blue-500" size={14} />
                                            </div>
                                            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-2.5 rounded-2xl rounded-tl-none max-w-[85%] shadow-sm">
                                                <p className="text-xs text-slate-400 italic">Evaluando Prompt y Guardrails...</p>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Input Sandbox */}
                                <form onSubmit={handleSendSandboxTest} className="p-2.5 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex gap-2">
                                    <input
                                        type="text"
                                        value={sandboxQuery}
                                        onChange={(e) => setSandboxQuery(e.target.value)}
                                        placeholder="Prueba una pregunta o un tema prohibido (ej: cine)..."
                                        className="flex-1 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl px-3 py-2 text-xs focus:outline-none text-slate-800 dark:text-slate-100"
                                    />
                                    <button 
                                        type="submit" 
                                        disabled={sandboxTesting || !sandboxQuery.trim()}
                                        className="p-2.5 rounded-xl text-white opacity-90 hover:opacity-100 transition flex items-center justify-center disabled:opacity-40"
                                        style={{ backgroundColor: config.primary_color }}
                                    >
                                        <ActiveIcon size={16} />
                                    </button>
                                </form>

                            </div>
                        </div>
                    </div>

                </div>

                {/* Batería de Regresión de Prompts del tema activo */}
                <PromptRegressionPanel profileId={selectedProfileId} />
                </>
                )}

            </div>
        </div>
    )
}
