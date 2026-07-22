import React, { useState, useEffect } from 'react'
import api from '../../services/api'
import { Play, Plus, Trash2, CheckCircle2, XCircle, RefreshCw, Layers, AlertCircle, FileCheck } from 'lucide-react'

/**
 * PromptRegressionPanel — Panel interactivo para baterías de prueba de regresión de Prompts.
 * Permite definir preguntas de referencia y evaluar automáticamente si las respuestas
 * generadas conservan las palabras clave obligatorias tras modificaciones al System Prompt o Guardrails.
 * 
 * @param {string} profileId - Identificador del perfil/tenant activo.
 */
export default function PromptRegressionPanel({ profileId = 'general' }) {
    // Casos de prueba cargados desde la BD para el perfil activo
    const [testCases, setTestCases] = useState([])
    // Estado de carga inicial
    const [loading, setLoading] = useState(true)
    // Estado de ejecución de la suite de regresión
    const [running, setRunning] = useState(false)
    // Resultados de la última corrida de regresión
    const [results, setResults] = useState(null)
    
    // Inputs para nuevos casos de prueba
    const [newQuery, setNewQuery] = useState('')
    const [newKeywords, setNewKeywords] = useState('')
    const [newDesc, setNewDesc] = useState('')

    /**
     * Carga la lista de casos de prueba asignados al perfil actual.
     */
    const fetchTestCases = async () => {
        setLoading(true)
        try {
            const res = await api.get(`admin/chatbot/profiles/${profileId}/test-cases`)
            if (Array.isArray(res.data)) {
                setTestCases(res.data)
            }
        } catch (err) {
            console.error("Error al cargar casos de prueba de regresión:", err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchTestCases()
        setResults(null)
    }, [profileId])

    /**
     * Agrega un nuevo caso de prueba a la BD para el perfil activo.
     */
    const handleAddTestCase = async (e) => {
        e.preventDefault()
        if (!newQuery.trim()) return
        try {
            const kwArray = newKeywords.split(',').map(k => k.trim()).filter(Boolean)
            await api.post(`admin/chatbot/profiles/${profileId}/test-cases`, {
                query: newQuery.trim(),
                expected_keywords: kwArray,
                description: newDesc.trim() || null
            })
            setNewQuery('')
            setNewKeywords('')
            setNewDesc('')
            fetchTestCases()
        } catch (err) {
            console.error("Error al agregar caso de prueba:", err)
        }
    }

    /**
     * Elimina un caso de prueba por su ID.
     */
    const handleDeleteTestCase = async (caseId) => {
        if (!window.confirm('¿Eliminar este caso de prueba de regresión?')) return
        try {
            await api.delete(`admin/chatbot/test-cases/${caseId}`)
            setTestCases(prev => prev.filter(c => c.id !== caseId))
        } catch (err) {
            console.error("Error al eliminar caso de prueba:", err)
        }
    }

    /**
     * Dispara la ejecución paralela/secuencial de la batería de regresión en el backend.
     */
    const handleRunRegression = async () => {
        if (testCases.length === 0) return
        setRunning(true)
        setResults(null)
        try {
            const res = await api.post(`admin/chatbot/profiles/${profileId}/run-regression`)
            if (res.data) {
                setResults(res.data)
            }
        } catch (err) {
            console.error("Error ejecutando regresión:", err)
        } finally {
            setRunning(false)
        }
    }

    return (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6 animate-in fade-in duration-200">
            {/* Encabezado */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                        <FileCheck className="text-purple-600 dark:text-purple-400" size={20} />
                        Batería de Regresión de System Prompts ({profileId})
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Guarda casos de prueba de referencia para validar que los cambios en Prompts o Guardrails no degraden la calidad.
                    </p>
                </div>
                <button
                    onClick={handleRunRegression}
                    disabled={running || testCases.length === 0}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-2.5 rounded-xl font-bold text-xs transition flex items-center gap-2 disabled:opacity-50 shrink-0"
                >
                    {running ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                    <span>Ejecutar Suite ({testCases.length})</span>
                </button>
            </div>

            {/* Formulario para agregar caso de prueba */}
            <form onSubmit={handleAddTestCase} className="p-4 bg-slate-50 dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
                <p className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    ➕ Agregar Caso de Prueba de Referencia
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                        type="text"
                        placeholder="Pregunta real (ej. ¿Cuáles son los requisitos de una inscripción?)"
                        value={newQuery}
                        onChange={(e) => setNewQuery(e.target.value)}
                        className="md:col-span-2 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-xs outline-none"
                        required
                    />
                    <input
                        type="text"
                        placeholder="Palabras esperadas separadas por coma (ej. escritura, pago, folio)"
                        value={newKeywords}
                        onChange={(e) => setNewKeywords(e.target.value)}
                        className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-xs outline-none"
                    />
                </div>
                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={!newQuery.trim()}
                        className="px-4 py-1.5 bg-slate-800 dark:bg-slate-700 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
                    >
                        <Plus size={14} />
                        <span>Guardar Caso de Prueba</span>
                    </button>
                </div>
            </form>

            {/* Resultados de la última corrida */}
            {results && (
                <div className="p-5 rounded-2xl border bg-slate-900 text-slate-100 space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-purple-400">Resultado de Regresión</span>
                        <span className={`px-3 py-0.5 rounded-full text-xs font-mono font-bold ${results.pass_rate_pct >= 80 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'}`}>
                            {results.pass_rate_pct}% Aprobados ({results.passed}/{results.total})
                        </span>
                    </div>

                    <div className="space-y-2">
                        {results.results.map((r, idx) => (
                            <div key={idx} className="p-3 bg-slate-800/80 rounded-xl border border-slate-750 text-xs space-y-1">
                                <div className="flex items-center justify-between">
                                    <span className="font-semibold text-slate-200">{r.query}</span>
                                    <span className={`flex items-center gap-1 font-bold ${r.is_passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                                        {r.is_passed ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                                        {r.is_passed ? 'APROBADO' : 'FALLIDO'}
                                    </span>
                                </div>
                                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{r.answer}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Lista de Casos Guardados */}
            <div className="space-y-2">
                <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Casos Registrados ({testCases.length})
                </p>
                {testCases.length === 0 ? (
                    <p className="text-xs text-slate-400 italic py-2">No hay casos de regresión guardados para este tema.</p>
                ) : (
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                        {testCases.map((tc) => (
                            <div key={tc.id} className="py-2.5 flex items-center justify-between gap-4">
                                <div>
                                    <p className="text-xs font-medium text-slate-800 dark:text-slate-200">{tc.query}</p>
                                    {tc.expected_keywords?.length > 0 && (
                                        <p className="text-[10px] text-purple-600 dark:text-purple-400 font-mono mt-0.5">
                                            Palabras esperadas: {tc.expected_keywords.join(', ')}
                                        </p>
                                    )}
                                </div>
                                <button
                                    onClick={() => handleDeleteTestCase(tc.id)}
                                    className="p-1.5 text-slate-400 hover:text-rose-500 transition"
                                    title="Eliminar caso"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
