import React, { useState, useEffect } from 'react'
import { searchAPI } from '../services/api'
import { Search, Target, Loader } from 'lucide-react'

export default function SearchResults() {
    const [searchQuery, setSearchQuery] = useState('')
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!searchQuery.trim()) return

        setLoading(true)
        setError(null)

        try {
            const response = await searchAPI.search(searchQuery)
            setResults(response.data.data || [])
        } catch (err) {
            setError('Error en la búsqueda: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            {/* Search Form */}
            <form onSubmit={handleSearch} className="flex space-x-2">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-3 text-gray-400" size={20} />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Busca en documentos..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
                <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                    {loading ? <Loader className="animate-spin" size={20} /> : 'Buscar'}
                </button>
            </form>

            {/* Error */}
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
                    {error}
                </div>
            )}

            {/* Results */}
            {results.length === 0 && !loading && (
                <div className="text-center py-12">
                    <Target size={48} className="mx-auto mb-4 text-gray-300" />
                    <p className="text-gray-500">
                        {searchQuery ? 'No se encontraron resultados' : 'Realiza una búsqueda para ver resultados'}
                    </p>
                </div>
            )}

            <div className="space-y-4">
                {results.map((result, idx) => (
                    <div
                        key={idx}
                        className="p-4 border border-gray-200 rounded-lg bg-white hover:shadow-lg transition-shadow"
                    >
                        <h3 className="font-semibold text-gray-900 mb-2">{result.title}</h3>
                        <p className="text-gray-600 mb-3">{result.snippet || result.content}</p>
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                                {result.source || result.document_name}
                            </span>
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                Relevancia: {(result.score * 100).toFixed(0)}%
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
