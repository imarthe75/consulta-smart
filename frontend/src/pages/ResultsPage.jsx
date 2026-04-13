import React from 'react'
import SearchResults from '../components/SearchResults'

export default function ResultsPage() {
    return (
        <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">Búsqueda de Documentos</h1>
                <SearchResults />
            </div>
        </div>
    )
}
