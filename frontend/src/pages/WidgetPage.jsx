import React, { useEffect, useState } from 'react'
import ChatInterface from '../components/ChatInterface'
import { useAuthStore } from '../stores/authStore'
import { RefreshCcw } from 'lucide-react'

export default function WidgetPage() {
    const { isAuthenticated, guestLogin } = useAuthStore()
    const [initializing, setInitializing] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const initGuest = async () => {
            try {
                if (!isAuthenticated) {
                    await guestLogin()
                }
                setInitializing(false)
            } catch (err) {
                console.error("Error initializing widget guest session:", err)
                setError("Error al conectar con el asistente. Por favor, intente más tarde.")
                setInitializing(false)
            }
        }
        initGuest()
    }, [isAuthenticated, guestLogin])

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
