import React, { useEffect, useState } from 'react'
import ChatInterface from '../components/ChatInterface'
import { useAuthStore } from '../stores/authStore'
import api from '../services/api'
import { RefreshCcw, ShieldOff } from 'lucide-react'

export default function WidgetPage() {
    const { guestLogin } = useAuthStore()
    const [initializing, setInitializing] = useState(true)
    const [error, setError] = useState(null)
    const [blocked, setBlocked] = useState(false)

    useEffect(() => {
        const initGuest = async () => {
            try {
                // El widget es el único punto de entrada público/no autenticado de la
                // app (embebible en sitios de terceros vía widget.js) -- se verifica
                // ANTES del guest login si el tema lo permite
                // (config_metadata.enable_widget_embed, panel admin). Default true
                // (comportamiento actual) para no romper ningún embed ya desplegado.
                // Fail-open si la verificación misma falla (red, tema inexistente):
                // no bloquear el widget por un error ajeno al permiso en sí.
                const queryParams = new URLSearchParams(window.location.search)
                const tenantId = queryParams.get('tenantId') || queryParams.get('tenant') || 'general'
                try {
                    const profileRes = await api.get(`chat/profiles/${tenantId}`)
                    if (profileRes.data?.enable_widget_embed === false) {
                        setBlocked(true)
                        setInitializing(false)
                        return
                    }
                } catch (profileErr) {
                    console.error("Error verificando permiso de embed del tema:", profileErr)
                }

                // SIEMPRE se establece una sesión de invitado nueva, sin importar
                // `isAuthenticated` -- el widget vive en el mismo origen
                // (chat.casmart.internal) que el panel de administración, y
                // comparte su localStorage. Si un admin inició sesión real ahí
                // (aunque sea en otra pestaña) y luego visita un sitio de
                // terceros con el widget embebido, `isAuthenticated` ya viene en
                // `true` con SU token real -- el widget terminaba operando con
                // esa sesión real (o, si ya expiró, disparando un 401 que un
                // interceptor global redirigía a /login DENTRO del iframe,
                // reemplazando el chat por la pantalla de login real).
                // Incidente real 2026-08-14. El guest login es idempotente del
                // lado del backend (siempre re-autentica contra el usuario
                // dedicado del widget), así que no hay costo real en llamarlo
                // siempre.
                await guestLogin()
                setInitializing(false)
            } catch (err) {
                console.error("Error initializing widget guest session:", err)
                setError("Error al conectar con el asistente. Por favor, intente más tarde.")
                setInitializing(false)
            }
        }
        initGuest()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    if (initializing) {
        return (
            <div className="w-full h-full flex flex-col items-center justify-center bg-white space-y-4">
                <RefreshCcw size={32} className="text-blue-600 animate-spin" />
                <p className="text-slate-500 font-medium animate-pulse">Iniciando asistente...</p>
            </div>
        )
    }

    if (blocked) {
        return (
            <div className="w-full h-full flex flex-col items-center justify-center bg-white p-6 text-center space-y-2">
                <ShieldOff size={28} className="text-slate-300" />
                <p className="text-slate-500 font-medium text-sm">Este asistente no está disponible para uso embebido.</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="w-full h-full flex flex-col items-center justify-center bg-white p-6 text-center">
                <p className="text-red-500 font-bold">{error}</p>
            </div>
        )
    }

    return (
        <div className="w-full h-screen">
            <ChatInterface isWidget={true} />
        </div>
    )
}
