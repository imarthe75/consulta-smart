import React from 'react'
import DocumentUpload from '../components/DocumentUpload'

export default function DocumentsPage() {
    return (
        <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">Gestión de Documentos</h1>
                <DocumentUpload />
            </div>
        </div>
    )
}
