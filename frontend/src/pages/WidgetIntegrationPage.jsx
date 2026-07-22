import React, { useState, useEffect } from 'react'
import { Code, Copy, Check, Layers, ExternalLink, Sparkles, Sliders, Smartphone, Laptop } from 'lucide-react'
import api from '../services/api'
import ModuleBanner from '../components/ModuleBanner'

export default function WidgetIntegrationPage() {
    const [profiles, setProfiles] = useState([])
    const [selectedTenant, setSelectedTenant] = useState('general')
    const [themeColor, setThemeColor] = useState('#3b82f6')
    const [title, setTitle] = useState('Asistente Virtual')
    const [copied, setCopied] = useState(false)
    const [viewMode, setViewMode] = useState('script')

    useEffect(() => {
        const loadProfiles = async () => {
            try {
                const res = await api.get('admin/chatbot/profiles')
                setProfiles(res.data)
                if (res.data.length > 0) {
                    const first = res.data[0]
                    setSelectedTenant(first.id)
                    setThemeColor(first.primary_color || '#3b82f6')
                    setTitle(first.title || first.name)
                }
            } catch (err) {
                console.error("Error loading profiles for widget:", err)
            }
        }
        loadProfiles()
    }, [])

    const handleTenantChange = (tenantId) => {
        setSelectedTenant(tenantId)
        const match = profiles.find(p => p.id === tenantId)
        if (match) {
            setThemeColor(match.primary_color || '#3b82f6')
            setTitle(match.title || match.name)
        }
    }

    const appUrl = window.location.origin + import.meta.env.BASE_URL

    const scriptSnippet = `<!-- ConsultaSmart Widget Snippet -->
<script 
  src="${appUrl}widget.js" 
  data-tenant-id="${selectedTenant}"
  data-primary-color="${themeColor}"
  data-title="${title}"
  async>
</script>`

    const iframeSnippet = `<iframe
  src="${appUrl}widget?tenantId=${selectedTenant}&themeColor=${encodeURIComponent(themeColor)}"
  width="400"
  height="600"
  style="border: none; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.2);"
  title="${title}">
</iframe>`

    const activeSnippet = viewMode === 'script' ? scriptSnippet : iframeSnippet

    const handleCopy = () => {
        navigator.clipboard.writeText(activeSnippet)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
            <div className="max-w-6xl mx-auto space-y-8">
                <ModuleBanner
                    badgeIcon={Code}
                    badgeLabel="SDK & Widget Embed"
                    title="Integración de Widget Flotante"
                    subtitle="Personaliza e integra el chat de IA RAG multitenant en cualquier portal web o aplicación externa en cuestión de minutos."
                    decorIcon={Code}
                />

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Controls Configurator */}
                    <div className="lg:col-span-5 space-y-6">
                        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
                            <div className="flex items-center space-x-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                                <Sliders className="text-blue-500" size={20} />
                                <h2 className="font-bold text-lg">Configurador del Widget</h2>
                            </div>

                            {/* Tenant Selector */}
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                                    Aplicativo / Tenant Destino
                                </label>
                                <select
                                    value={selectedTenant}
                                    onChange={(e) => handleTenantChange(e.target.value)}
                                    className="w-full px-3 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    {profiles.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.name} ({p.id})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Widget Title */}
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                                    Título de Encabezado
                                </label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    className="w-full px-3 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>

                            {/* Primary Color Picker */}
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                                    Color Primario de Marca
                                </label>
                                <div className="flex items-center space-x-3">
                                    <input
                                        type="color"
                                        value={themeColor}
                                        onChange={(e) => setThemeColor(e.target.value)}
                                        className="w-10 h-10 rounded-lg cursor-pointer border-none bg-transparent"
                                    />
                                    <input
                                        type="text"
                                        value={themeColor}
                                        onChange={(e) => setThemeColor(e.target.value)}
                                        className="flex-1 px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-mono"
                                    />
                                </div>
                            </div>

                            {/* Embed Mode Tabs */}
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                                    Método de Integración
                                </label>
                                <div className="grid grid-cols-2 gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
                                    <button
                                        onClick={() => setViewMode('script')}
                                        className={`py-2 text-xs font-semibold rounded-lg transition-all ${viewMode === 'script' ? 'bg-white dark:bg-slate-700 shadow text-blue-600 dark:text-blue-400' : 'text-slate-500'}`}
                                    >
                                        Script JS (Flotante)
                                    </button>
                                    <button
                                        onClick={() => setViewMode('iframe')}
                                        className={`py-2 text-xs font-semibold rounded-lg transition-all ${viewMode === 'iframe' ? 'bg-white dark:bg-slate-700 shadow text-blue-600 dark:text-blue-400' : 'text-slate-500'}`}
                                    >
                                        iFrame Embebido
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 p-5 rounded-2xl space-y-2">
                            <div className="flex items-center space-x-2 text-blue-700 dark:text-blue-300 font-semibold text-sm">
                                <Sparkles size={18} />
                                <span>Aislamiento de Respuestas RAG</span>
                            </div>
                            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                                El parámetro <code className="bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded border border-blue-200 dark:border-slate-700 text-blue-600 font-mono">data-tenant-id="{selectedTenant}"</code> garantiza que el chat consulte de forma exclusiva la base documental y reglas asociadas a este aplicativo.
                            </p>
                        </div>
                    </div>

                    {/* Code Snippet & Live Preview */}
                    <div className="lg:col-span-7 space-y-6">
                        {/* Code Display */}
                        <div className="bg-slate-900 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
                            <div className="flex items-center justify-between px-5 py-3 bg-slate-950 border-b border-slate-800">
                                <div className="flex items-center space-x-2">
                                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                    <span className="ml-2 text-xs font-mono text-slate-400">codigo_integracion.html</span>
                                </div>
                                <button
                                    onClick={handleCopy}
                                    className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                                >
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                    <span>{copied ? '¡Copiado!' : 'Copiar Código'}</span>
                                </button>
                            </div>
                            <div className="p-5 font-mono text-xs overflow-x-auto text-emerald-400 leading-relaxed">
                                <pre>{activeSnippet}</pre>
                            </div>
                        </div>

                        {/* Live Widget Preview Frame */}
                        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="font-bold text-sm text-slate-700 dark:text-slate-300 flex items-center gap-2">
                                    <Sparkles size={16} className="text-amber-500" />
                                    <span>Vista Previa Interactiva del Widget ({selectedTenant})</span>
                                </h3>
                                <a
                                    href={`${appUrl}widget?tenantId=${selectedTenant}&themeColor=${encodeURIComponent(themeColor)}&title=${encodeURIComponent(title)}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center space-x-1 text-xs text-blue-600 dark:text-blue-400 font-semibold hover:underline"
                                >
                                    <span>Abrir ventana independiente</span>
                                    <ExternalLink size={12} />
                                </a>
                            </div>

                            {/* Card de Simulación Visual con Color y Título Dinámicos */}
                            <div className="w-full h-[450px] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-md bg-slate-100 dark:bg-slate-950 flex flex-col relative">
                                {/* Header del Widget con el color primario dinámico */}
                                <div 
                                    className="p-4 text-white flex items-center justify-between shadow-sm transition-colors duration-300"
                                    style={{ backgroundColor: themeColor }}
                                >
                                    <div className="flex items-center space-x-3">
                                        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center font-bold text-xs shrink-0">
                                            🤖
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-bold leading-tight">{title || 'Asistente Virtual'}</h4>
                                            <p className="text-[10px] text-white/80 leading-none mt-0.5 font-mono">Tenant: {selectedTenant}</p>
                                        </div>
                                    </div>
                                    <span className="text-[10px] bg-black/20 px-2 py-0.5 rounded-md font-mono">
                                        En Vivo
                                    </span>
                                </div>

                                {/* Frame del Widget */}
                                <div className="flex-1 w-full relative">
                                    <iframe
                                        key={`${selectedTenant}-${themeColor}-${title}`}
                                        src={`${appUrl}widget?tenantId=${selectedTenant}&themeColor=${encodeURIComponent(themeColor)}&title=${encodeURIComponent(title)}`}
                                        className="w-full h-full border-none"
                                        title="Widget Preview"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
