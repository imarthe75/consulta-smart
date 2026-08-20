import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useDocumentStore } from '../stores/documentStore'
import api from '../services/api'
import { Upload, X, AlertCircle, FileText, Layers, RefreshCw, CheckCircle2, Trash2 } from 'lucide-react'

export default function DocumentUpload({ tenantId = 'all' }) {
    const [dragActive, setDragActive]       = useState(false)
    const [targetTenant, setTargetTenant]   = useState(tenantId !== 'all' ? tenantId : '')
    const [category, setCategory]           = useState('reglamentos')
    const [profiles, setProfiles]           = useState([])
    // Estado de reindexado: { [docId]: 'loading' | 'done' | 'error' }
    const [reindexStatus, setReindexStatus] = useState({})
    const fileInputRef = useRef(null)

    const { documents, setDocuments, loading, setLoading, setError, setUploadProgress, clearError, uploadProgress } = useDocumentStore()

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
    // Extraída de useEffect para poder reusarla también después de subir un archivo
    // (antes, tras subir, se agregaba un documento LOCAL falso con id: Date.now() en
    // vez de recargar la lista real -- eso hacía que la salud del índice se mostrara
    // en 0% aunque el backend ya lo hubiera indexado de verdad, y que "Reintentar"
    // fallara con 404 porque Date.now() nunca es un id real de la BD. Incidente real
    // 2026-08-14: esto llevó a que el usuario, pensando que la subida había fallado,
    // volviera a subir el mismo archivo, duplicándolo de verdad en la BD).
    const fetchDocs = useCallback(async () => {
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
    }, [tenantId, selectedDocType, setDocuments, setLoading])

    useEffect(() => {
        fetchDocs()
    }, [fetchDocs])

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

    const [selectedFiles, setSelectedFiles] = useState([])
    const [uploadBatchResult, setUploadBatchResult] = useState(null)

    // Tamaño total sumado del lote en Bytes (Límite: 500 MB = 500 * 1024 * 1024)
    const MAX_BATCH_SIZE_BYTES = 500 * 1024 * 1024
    const totalBatchSizeBytes = selectedFiles.reduce((acc, f) => acc + (f.size || 0), 0)
    const isBatchSizeExceeded = totalBatchSizeBytes > MAX_BATCH_SIZE_BYTES

    const handleFilesSelected = (filesList) => {
        const filesArray = Array.from(filesList)
        const validFiles = []
        let hasError = false

        for (const file of filesArray) {
            const ext = file.name.split('.').pop().toLowerCase()
            if (!['pdf', 'md', 'txt'].includes(ext)) {
                setError(`Formato no soportado en "${file.name}". Solo se admiten PDF, MD y TXT.`)
                hasError = true
                break
            }
            if (file.size > 50 * 1024 * 1024) {
                setError(`El archivo "${file.name}" supera los 50 MB.`)
                hasError = true
                break
            }
            validFiles.push(file)
        }

        if (!hasError && validFiles.length > 0) {
            clearError()
            setUploadBatchResult(null)
            setSelectedFiles(prev => {
                // Evitar duplicados exactos en la seleccion local por nombre y tamaño
                const existingKeys = new Set(prev.map(f => `${f.name}_${f.size}`))
                const newUnique = validFiles.filter(f => !existingKeys.has(`${f.name}_${f.size}`))
                return [...prev, ...newUnique]
            })
        }
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFilesSelected(e.dataTransfer.files)
        }
    }

    const handleChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFilesSelected(e.target.files)
        }
    }

    const removeFile = (index) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index))
    }

    const uploadFiles = async () => {
        if (selectedFiles.length === 0) return

        if (!targetTenant || targetTenant === 'general' || targetTenant === 'all') {
            setError('Debes seleccionar un Aplicativo / Tema (Tenant) específico en el filtro superior antes de realizar la carga.')
            return
        }

        setLoading(true)
        clearError()
        setUploadBatchResult(null)

        try {
            const formData = new FormData()
            selectedFiles.forEach(file => {
                formData.append('files', file)
            })
            formData.append('category', targetTenant || 'general')
            formData.append('doc_type', category || 'reglamentos')

            const response = await api.post('admin/chatbot/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    )
                    setUploadProgress(percentCompleted)
                },
            })

            await fetchDocs()

            setUploadBatchResult(response.data)
            setSelectedFiles([])
            if (fileInputRef.current) fileInputRef.current.value = ''
            setUploadProgress(0)
        } catch (err) {
            setError('Error al cargar archivos: ' + (err.response?.data?.detail || err.message))
        } finally {
            setLoading(false)
        }
    }

    /**
     * handleDeleteDocument — borra un documento y sus vectores del RAG (con confirmación).
     */
    const handleDeleteDocument = async (docId, docName) => {
        if (!window.confirm(`¿Eliminar "${docName}" y todos sus fragmentos vectorizados del RAG? Esta acción no se puede deshacer.`)) return
        try {
            await api.delete(`admin/chatbot/documents/${docId}`)
            setDocuments(prev => prev.filter(d => d.id !== docId))
        } catch (err) {
            console.error('[Delete] Error:', err)
            setError('No se pudo eliminar el documento.')
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

            {/* Mensaje Informativo de Tenant seleccionado */}
            {(!targetTenant || targetTenant === 'general' || targetTenant === 'all') && (
                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 rounded-xl border border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs font-semibold flex items-center gap-2">
                    <AlertCircle size={16} className="shrink-0 text-amber-600 dark:text-amber-400" />
                    <span>
                        Para cargar e indexar documentos debes seleccionar un Aplicativo / Tema (Tenant) específico en el filtro superior. No se permite carga en el tema genérico o global.
                    </span>
                </div>
            )}

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
                            : selectedFiles.length > 0
                                ? 'border-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20'
                                : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-850 hover:border-blue-500'
                    }`}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleChange}
                        multiple
                        accept=".pdf,.txt,.md"
                        className="hidden"
                    />

                    {selectedFiles.length > 0 ? (
                        <div className="space-y-3" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <p className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                                        Archivos Seleccionados ({selectedFiles.length})
                                    </p>
                                    <span className={`text-[11px] font-mono px-2 py-0.5 rounded-md font-bold ${
                                        isBatchSizeExceeded
                                            ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                                            : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                                    }`}>
                                        Peso Total: {(totalBatchSizeBytes / (1024 * 1024)).toFixed(1)} MB / 500 MB
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setSelectedFiles([])}
                                    className="text-xs text-rose-500 hover:underline font-semibold"
                                >
                                    Limpiar todos
                                </button>
                            </div>

                            {isBatchSizeExceeded && (
                                <div className="p-3 bg-rose-50 dark:bg-rose-950/50 border border-rose-300 dark:border-rose-800 rounded-xl text-rose-800 dark:text-rose-300 text-xs font-semibold flex items-center gap-2">
                                    <AlertCircle size={16} className="shrink-0 text-rose-600 dark:text-rose-400" />
                                    <span>
                                        ¡El lote excede el tamaño máximo permitido! El peso total es de <strong>{(totalBatchSizeBytes / (1024 * 1024)).toFixed(1)} MB</strong> (Límite: 500 MB). Remueve algunos archivos para habilitar el botón de carga.
                                    </span>
                                </div>
                            )}

                            <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                                {selectedFiles.map((file, idx) => (
                                    <div key={`${file.name}_${idx}`} className="flex items-center justify-between bg-white dark:bg-slate-900 p-3 rounded-xl border border-emerald-300 dark:border-emerald-800 shadow-sm">
                                        <div className="flex items-center space-x-3 text-left min-w-0">
                                            <FileText className="text-emerald-500 shrink-0" size={20} />
                                            <div className="min-w-0">
                                                <p className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate">{file.name}</p>
                                                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                                                    {(file.size / 1024).toFixed(1)} KB
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => removeFile(idx)}
                                            className="p-1 text-slate-400 hover:text-rose-500 transition"
                                            title="Quitar archivo"
                                        >
                                            <X size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="text-xs text-blue-600 dark:text-blue-400 font-bold hover:underline"
                            >
                                + Agregar más archivos
                            </button>
                        </div>
                    ) : (
                        <>
                            <Upload size={40} className="mx-auto mb-3 text-blue-500" />
                            <p className="text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                                Arrastra tus archivos aquí o haz clic para seleccionar (Múltiples permitidos)
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                                Se asociarán al aplicativo: <strong className="text-blue-600 dark:text-blue-400">{profiles.find(p => p.id === targetTenant)?.name || targetTenant}</strong>
                            </p>
                            <div className="inline-flex flex-wrap items-center justify-center gap-2 mb-4">
                                <span className="px-2.5 py-0.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md text-[11px] font-mono font-semibold">
                                    Formatos: PDF, TXT, MD
                                </span>
                                <span className="px-2.5 py-0.5 bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 rounded-md text-[11px] font-mono border border-emerald-200 dark:border-emerald-900 font-bold">
                                    Límite Máx: 500 MB por lote (50 MB c/u)
                                </span>
                            </div>
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-bold text-xs hover:bg-blue-700 transition shadow-sm"
                            >
                                Seleccionar Archivos
                            </button>
                        </>
                    )}
                </div>

                {uploadBatchResult && (
                    <div className="p-4 bg-slate-50 dark:bg-slate-800/90 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3 shadow-sm">
                        <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                                <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />
                                <div>
                                    <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
                                        Resumen de Ingesta al RAG ({uploadBatchResult.total_files || uploadBatchResult.results?.length} archivos en total)
                                    </p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">
                                        {uploadBatchResult.message}
                                    </p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setUploadBatchResult(null)}
                                className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 text-xs font-bold rounded-lg transition shrink-0"
                            >
                                Limpiar Resumen
                            </button>
                        </div>

                        {/* Chips de desglose de métricas */}
                        <div className="flex flex-wrap items-center gap-2 pt-1">
                            <span className="px-2.5 py-1 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 font-bold rounded-lg text-xs border border-emerald-300 dark:border-emerald-800">
                                Total Cargados: {uploadBatchResult.processed_count ?? 0}
                            </span>
                            <span className="px-2.5 py-1 bg-blue-100 dark:bg-blue-950/50 text-blue-800 dark:text-blue-300 font-medium rounded-lg text-xs border border-blue-300 dark:border-blue-800">
                                Nuevos: {uploadBatchResult.new_files_count ?? 0}
                            </span>
                            <span className="px-2.5 py-1 bg-indigo-100 dark:bg-indigo-950/50 text-indigo-800 dark:text-indigo-300 font-medium rounded-lg text-xs border border-indigo-300 dark:border-indigo-800">
                                Actualizados / Versión: {uploadBatchResult.duplicate_renamed_count ?? 0}
                            </span>
                            <span className="px-2.5 py-1 bg-amber-100 dark:bg-amber-950/50 text-amber-800 dark:text-amber-300 font-bold rounded-lg text-xs border border-amber-300 dark:border-amber-800">
                                Omitidos (Idénticos): {uploadBatchResult.duplicate_omitted_count ?? 0}
                            </span>
                            {uploadBatchResult.failed_count > 0 && (
                                <span className="px-2.5 py-1 bg-rose-100 dark:bg-rose-950/50 text-rose-800 dark:text-rose-300 font-bold rounded-lg text-xs border border-rose-300 dark:border-rose-800">
                                    Fallidos: {uploadBatchResult.failed_count - (uploadBatchResult.duplicate_omitted_count || 0)}
                                </span>
                            )}
                        </div>

                        {uploadBatchResult.results && (
                            <div className="space-y-1 text-xs pt-2 border-t border-slate-200 dark:border-slate-700 max-h-40 overflow-y-auto pr-1">
                                {uploadBatchResult.results.map((res, i) => (
                                    <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-100 dark:border-slate-800 last:border-0">
                                        <span className="font-mono text-slate-700 dark:text-slate-300 truncate max-w-xs">{res.filename}</span>
                                        <span className={`font-semibold px-2 py-0.5 rounded text-[10px] ${
                                            res.status === 'success' ? 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300' :
                                            res.status === 'duplicate_renamed' ? 'bg-indigo-100 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300' :
                                            res.status === 'duplicate_omitted' || res.status === 'duplicate' ? 'bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300' :
                                            'bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300'
                                        }`}>
                                            {res.status === 'success' ? `Nuevo Indexado (${res.document?.chunk_count} chunks)` :
                                             res.status === 'duplicate_renamed' ? `Cargado como ${res.document?.title}` :
                                             res.status === 'duplicate_omitted' || res.status === 'duplicate' ? 'Omitido (Idéntico)' : 'Error'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Progress Bar during Upload */}
                {loading && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-xl border border-blue-200 dark:border-blue-800 space-y-2">
                        <div className="flex items-center justify-between text-xs font-bold text-blue-700 dark:text-blue-300">
                            <span className="flex items-center gap-2">
                                <RefreshCw size={14} className="animate-spin text-blue-500" />
                                <span>Procesando e Indexando Documentos en el RAG...</span>
                            </span>
                            <span>{uploadProgress > 0 ? `${uploadProgress}%` : 'Extrayendo texto y generando vectores...'}</span>
                        </div>
                        <div className="w-full h-2 bg-blue-200 dark:bg-blue-900 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-blue-600 rounded-full transition-all duration-300"
                                style={{ width: `${uploadProgress > 0 ? uploadProgress : 100}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Categoría y Botón de Acción de Carga */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-850 p-4 rounded-xl border border-slate-200 dark:border-slate-800 items-end">
                    <div>
                        <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                            Categoría / Tipo de Documento:
                        </label>
                        <select
                            value={category}
                            disabled={loading}
                            onChange={(e) => setCategory(e.target.value)}
                            className="w-full px-4 py-2.5 border border-slate-300 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer font-medium text-xs disabled:opacity-50"
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
                        onClick={uploadFiles}
                        disabled={selectedFiles.length === 0 || loading || !targetTenant || targetTenant === 'general' || targetTenant === 'all' || isBatchSizeExceeded}
                        className={`w-full py-2.5 px-5 font-bold rounded-xl text-xs transition flex items-center justify-center space-x-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed ${
                            isBatchSizeExceeded
                                ? 'bg-rose-600 text-white'
                                : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                        }`}
                    >
                        {loading ? (
                            <>
                                <RefreshCw size={16} className="animate-spin text-white" />
                                <span>Cargando e Indexando en RAG...</span>
                            </>
                        ) : isBatchSizeExceeded ? (
                            <>
                                <AlertCircle size={16} />
                                <span>Tamaño Excedido (&gt;500 MB)</span>
                            </>
                        ) : (
                            <>
                                <Upload size={16} />
                                <span>Cargar e Indexar en el RAG</span>
                            </>
                        )}
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
                                        <button
                                            onClick={() => handleDeleteDocument(doc.id, doc.name)}
                                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition shrink-0"
                                            title="Eliminar documento y sus vectores del RAG"
                                        >
                                            <Trash2 size={14} />
                                        </button>
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
