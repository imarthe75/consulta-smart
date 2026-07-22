import React, { useState } from 'react'
import { Sparkles, RefreshCw } from 'lucide-react'
import api from '../../services/api'

/**
 * PromptGenerator — Componente asistido para la redacción de System Prompts.
 * Utiliza metodologías de ingeniería de prompts (CRAFT, CREA, ASPECCT) para estructurar
 * automáticamente las instrucciones del modelo de lenguaje según el tema y audiencia.
 * 
 * @param {Function} onPromptGenerated - Callback invocado al generar con éxito el prompt.
 */
export default function PromptGenerator({ onPromptGenerated }) {
    // Estado de carga durante la llamada a la API de generación
    const [generating, setGenerating] = useState(false)
    // Tema central sobre el cual se construirá el prompt (ej. "Inscripciones Registrales")
    const [topic, setTopic] = useState('')
    // Metodología de ingeniería de prompts seleccionada ('craft', 'crea', 'aspecct')
    const [methodology, setMethodology] = useState('craft')
    // Audiencia objetivo para adaptar el tono y vocabulario del prompt
    const [targetAudience, setTargetAudience] = useState('Ciudadanía en General (Público Abierto)')
    // Nombre de la dependencia u organización
    const [organization, setOrganization] = useState('Registro Público / Catastro')
    // Sector institucional / empresarial
    const [sector, setSector] = useState('Gobierno Estatal / Organismo Descentralizado')

    /**
     * Envia los parámetros al endpoint POST /admin/generate-prompt para obtener
     * la estructura del System Prompt adaptada.
     */
    const handleGenerate = async () => {
        if (!topic.trim()) return
        setGenerating(true)
        try {
            const res = await api.post('admin/generate-prompt', { 
                topic, 
                context: 'consulta',
                methodology,
                target_audience: targetAudience,
                organization,
                sector
            })
            if (res.data && res.data.prompt) {
                onPromptGenerated(res.data.prompt, methodology)
            }
        } catch (error) {
            console.error("Error generando prompt:", error)
        } finally {
            setGenerating(false)
        }
    }

    return (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Sparkles className="text-amber-500" size={20} />
                Generador Asistido de System Prompt
            </h2>
            
            {/* Selección de Metodología de Ingeniería de Prompts */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <button
                    type="button"
                    onClick={() => setMethodology('craft')}
                    className={`p-2.5 rounded-lg text-left border transition ${methodology === 'craft' ? 'bg-blue-600 text-white font-bold' : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700'}`}
                >
                    <p className="text-xs">1. CRAFT</p>
                    <p className="text-[10px] opacity-80 mt-0.5">Contexto ➔ Rol ➔ Acción ➔ Tono</p>
                </button>
                <button
                    type="button"
                    onClick={() => setMethodology('crea')}
                    className={`p-2.5 rounded-lg text-left border transition ${methodology === 'crea' ? 'bg-blue-600 text-white font-bold' : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700'}`}
                >
                    <p className="text-xs">2. CREA</p>
                    <p className="text-[10px] opacity-80 mt-0.5">Contexto ➔ Especificidad ➔ Acción</p>
                </button>
                <button
                    type="button"
                    onClick={() => setMethodology('aspecct')}
                    className={`p-2.5 rounded-lg text-left border transition ${methodology === 'aspecct' ? 'bg-blue-600 text-white font-bold' : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700'}`}
                >
                    <p className="text-xs">3. ASPECCT</p>
                    <p className="text-[10px] opacity-80 mt-0.5">Acción ➔ Persona ➔ Ejemplos</p>
                </button>
            </div>

            {/* Input de tema y botón de ejecución */}
            <div className="flex gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <input
                    type="text"
                    placeholder={`Escribe el tema: ej. Inscripción de Inmuebles, Control Escolar...`}
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="flex-1 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm focus:outline-none text-slate-800 dark:text-slate-100"
                />
                <button
                    onClick={handleGenerate}
                    disabled={generating || !topic.trim()}
                    className="bg-primary hover:bg-primary/95 text-white bg-blue-600 px-5 py-2 rounded-xl font-semibold text-xs transition flex items-center gap-2 disabled:opacity-50"
                >
                    {generating ? <RefreshCw className="animate-spin" size={14} /> : <Sparkles size={14} />}
                    <span>Generar Prompt</span>
                </button>
            </div>
        </div>
    )
}
