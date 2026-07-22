import React, { useState, useRef, useEffect } from 'react'
import { useDocumentStore } from '../stores/documentStore'
import { documentsAPI } from '../services/api'
import api from '../services/api'
import { Upload, X, AlertCircle, FileText, Layers, RefreshCw, CheckCircle2 } from 'lucide-react'

export default function DocumentUpload({ tenantId = 'all' }) {
    const [dragActive, setDragActive]       = useState(false)
    const [targetTenant, setTargetTenant]   = useState(tenantId !== 'all' ? tenantId : '')
    const [category, setCategory]           = useState('reglamentos')
    const [profiles, setProfiles]           = useState([])
    // Estado de reindexado: { [docId]: 'loading' | 'done' | 'error' }
    const [reindexStatus, setReindexStatus] = useState({})
    const fileInputRef = useRef(null)

    const { documents, addDocument, setDocuments, setLoading, setError, setUploadProgress, clearError } = useDocumentStore()

    // Cargar perfiles de la BD para asociar el proyecto/tenant
    useEffect(() => {
        const loadProfiles = async () => {
            try {
                const res = await api.get('admin/chatbot/profiles')
                if (Array.isArray(res.data)) {
                    setProfiles(res.data)
                    if (tenantId === 'all' && res.data.length > 0) {
                        setTargetTenant(res.data[0].id)
                    }
                }
            } catch (err) {
                console.error("Error al cargar perfiles en DocumentUpload", err)
            }
        }
        loadProfiles()
    }, [])

    useEffect(() => {
        if (tenantId !== 'all') {
            setTargetTenant(tenantId)
        }
    }, [tenantId])
    
    const [selectedDocType, setSelectedDocType] = useState('all')

    // Carga documentos desde el endpoint de admin para obtener métricas de salud del índice.
    React.useEffect(() => {
        const fetchDocs = async () => {
            setLoading(true)
            try {
                const response = await api.get('admin/chatbot/documents')
                const rawDocs = Array.isArray(response.data) ? response.data : []
                let filtered = rawDocs

                // 1. Filtrar por Aplicativo / Tenant
                if (tenantId && tenantId !== 'all') {
                    filtered = filtered.filter(d =>
                        (d.category || '').toLowerCase() === tenantId.toLowerCase()
                    )
                }

                // 2. Filtrar por Tipo/Categoría de Documento (reglamentos, guias, tramites, etc.)
                if (selectedDocType && selectedDocType !== 'all') {
                    filtered = filtered.filter(d => {
                        const docMetaType = (d.doc_metadata?.doc_type || d.doc_metadata?.category || '').toLowerCase()
                        const titleLower = (d.title || '').toLowerCase()
                        if (selectedDocType === 'reglamentos') return docMetaType.includes('reglamento') || titleLower.includes('legislacion') || titleLower.includes('oficial')
                        if (selectedDocType === 'guias') return docMetaType.includes('guia') || titleLower.includes('guia') || titleLower.includes('diccionario')
                        if (selectedDocType === 'tramites') return docMetaType.includes('tramite') || titleLower.includes('procedimiento') || titleLower.includes('requisito') || titleLower.includes('acto')
                        if (selectedDocType === 'costos') return docMetaType.includes('costo') || titleLower.includes('costo') || titleLower.includes('derechos') || titleLower.includes('arancel')
                        return docMetaType === selectedDocType.toLowerCase()
                    })
                }

                // Mapear al formato del store preservando los metadatos de salud
                setDocuments(filtered.map(doc => ({
                    id:                  doc.id,
                    name:                doc.title || 'Documento RAG',
                    size:                doc.token_count || 1024,
                    category:            doc.category || 'general',
                    doc_type:            doc.doc_metadata?.doc_type || 'Procedimiento / Normativa',
                    uploadedAt:          doc.created_at || new Date().toISOString(),
                    status:              doc.status || 'indexed',
                    // Métricas de salud del índice vectorial
                    chunk_count:         doc.chunk_count || 0,
                    embedded_chunk_count: doc.embedded_chunk_count || 0,
                    health_pct:          doc.health_pct ?? 0,
                    processing_error:    doc.processing_error || null,
                })))
            } catch (err) {
                console.error("Error al cargar documentos desde admin:", err)
            } finally {
                setLoading(false)
            }
        }
        fetchDocs()
    }, [tenantId, selectedDocType])

    const categories = [
        { value: 'all', label: 'Todos los tipos (Mostrar Todo)' },
        { value: 'reglamentos', label: 'Reglamentos, Leyes & Decretos' },
        { value: 'guias', label: 'Guías & Manuales Operativos' },
        { value: 'tramites', label: 'Trámites, Requisitos & Procedimientos' },
        { value: 'costos', label: 'Costos, Aranceles & Tabuladores' },
        { value: 'faqs', label: 'Preguntas Frecuentes (FAQs)' },
        { value: 'formatos', label: 'Formatos, Plantillas & Solicitudes' },
        { value: 'instructivos', label: 'Instructivos & Circulares Tecnicas' },
        { value: 'otro', label: 'Otro / Documento General' },
    ]

    const handleDrag = (e) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true)
        } else if (e.type === "dragleave") {
            setDragActive(false)
        }
    }

    const [selectedFile, setSelectedFile]   = useState(null)

    const handleFileSelected = (file) => {
        if (!file) return
        const ext = file.name.split('.').pop().toLowerCase()
        const allowedExts = ['pdf', 'doc', 'docx', 'txt', 'md', 'png', 'jpg', 'jpeg']
        
        if (!allowedExts.includes(ext)) {
            setError(`Formato .${ext} no permitido. Formatos aceptados: PDF, Word (DOC/DOCX), TXT, Markdown (MD) e Imágenes (PNG, JPG).`)
            return
        }

        const maxSizeBytes = 50 * 1024 * 1024 // 50 MB
        if (file.size > maxSizeBytes) {
            setError(`El archivo supera el tamaño máximo permitido de 50 MB (Tamaño actual: ${(file.size / (1024 * 1024)).toFixed(1)} MB).`)
            return
        }

        clearError()
        setSelectedFile(file)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelected(e.dataTransfer.files[0])
        }
    }

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelected(e.target.files[0])
        }
    }

    const uploadFile = async () => {
        if (!selectedFile) return

        setLoading(true)
        clearError()

        try {
            const formData = new FormData()
            formData.append('file', selectedFile)
            formData.append('category', targetTenant || 'general')
            formData.append('tenant_id', targetTenant)
            formData.append('doc_type', category || 'reglamentos')

            await documentsAPI.upload(formData, targetTenant || 'general', (progressEvent) => {
                const percentCompleted = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                )
                setUploadProgress(percentCompleted)
            })

            addDocument({
                id: Date.now(),
                name: selectedFile.name,
                size: selectedFile.size,
                category: targetTenant || category,
                uploadedAt: new Date().toISOString(),
            })

            setSelectedFile(null)
            if (fileInputRef.current) fileInputRef.current.value = ''
            setUploadProgress(0)
        } catch (err) {
            setError('Error al cargar archivo: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    /**
     * handleReindex — re-ejecuta el proceso de chunking y embedding de un documento.
     * Llama a POST /admin/chatbot/documents/{id}/reindex y actualiza el estado local
     * del documento con los nuevos conteos devueltos por el backend.
     */
    const handleReindex = async (docId) => {
        setReindexStatus(prev => ({ ...prev, [docId]: 'loading' }))
        try {
            const res = await api.post(`admin/chatbot/documents/${docId}/reindex`)
            const { chunk_count, embedded_count, health_pct } = res.data
            // Actualizar el documento en el store con los datos frescos
            setDocuments(prev => prev.map(d => d.id === docId
                ? {
                    ...d,
                    chunk_count,
                    embedded_chunk_count: embedded_count,
                    health_pct,
                    processing_error: null,
                    status: health_pct >= 100 ? 'indexed' : 'partial'
                }
                : d
            ))
            setReindexStatus(prev => ({ ...prev, [docId]: 'done' }))
            // Limpiar la señal de éxito tras 3 segundos
            setTimeout(() => setReindexStatus(prev => ({ ...prev, [docId]: null })), 3000)
        } catch (err) {
            console.error('[Reindex] Error:', err)
            setReindexStatus(prev => ({ ...prev, [docId]: 'error' }))
            setTimeout(() => setReindexStatus(prev => ({ ...prev, [docId]: null })), 4000)
        }
    }

    return (
        <div className="space-y-6">
            
            {/* Proyecto / Tenant Selector obligatorio */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <Layers size={16} className="text-blue-500" />
                    <span>Proyecto / Tenant de Destino (Requerido)</span>
                </label>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                    Selecciona a qué aplicativo o tema del chatbot se vinculará este documento normativo:
                </p>
                <select
                    value={targetTenant}
                    onChange={(e) => setTargetTenant(e.target.value)}
                    className="w-full px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary cursor-pointer"
                >
                    {profiles.map(p => (
                        <option key={p.id} value={p.id}>
                            {p.name} ({p.id})
                        </option>
                    ))}
                    <option value="general">Chatbot General (general)</option>
                </select>
            </div>

            {/* Upload Area & File Selection Form */}
            <div className="space-y-4">
                <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                        dragActive
                            ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20'
                            : selectedFile
                                ? 'border-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20'
                                : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-850 hover:border-blue-500'
                    }`}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleChange}
                        accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg"
                        className="hidden"
                    />

                    {selectedFile ? (
                        <div className="flex items-center justify-between bg-white dark:bg-slate-900 p-4 rounded-xl border border-emerald-300 dark:border-emerald-800 shadow-sm max-w-md mx-auto">
                            <div className="flex items-center space-x-3 text-left">
                                <FileText className="text-emerald-500 shrink-0" size={24} />
                                <div className="min-w-0">
                                    <p className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate">{selectedFile.name}</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                                        {(selectedFile.size / 1024).toFixed(1)} KB
                                    </p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setSelectedFile(null)
                                    if (fileInputRef.current) fileInputRef.current.value = ''
                                }}
                                className="p-1 text-slate-400 hover:text-rose-500 transition"
                                title="Quitar archivo"
                            >
                                <X size={18} />
                            </button>
                        </div>
                    ) : (
                        <>
                            <Upload size={40} className="mx-auto mb-3 text-blue-500" />
                            <p className="text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                                Arrastra un archivo aquí o haz clic para seleccionar
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                                Se asociará al aplicativo: <strong className="text-blue-600 dark:text-blue-400">{profiles.find(p => p.id === targetTenant)?.name || targetTenant}</strong>
                            </p>
                            <div className="inline-flex flex-wrap items-center justify-center gap-2 mb-4">
                                <span className="px-2.5 py-0.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md text-[11px] font-mono">
                                    PDF, DOC, DOCX, TXT, MD, PNG, JPG
                                </span>
                                <span className="px-2.5 py-0.5 bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 rounded-md text-[11px] font-mono border border-amber-200 dark:border-amber-900">
                                    Máx. 50 MB
                                </span>
                            </div>
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-bold text-xs hover:bg-blue-700 transition shadow-sm"
                            >
                                Seleccionar Archivo
                            </button>
                        </>
                    )}
                </div>

                {/* Categoría y Botón de Acción de Carga */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-850 p-4 rounded-xl border border-slate-200 dark:border-slate-800 items-end">
                    <div>
                        <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                            Categoría / Tipo de Documento:
                        </label>
                        <select
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            className="w-full px-4 py-2.5 border border-slate-300 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer font-medium text-xs"
                        >
                            {categories.filter(c => c.value !== 'all').map(cat => (
                                <option key={cat.value} value={cat.value}>
                                    {cat.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        type="button"
                        onClick={uploadFile}
                        disabled={!selectedFile}
                        className="w-full py-2.5 px-5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs transition flex items-center justify-center space-x-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Upload size={16} />
                        <span>Cargar e Indexar en el RAG</span>
                    </button>
                </div>
            </div>

            {/* Selector de Filtro en Lista */}
            <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Filtrar Lista por Tipo de Documento:
                </label>
                <select
                    value={selectedDocType}
                    onChange={(e) => setSelectedDocType(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer font-medium text-xs"
                >
                    {categories.map(cat => (
                        <option key={cat.value} value={cat.value}>
                            {cat.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Documentos Indexados con Indicador de Salud del Índice */}
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Documentos Indexados en el RAG</h3>
                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full border border-blue-200 dark:border-blue-800">
                        {documents.length} documento(s) disponibles
                    </span>
                </div>
                {documents.length === 0 ? (
                    <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                        <p className="text-slate-500 dark:text-slate-400 text-sm">No hay documentos registrados o procesados aún.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {documents.map(doc => {
                            // Determinar color semántico de la barra según health_pct
                            const hp = doc.health_pct ?? 0
                            const healthColor = hp >= 95
                                ? 'var(--cs-success)'
                                : hp >= 50
                                    ? 'var(--cs-warning)'
                                    : 'var(--cs-danger)'
                            const healthBg = hp >= 95
                                ? 'var(--cs-success-bg)'
                                : hp >= 50
                                    ? 'var(--cs-warning-bg)'
                                    : 'var(--cs-danger-bg)'
                            const isReindexing = reindexStatus[doc.id] === 'loading'
                            const reindexDone  = reindexStatus[doc.id] === 'done'
                            const reindexError = reindexStatus[doc.id] === 'error'

                            return (
                                <div
                                    key={doc.id}
                                    className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 shadow-sm hover:shadow-md transition-all"
                                >
                                    {/* Fila principal: icono + nombre + fragmentos + chip */}
                                    <div className="flex items-center justify-between gap-3">
                                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                                            <div className="p-2.5 bg-blue-50 dark:bg-slate-800 rounded-lg text-blue-600 dark:text-blue-400 shrink-0">
                                                <FileText size={20} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-semibold text-slate-900 dark:text-slate-100 text-sm truncate">{doc.name}</p>
                                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                                    Categoría: <span className="font-medium text-slate-700 dark:text-slate-300">{doc.category}</span>
                                                    {doc.chunk_count > 0 && (
                                                        <> • <span className="font-mono">
                                                            {doc.embedded_chunk_count}/{doc.chunk_count} fragmentos
                                                        </span></>
                                                    )}
                                                </p>
                                            </div>
                                        </div>
                                        {/* Chip de estado con tokens semánticos */}
                                        <span
                                            className="cs-chip shrink-0"
                                            style={{ backgroundColor: healthBg, color: healthColor, borderColor: `color-mix(in srgb, ${healthColor} 35%, transparent)` }}
                                        >
                                            {hp >= 95
                                                ? <CheckCircle2 size={10} />
                                                : <AlertCircle size={10} />}
                                            {hp >= 95 ? 'Indexado' : hp > 0 ? `Parcial ${hp}%` : 'Sin embedding'}
                                        </span>
                                    </div>

                                    {/* Barra de salud del índice — Renderizada para todos los documentos */}
                                    <div className="mt-3">
                                        <div className="flex justify-between text-[10px] font-mono mb-1"
                                             style={{ color: healthColor }}>
                                            <span>Salud del índice vectorial</span>
                                            <span>{hp}% {doc.chunk_count > 0 ? `(${doc.embedded_chunk_count}/${doc.chunk_count} chunks)` : '(0 chunks)'}</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                            <div
                                                className="h-full rounded-full transition-all duration-500"
                                                style={{ width: `${Math.max(hp, doc.chunk_count === 0 ? 0 : 5)}%`, backgroundColor: healthColor }}
                                            />
                                        </div>
                                    </div>

                                    {/* Mensaje de error colapsable + botón Reintentar */}
                                    {(doc.processing_error || hp < 100 || doc.chunk_count === 0) && (
                                        <div className="mt-2.5 flex items-center justify-between gap-3">
                                            {doc.processing_error ? (
                                                <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate flex-1">
                                                    <AlertCircle size={10} className="inline mr-1" style={{ color: 'var(--cs-danger)' }} />
                                                    {doc.processing_error}
                                                </p>
                                            ) : <span />}
                                            {/* Botón Reintentar — siempre disponible si la salud es menor al 100% */}
                                            {hp < 100 && (
                                                <button
                                                    onClick={() => handleReindex(doc.id)}
                                                    disabled={isReindexing}
                                                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition shrink-0"
                                                    style={{
                                                        backgroundColor: reindexDone ? 'var(--cs-success-bg)' : reindexError ? 'var(--cs-danger-bg)' : 'var(--cs-info-bg)',
                                                        color: reindexDone ? 'var(--cs-success)' : reindexError ? 'var(--cs-danger)' : 'var(--cs-info)',
                                                    }}
                                                    title="Re-ejecutar el proceso de chunking y embedding"
                                                >
                                                    {isReindexing
                                                        ? <><RefreshCw size={10} className="animate-spin" />Reindexando...</>
                                                        : reindexDone
                                                            ? <><CheckCircle2 size={10} />Completado</>
                                                            : reindexError
                                                                ? <><AlertCircle size={10} />Error</>   
                                                                : <><RefreshCw size={10} />Reintentar</>}
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}
