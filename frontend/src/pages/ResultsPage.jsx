import React from 'react'
import SearchResults from '../components/SearchResults'
import ModuleBanner from '../components/ModuleBanner'
import { Search } from 'lucide-react'

export default function ResultsPage() {
    return (
        <div className="flex-1 p-6 md:p-8 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
            <div className="max-w-4xl mx-auto space-y-6">
                <ModuleBanner
                    badgeIcon={Search}
                    badgeLabel="Búsqueda Semántica RAG"
                    title="Búsqueda de Documentos"
                    subtitle="Encuentra fragmentos indexados en la base de conocimiento por similitud semántica, no solo por coincidencia exacta de palabras."
                    decorIcon={Search}
                />
                <SearchResults />
            </div>
        </div>
    )
}
