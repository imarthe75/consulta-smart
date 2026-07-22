import React, { useState } from 'react'
import { BookOpen, Shield, User, Code, Terminal, ChevronRight, FileText, CheckCircle, Database, Layers, Sliders, Key, Lock, Cpu, Server, ExternalLink } from 'lucide-react'
import ModuleBanner from '../components/ModuleBanner'

export default function DocumentationPage() {
    const [activeTab, setActiveTab] = useState('admin')

    const tabs = [
        { id: 'admin', label: '1. Personalización de Chatbots & Temas', icon: Shield },
        { id: 'rag', label: '2. Gestión e Indexación RAG', icon: FileText },
        { id: 'widget', label: '3. Integración & Enbebido de Widget', icon: Code },
        { id: 'dev', label: '4. Arquitectura de Sistema & API REST', icon: Terminal },
    ]

    return (
        <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
            <div className="max-w-6xl mx-auto space-y-8">
                <ModuleBanner
                    badgeIcon={BookOpen}
                    badgeLabel="Manual Operativo & Técnico • ConsultaSmart Admin"
                    title="Manual de Administración y Personalización Multitenant"
                    subtitle="Guía completa para la creación de chatbots por tema, gestión e indexación vectorial de documentos RAG, personalización de guardrails/motores de IA e integración de widgets flotantes."
                    decorIcon={BookOpen}
                    tabs={tabs.map(({ id, label, icon: Icon }) => (
                        <button
                            key={id}
                            onClick={() => setActiveTab(id)}
                            className={`flex items-center space-x-2 px-5 py-3 rounded-xl text-xs font-bold transition-all ${activeTab === id
                                    ? 'bg-primary text-white shadow-lg shadow-black/30 scale-[1.02]'
                                    : 'bg-white/10 text-slate-300 hover:bg-white/20 hover:text-white'
                                }`}
                        >
                            <Icon size={16} />
                            <span>{label}</span>
                        </button>
                    ))}
                />

                {/* Content Container */}
                <div className="bg-white dark:bg-slate-900 p-6 md:p-10 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-8">

                    {/* ==========================================
                        1. PERSONALIZACIÓN DE CHATBOTS & TEMAS
                       ========================================== */}
                    {activeTab === 'admin' && (
                        <div className="space-y-8 animate-in fade-in duration-200">
                            <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex items-center justify-between">
                                <div>
                                    <div className="inline-flex items-center space-x-2 text-blue-600 dark:text-blue-400 text-xs font-bold uppercase tracking-wider mb-1">
                                        <Shield size={16} />
                                        <span>Módulo 1</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Personalización de Chatbots, Temas & Guardrails</h2>
                                </div>
                                <span className="px-3 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full border border-blue-200 dark:border-blue-800">
                                    Panel /admin
                                </span>
                            </div>

                            {/* 1.1 Creación y Gestión Multi-Tenant */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-blue-500" size={20} />
                                    1.1 Alta de Temas y Asistentes Independientes (Multi-Tenant)
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    El administrador puede crear perfiles de chatbot ilimitados (ej. <code>rpp</code>, <code>ircep</code>, <code>catastro</code>, <code>control_escolar</code>). Cada perfil posee su propio **System Prompt**, **Guardrails**, **Logos/Colores**, **Motor de IA** y **Acervo Documental aisaldo**.
                                </p>
                                <div className="pl-7 text-xs text-slate-600 dark:text-slate-300 space-y-1">
                                    <p>1. Haga clic en <strong>+ Nuevo Tema</strong> en la esquina superior del panel `/admin`.</p>
                                    <p>2. Ingrese el ID alfanumérico (ej. <code>catastro</code>) y el Nombre Oficial.</p>
                                    <p>3. Personalice el título, subtítulo, mensaje de bienvenida y seleccione la paleta de color primaria.</p>
                                </div>
                            </div>

                            {/* 1.2 Configuración del Motor LLM por Tema */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-blue-500" size={20} />
                                    1.2 Selección del Motor de IA y Claves Privadas por Tema
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    Es posible asignar un proveedor de IA específico para cada tema (ej. <strong>Groq Llama 3</strong>, <strong>GCP Vertex AI</strong>, <strong>NVIDIA NIM Cloud</strong> o <strong>Gemini</strong>) introduciendo una API Key privada.
                                </p>
                                <div className="p-4 bg-slate-50 dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 pl-7 text-xs text-slate-600 dark:text-slate-300 space-y-1.5">
                                    <p>• <strong>Enmascaramiento de API Keys:</strong> Al guardar la clave en el panel, el backend la encripta y expone únicamente una máscara (`••••••••1234`) para prevenir filtraciones visuales.</p>
                                    <p>• <strong>Fallback Automático:</strong> Si el proveedor personalizado agota sus tokens o presenta latencia, el <em>Smart Router</em> conmutará sin interrupción al proveedor global de respaldo.</p>
                                </div>
                            </div>

                            {/* 1.3 Guardrails y Generador Asistido */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-blue-500" size={20} />
                                    1.3 Guardrails, Estrictez y Generador Asistido de Prompts
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    Permite definir el grado de adherencia normativa y bloquear temas no relacionados.
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-7 text-xs">
                                    <div className="p-4 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                                        <h4 className="font-bold text-slate-800 dark:text-slate-100">Estrictez RAG</h4>
                                        <p className="text-slate-500 dark:text-slate-400">Modo <strong>Estricto</strong> fuerza al modelo a responder <em>únicamente</em> utilizando fragmentos documentales indexados, rechazando preguntas ajenas.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                                        <h4 className="font-bold text-slate-800 dark:text-slate-100">Generador CRAFT / CREA / ASPECCT</h4>
                                        <p className="text-slate-500 dark:text-slate-400">Genera automáticamente la estructura de System Prompt ideal adaptada al sector, audiencia y rol directivo.</p>
                                    </div>
                                </div>
                            </div>

                            {/* 1.4 Batería de Regresión de Prompts */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-blue-500" size={20} />
                                    1.4 Batería de Regresión de System Prompts
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    Debajo del panel de configuración del tema activo, el administrador puede registrar preguntas de referencia (con palabras clave que la respuesta debe contener) y ejecutarlas contra el System Prompt vigente con un clic. Detecta si un cambio a un prompt o guardrail rompió respuestas que antes eran correctas, antes de que lo note un usuario final.
                                </p>
                            </div>

                            {/* 1.5 Observabilidad del Motor de IA */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-blue-500" size={20} />
                                    1.5 Observabilidad del Motor de IA
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    Pestaña "Observabilidad" del panel <code>/admin</code>: consultas procesadas, tasa de satisfacción agregada (según los votos "útil"/"no útil" registrados en el chat), proveedores de IA activos y su orden de respaldo, y estado de la caché semántica.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* ==========================================
                        2. GESTIÓN E INDEXACIÓN RAG
                       ========================================== */}
                    {activeTab === 'rag' && (
                        <div className="space-y-8 animate-in fade-in duration-200">
                            <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex items-center justify-between">
                                <div>
                                    <div className="inline-flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
                                        <FileText size={16} />
                                        <span>Módulo 2</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Gestión e Indexación de Documentos RAG (/documentos)</h2>
                                </div>
                                <span className="px-3 py-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-xs font-semibold rounded-full border border-emerald-200 dark:border-emerald-800">
                                    Base de Conocimiento
                                </span>
                            </div>

                            {/* 2.1 Carga y Categorización */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-emerald-500" size={20} />
                                    2.1 Procedimiento de Carga y Categorización de Archivos
                                </h3>
                                <div className="pl-7 space-y-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                                    <p>1. Seleccione el <strong>Proyecto / Tenant de Destino</strong> obligatorio al que responderá el documento.</p>
                                    <p>2. Arrastre o seleccione un archivo compatible (<strong>PDF, Word DOC/DOCX, TXT, Markdown, PNG/JPG</strong>) con un tamaño máximo de <strong>50 MB</strong>.</p>
                                    <p>3. Seleccione la <strong>Categoría / Tipo de Documento</strong> (<em>Reglamentos, Guías, Trámites, Costos, FAQs, Formatos, Instructivos</em>).</p>
                                    <p>4. Haga clic en <strong>Cargar e Indexar en el RAG</strong>. El backend ejecutará la extracción de texto, fragmentación y generación de vectores de incrustación.</p>
                                </div>
                            </div>

                            {/* 2.2 Indicador de Salud del Índice y Reintentos */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-emerald-500" size={20} />
                                    2.2 Monitor de Salud del Índice Vectorial y Reintentos
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    Cada documento exhibe una barra porcentual de salud basada en la proporción de fragmentos con incrustación vectorial efectiva (`embedded_chunks / total_chunks`).
                                </p>
                                <div className="p-4 bg-slate-50 dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 pl-7 text-xs text-slate-600 dark:text-slate-300 space-y-1.5">
                                    <p>• <span className="font-bold text-emerald-600">Salud &gt;= 95%:</span> Estado <em>Indexado</em> completo disponible para la búsqueda semántica e híbrida.</p>
                                    <p>• <span className="font-bold text-amber-600">Salud &lt; 95% o Parcial:</span> Muestra el botón <strong>Reintentar</strong> para forzar la re-generación asíncrona de embeddings en Celery sin necesidad de volver a subir el archivo.</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ==========================================
                        3. INTEGRACIÓN & ENBEBIDO DE WIDGET
                       ========================================== */}
                    {activeTab === 'widget' && (
                        <div className="space-y-8 animate-in fade-in duration-200">
                            <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex items-center justify-between">
                                <div>
                                    <div className="inline-flex items-center space-x-2 text-purple-600 dark:text-purple-400 text-xs font-bold uppercase tracking-wider mb-1">
                                        <Code size={16} />
                                        <span>Módulo 3</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Guía de Integración y Enbebido del Widget Flotante</h2>
                                </div>
                                <span className="px-3 py-1 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 text-xs font-semibold rounded-full border border-purple-200 dark:border-purple-800">
                                    Integración Web
                                </span>
                            </div>

                            {/* 3.1 Emisión e Incrustación de Widget */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-purple-500" size={20} />
                                    3.1 Inclusión en Portales Institucionales mediante Iframe / Script
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    Cualquier portal web externo (ej. sitios estatales, gubernamentales o educativos) puede embeber el asistente configurado añadiendo el parámetro de tenant en la URL.
                                </p>
                                <div className="pl-7 space-y-3">
                                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs space-y-2 border border-slate-800 shadow-md">
                                        <p className="text-slate-400">// Ejemplo de Iframe para incorporar el Asistente de Catastro o RPP:</p>
                                        <pre className="text-amber-300">
{`<iframe 
  src="https://chat.casmart.internal/widget?tenant=rpp&themeColor=%230284c7" 
  width="400" 
  height="600" 
  style="border:none; position:fixed; bottom:20px; right:20px; z-index:9999;"
></iframe>`}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ==========================================
                        3. GUÍA DEL DESARROLLADOR & API
                       ========================================== */}
                    {activeTab === 'dev' && (
                        <div className="space-y-8 animate-in fade-in duration-200">
                            <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex items-center justify-between">
                                <div>
                                    <div className="inline-flex items-center space-x-2 text-purple-600 dark:text-purple-400 text-xs font-bold uppercase tracking-wider mb-1">
                                        <Terminal size={16} />
                                        <span>Sección 3</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Guía del Desarrollador & Especificaciones API</h2>
                                </div>
                                <span className="px-3 py-1 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 text-xs font-semibold rounded-full border border-purple-200 dark:border-purple-800">
                                    Arquitectura & SDK
                                </span>
                            </div>

                            {/* 3.1 Arquitectura de Software */}
                            <div className="space-y-3">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-purple-500" size={20} />
                                    3.1 Arquitectura del Ecosistema
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pl-7">
                                    ConsultaSmart está compuesto por una arquitectura orientada a servicios totalmente desacoplada:
                                </p>
                                <ul className="list-disc pl-12 text-xs text-slate-600 dark:text-slate-300 space-y-1.5">
                                    <li><strong>Frontend (SPA):</strong> React 18, Vite, TailwindCSS y Lucide Icons. Gestión de estado mediante Zustand.</li>
                                    <li><strong>Backend (Core API):</strong> FastAPI (Python 3.12) asíncrono con SQLAlchemy ORM y Uvicorn.</li>
                                    <li><strong>Motor RAG & Búsqueda Híbrida:</strong> PostgreSQL 16 con extensión <code className="font-mono text-purple-600">pgvector</code> para almacenamiento de incrustaciones y <code className="font-mono text-purple-600">tsvector/ts_rank</code> para búsqueda léxica.</li>
                                    <li><strong>Enrutador Inteligente LLM (Smart Router):</strong> Conmutación y fallback automático entre Groq (Llama 3), GCP Vertex AI, NVIDIA NIM Cloud y Gemini.</li>
                                    <li><strong>Caché Semántica Híbrida:</strong> Redis para hashing de consultas exactas e incrustaciones locales (SentenceTransformers) para similitud de coseno (&gt;0.92).</li>
                                    <li><strong>Autenticación & SSO:</strong> OIDC / OAuth2 integrado con Authentik Login Manager.</li>
                                </ul>
                            </div>

                            {/* 3.2 Especificación de Endpoints de Administración y RAG */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                                    <ChevronRight className="text-purple-500" size={20} />
                                    3.2 Especificación de Endpoints REST (API V1)
                                </h3>

                                <div className="space-y-4 pl-7">
                                    {/* Endpoint 1: Consulta RAG */}
                                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs space-y-2 border border-slate-800 shadow-md">
                                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                            <span className="text-emerald-400 font-bold">POST /api/v1/chat/query</span>
                                            <span className="text-slate-400 text-[11px]">Envío de Consulta RAG</span>
                                        </div>
                                        <p className="text-slate-400">// Body JSON:</p>
                                        <pre className="text-amber-300">
{`{
  "session_id": "019f85c3-aeb0-7744-a7f0-00572933bd48",
  "message": "¿Cuáles son los costos de inscripción en el RPP?",
  "filters": { "category": "rpp" }
}`}
                                        </pre>
                                    </div>

                                    {/* Endpoint 2: Feedback */}
                                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs space-y-2 border border-slate-800 shadow-md">
                                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                            <span className="text-blue-400 font-bold">POST /api/v1/chat/messages/&#123;id&#125;/feedback</span>
                                            <span className="text-slate-400 text-[11px]">Registro de Útil / No Útil</span>
                                        </div>
                                        <pre className="text-amber-300">{`{ "rating": "up", "comment": "Excelente respuesta" }`}</pre>
                                        <p className="text-slate-500 text-[11px]">// rating: "up" | "down". Solo puede calificarse un mensaje de una sesión propia (BOLA verificado en el backend).</p>
                                    </div>

                                    {/* Endpoint 3: Regresión de Prompts */}
                                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs space-y-2 border border-slate-800 shadow-md">
                                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                            <span className="text-purple-400 font-bold">POST /api/v1/admin/chatbot/profiles/&#123;id&#125;/run-regression</span>
                                            <span className="text-slate-400 text-[11px]">Ejecución de Batería de Regresión</span>
                                        </div>
                                        <p className="text-slate-400">// Evalúa casos de prueba registrados verificando inclusión de palabras clave esperadas.</p>
                                    </div>

                                    {/* Endpoint 4: Observabilidad LLM Router */}
                                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs space-y-2 border border-slate-800 shadow-md">
                                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                                            <span className="text-amber-400 font-bold">GET /api/v1/admin/stats/llm-router</span>
                                            <span className="text-slate-400 text-[11px]">Métricas de Proveedores y Caché</span>
                                        </div>
                                        <p className="text-slate-400">// Retorna disponibilidad, latencia y tasa de aciertos de caché semántica.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

