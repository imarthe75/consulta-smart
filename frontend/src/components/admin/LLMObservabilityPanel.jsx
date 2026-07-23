import React, { useState, useEffect } from 'react'
import api from '../../services/api'
import { Activity, Cpu, Server, CheckCircle2, ThumbsUp, ThumbsDown, RefreshCw, Zap, ShieldCheck, AlertTriangle } from 'lucide-react'

/**
 * LLMObservabilityPanel — Componente de observabilidad operacional de IA.
 * Muestra el estado del enrutador de modelos (LLM Router), métricas de satisfacción del usuario,
 * hit/miss rate de la caché semántica híbrida y estado de fallbacks activos.
 */
export default function LLMObservabilityPanel() {
    const [metrics, setMetrics] = useState(null)
    const [loading, setLoading] = useState(true)

    /**
     * Consulta las métricas de observabilidad expuestas en GET /api/v1/admin/stats/llm-router
     */
    const fetchStats = async () => {
        setLoading(true)
        try {
            const res = await api.get('admin/stats/llm-router')
            if (res.data && res.data.metrics) {
                setMetrics(res.data.metrics)
            }
        } catch (err) {
            console.error("Error al cargar métricas de observabilidad:", err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchStats()
    }, [])

    if (loading) {
        return (
            <div className="p-8 flex items-center justify-center space-x-3 text-slate-400">
                <RefreshCw size={20} className="animate-spin text-blue-500" />
                <span>Cargando observabilidad del enrutador LLM...</span>
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-in fade-in duration-200">
            {/* Encabezado del panel */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                        <Activity className="text-blue-500" size={20} />
                        Observabilidad & Salud del Enrutador LLM
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Monitoreo en tiempo real del estado de proveedores, tasa de satisfacción y aceleración por caché semántica.
                    </p>
                </div>
                <button
                    onClick={fetchStats}
                    className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl transition"
                    title="Actualizar métricas"
                >
                    <RefreshCw size={16} />
                </button>
            </div>

            {/* Alerta crítica: sin ningún proveedor de IA configurado, el chat no genera
                respuestas reales — responde con un texto de respaldo genérico que ignora
                la pregunta y el contexto RAG recuperado. Hallazgo real (2026-07-22): esto
                ocurría en silencio, sin ningún indicador visible para el administrador. */}
            {metrics?.no_llm_provider_configured && (
                <div
                    className="p-4 rounded-xl border flex items-start gap-3"
                    style={{ backgroundColor: 'var(--cs-danger-bg)', borderColor: 'var(--cs-danger)', color: 'var(--cs-danger)' }}
                >
                    <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                    <div className="text-xs">
                        <p className="font-bold mb-1">Ningún proveedor de IA está configurado.</p>
                        <p>
                            El chat sigue recuperando documentos reales del RAG, pero las respuestas que se
                            muestran al usuario son un texto genérico de respaldo que no usa el contexto ni
                            responde a la pregunta real. Verifica las claves de API (Groq, Gemini, Vertex AI o
                            NVIDIA NIM) o la conexión a Vault en la configuración del backend.
                        </p>
                    </div>
                </div>
            )}

            {/* Metricas de Resumen */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">
                        <span>Consultas Procesadas</span>
                        <Zap size={16} className="text-amber-500" />
                    </div>
                    <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 font-mono">
                        {metrics?.total_queries_processed || 0}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">En el historial activo</p>
                </div>

                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">
                        <span>Satisfacción Usuario</span>
                        <ThumbsUp size={16} className="text-emerald-500" />
                    </div>
                    <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 font-mono">
                        {metrics?.feedback?.satisfaction_rate_pct || 100}%
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                        <span className="flex items-center gap-1 text-emerald-600"><ThumbsUp size={11} /> {metrics?.feedback?.positive || 0}</span>
                        <span className="flex items-center gap-1 text-rose-500"><ThumbsDown size={11} /> {metrics?.feedback?.negative || 0}</span>
                    </div>
                </div>

                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">
                        <span>Perfiles / Tenants</span>
                        <ShieldCheck size={16} className="text-blue-500" />
                    </div>
                    <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 font-mono">
                        {metrics?.total_profiles_active || 0}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">Configurados en BD</p>
                </div>

                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">
                        <span>Caché Híbrida</span>
                        <Server size={16} className="text-purple-500" />
                    </div>
                    <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 size={14} /> {metrics?.cache_layer?.status?.toUpperCase()}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1 font-mono">Umbral: {metrics?.cache_layer?.similarity_threshold}</p>
                </div>
            </div>

            {/* Estado de Proveedores LLM */}
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                    <Cpu size={16} className="text-blue-500" />
                    <span>Matriz de Proveedores LLM & Fallback Strategy</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {metrics?.active_llm_providers?.map((provider, idx) => (
                        <div key={idx} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className={`w-2.5 h-2.5 rounded-full ${
                                    provider.status === 'active' ? 'bg-emerald-500' : provider.status === 'fallback_standby' ? 'bg-amber-500' : 'bg-slate-300 dark:bg-slate-700'
                                }`} />
                                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">{provider.name}</span>
                            </div>
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                                provider.status === 'active' 
                                    ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border-emerald-200' 
                                    : provider.status === 'fallback_standby'
                                        ? 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border-amber-200'
                                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500 border-slate-200'
                            }`}>
                                {provider.status}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
