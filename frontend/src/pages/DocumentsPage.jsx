import React, { useState, useEffect } from 'react'
import DocumentUpload from '../components/DocumentUpload'
import ModuleBanner from '../components/ModuleBanner'
import { FileText, Shield, Layers, Database, Filter } from 'lucide-react'
import api from '../services/api'

export default function DocumentsPage() {
    const [selectedApp, setSelectedApp] = useState('all')
    const [profiles, setProfiles] = useState([])

    useEffect(() => {
        const fetchProfiles = async () => {
            try {
                const res = await api.get('admin/chatbot/profiles')
                if (Array.isArray(res.data)) {
                    setProfiles(res.data)
                }
            } catch (err) {
                console.error("Error al cargar perfiles en DocumentsPage:", err)
            }
        }
        fetchProfiles()
    }, [])

    return (
        <div className="w-full min-h-screen p-6 md:p-8 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
            <div className="max-w-5xl mx-auto space-y-6">
                <ModuleBanner
                    badgeIcon={Layers}
                    badgeLabel="Base de Conocimiento RAG Multitenant"
                    title="Documentos de Soporte RAG"
                    subtitle="Administra e indexa la documentación oficial de soporte para alimentar las respuestas generativas de cada aplicativo/tenant en tiempo real."
                    decorIcon={Database}
                    actions={
                        <div className="flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-xl border border-white/10">
                            <Shield className="text-emerald-400" size={20} />
                            <div>
                                <p className="text-xs font-bold text-white">Aislamiento Vectorial</p>
                                <p className="text-[11px] text-slate-300">Filtro automático por Tenant</p>
                            </div>
                        </div>
                    }
                />

                {/* Filtro por Aplicativo */}
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center space-x-2 text-slate-700 dark:text-slate-300 font-semibold text-sm">
                        <Filter size={18} className="text-blue-500" />
                        <span>Filtrar por Aplicativo / Tema (Tenant):</span>
                    </div>
                    <select
                        value={selectedApp}
                        onChange={(e) => setSelectedApp(e.target.value)}
                        className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer"
                    >
                        <option value="all">Todos los Aplicativos (Global)</option>
                        {profiles.map(p => (
                            <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
                        ))}
                    </select>
                </div>

                {/* Componente de Carga y Lista */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <DocumentUpload tenantId={selectedApp} />
                </div>
            </div>
        </div>
    )
}

