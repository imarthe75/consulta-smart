import React, { useState, useRef } from 'react'
import { useDocumentStore } from '../stores/documentStore'
import { documentsAPI } from '../services/api'
import { Upload, X, AlertCircle } from 'lucide-react'

export default function DocumentUpload() {
    const [dragActive, setDragActive] = useState(false)
    const [category, setCategory] = useState('reglamentos')
    const fileInputRef = useRef(null)

    const { documents, addDocument, setDocuments, setLoading, setError, setUploadProgress, clearError } = useDocumentStore()
    
    // Fetch documents on mount
    React.useEffect(() => {
        const fetchDocs = async () => {
            setLoading(true)
            try {
                const response = await documentsAPI.list(1, 100)
                if (response.data?.data?.documents) {
                    setDocuments(response.data.data.documents.map(doc => ({
                        id: doc.id,
                        name: doc.title,
                        size: doc.size || 0,
                        category: doc.category,
                        uploadedAt: doc.created_at,
                        status: doc.status
                    })))
                }
            } catch (err) {
                console.error("Error al cargar documentos", err)
            } finally {
                setLoading(false)
            }
        }
        fetchDocs()
    }, [])

    const categories = [
        { value: 'reglamentos', label: 'Reglamentos' },
        { value: 'guias', label: 'Guías' },
        { value: 'tramites', label: 'Trámites' },
        { value: 'costos', label: 'Costos' },
        { value: 'otro', label: 'Otro' },
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

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        const files = e.dataTransfer.files
        if (files && files[0]) {
            uploadFile(files[0])
        }
    }

    const handleChange = (e) => {
        const files = e.target.files
        if (files && files[0]) {
            uploadFile(files[0])
        }
    }

    const uploadFile = async (file) => {
        if (!file.type.includes('pdf') && !file.type.includes('word') && !file.type.includes('image')) {
            setError('Formato de archivo no permitido. Solo PDF, Word e imágenes.')
            return
        }

        setLoading(true)
        clearError()

        try {
            const formData = new FormData()
            formData.append('file', file)
            formData.append('category', category)

            await documentsAPI.upload(formData, category, (progressEvent) => {
                const percentCompleted = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                )
                setUploadProgress(percentCompleted)
            })

            addDocument({
                id: Date.now(),
                name: file.name,
                size: file.size,
                category,
                uploadedAt: new Date().toISOString(),
            })

            setUploadProgress(0)
        } catch (err) {
            setError('Error al cargar archivo: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            {/* Upload Area */}
            <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${dragActive
                        ? 'border-primary bg-blue-50'
                        : 'border-gray-300 bg-gray-50 hover:border-primary'
                    }`}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleChange}
                    accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
                    className="hidden"
                    multiple
                />

                <Upload size={40} className="mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-semibold text-gray-700 mb-2">
                    Arrastra un archivo aquí o haz clic para seleccionar
                </p>
                <p className="text-sm text-gray-500 mb-4">
                    Formatos soportados: PDF, Word, Imágenes
                </p>
                <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    Seleccionar archivo
                </button>
            </div>

            {/* Category Selector */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categoría del documento
                </label>
                <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    {categories.map(cat => (
                        <option key={cat.value} value={cat.value}>
                            {cat.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Uploaded Documents */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Documentos cargados</h3>
                {documents.length === 0 ? (
                    <p className="text-gray-500">No hay documentos cargados aún.</p>
                ) : (
                    <div className="space-y-2">
                        {documents.map(doc => (
                            <div
                                key={doc.id}
                                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-white"
                            >
                                <div className="flex-1">
                                    <p className="font-medium text-gray-900">{doc.name}</p>
                                    <p className="text-sm text-gray-500">
                                        {doc.category} • {(doc.size / 1024).toFixed(2)} KB
                                    </p>
                                </div>
                                <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                    Procesando...
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
