import React, { useState, useEffect } from 'react'
import api from '../../services/api'
import { History, RotateCcw, RefreshCw, Plus, Pencil, Trash2, Undo2 } from 'lucide-react'

const ACTION_META = {
    create: { label: 'Creación', icon: Plus, color: 'var(--cs-success)', bg: 'var(--cs-success-bg)' },
    update: { label: 'Edición', icon: Pencil, color: 'var(--cs-info)', bg: 'var(--cs-info-bg)' },
    delete: { label: 'Eliminación', icon: Trash2, color: 'var(--cs-danger)', bg: 'var(--cs-danger-bg)' },
    restore: { label: 'Restauración', icon: Undo2, color: 'var(--cs-warning)', bg: 'var(--cs-warning-bg)' },
}

/**
 * ProfileAuditLogPanel — Bitácora de cambios del tema activo (práctica CMMI CM).
 *
 * Se agregó tras un incidente real (2026-07-22): el tema 'general' quedó con un
 * System Prompt corrupto sin forma de saber quién lo cambió ni de recuperarlo.
 * Este panel consume GET /admin/chatbot/profiles/{id}/audit-log y permite
 * restaurar cualquier estado previo con un clic (POST .../restore/{audit_log_id}).
 *
 * @param {string} profileId - Identificador del tema activo.
 * @param {Function} onRestored - Callback invocado tras una restauración exitosa,
 *   para que el componente padre recargue la configuración del tema en pantalla.
 */
export default function ProfileAuditLogPanel({ profileId = 'general', onRestored }) {
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(true)
    const [restoringId, setRestoringId] = useState(null)

    const fetchLog = async () => {
        setLoading(true)
        try {
            const res = await api.get(`admin/chatbot/profiles/${profileId}/audit-log`)
            if (Array.isArray(res.data)) {
                setEntries(res.data)
            }
        } catch (err) {
            console.error('Error al cargar la bitácora de cambios:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchLog()
    }, [profileId])

    const handleRestore = async (entry) => {
        if (!entry.after) return
        if (!window.confirm(
            `¿Restaurar el tema a su estado del ${new Date(entry.created_at).toLocaleString()}? ` +
            `Esto sobreescribirá la configuración actual (quedará registrado como una nueva entrada en esta bitácora).`
        )) return

        setRestoringId(entry.id)
        try {
            await api.post(`admin/chatbot/profiles/${profileId}/restore/${entry.id}`)
            await fetchLog()
            if (onRestored) onRestored()
        } catch (err) {
            console.error('Error al restaurar:', err)
        } finally {
            setRestoringId(null)
        }
    }

    return (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                    <History size={16} className="text-slate-500" />
                    Historial de Cambios ({profileId})
                </h3>
                <button
                    onClick={fetchLog}
                    className="p-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-300 rounded-lg transition"
                    title="Actualizar historial"
                >
                    <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            {entries.length === 0 && !loading ? (
                <p className="text-xs text-slate-400 italic">Sin cambios registrados todavía para este tema.</p>
            ) : (
                <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                    {entries.map((entry) => {
                        const meta = ACTION_META[entry.action] || ACTION_META.update
                        const Icon = meta.icon
                        return (
                            <div
                                key={entry.id}
                                className="flex items-center justify-between gap-3 p-2.5 rounded-xl border border-slate-100 dark:border-slate-800 text-xs"
                            >
                                <div className="flex items-center gap-2 min-w-0">
                                    <span
                                        className="p-1.5 rounded-lg shrink-0"
                                        style={{ backgroundColor: meta.bg, color: meta.color }}
                                    >
                                        <Icon size={12} />
                                    </span>
                                    <div className="min-w-0">
                                        <p className="font-semibold text-slate-700 dark:text-slate-200">{meta.label}</p>
                                        <p className="text-[10px] text-slate-400 truncate">
                                            {entry.changed_by_email || 'usuario desconocido'} · {new Date(entry.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                {entry.after && (
                                    <button
                                        onClick={() => handleRestore(entry)}
                                        disabled={restoringId === entry.id}
                                        className="shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-bold border transition disabled:opacity-50"
                                        style={{ borderColor: 'var(--cs-info)', color: 'var(--cs-info)' }}
                                        title="Restaurar la configuración a este punto"
                                    >
                                        <RotateCcw size={11} className={restoringId === entry.id ? 'animate-spin' : ''} />
                                        Restaurar
                                    </button>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
