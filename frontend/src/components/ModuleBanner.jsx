import React from 'react'

/**
 * Banner de encabezado estándar para las páginas de módulo (Admin, Documentos RAG,
 * Documentación, Integración de Widget, etc.). Unifica el gradiente, la tipografía
 * y el badge que antes estaban duplicados de forma inconsistente en cada página
 * (distintos colores de gradiente, tamaños de título e iconos decorativos).
 *
 * El gradiente usa los tokens de marca reales (--color-primary/--color-secondary
 * definidos en index.css), no colores Tailwind arbitrarios.
 */
export default function ModuleBanner({
    badgeIcon: BadgeIcon,
    badgeLabel,
    title,
    subtitle,
    decorIcon: DecorIcon,
    actions,
    tabs,
}) {
    return (
        <div className="bg-gradient-to-r from-primary via-secondary to-slate-950 rounded-2xl p-6 md:p-8 text-white shadow-xl relative overflow-hidden">
            {DecorIcon && (
                <div className="absolute right-[-20px] top-[-20px] opacity-10 pointer-events-none">
                    <DecorIcon size={220} />
                </div>
            )}
            <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    {badgeLabel && (
                        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-blue-200 border border-white/20 text-xs font-bold uppercase tracking-widest mb-2">
                            {BadgeIcon && <BadgeIcon size={14} />}
                            <span>{badgeLabel}</span>
                        </div>
                    )}
                    <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">{title}</h1>
                    {subtitle && (
                        <p className="text-slate-300 text-sm mt-1 max-w-2xl">{subtitle}</p>
                    )}
                </div>
                {actions && (
                    <div className="flex items-center gap-2 relative z-10">{actions}</div>
                )}
            </div>
            {tabs && (
                <div className="flex flex-wrap gap-2 pt-4 mt-4 border-t border-white/10 relative z-10">
                    {tabs}
                </div>
            )}
        </div>
    )
}
