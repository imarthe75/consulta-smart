import React, { useEffect, useState } from 'react'
import ChatInterface from '../components/ChatInterface'
import { useAuthStore } from '../stores/authStore'
import { RefreshCcw } from 'lucide-react'

export default function WidgetPage() {
    const { guestLogin } = useAuthStore()
    const [initializing, setInitializing] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const initGuest = async () => {
            try {
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
