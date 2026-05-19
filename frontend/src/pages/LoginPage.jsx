import React, { useEffect } from 'react'
import { useAuth } from 'react-oidc-context'
import { useNavigate } from 'react-router-dom'
import { Loader, ShieldCheck } from 'lucide-react'

export default function LoginPage() {
    const auth = useAuth()
    const navigate = useNavigate()

    console.log("LoginPage Rendered:", { 
        isLoading: auth.isLoading, 
        isAuthenticated: auth.isAuthenticated,
        hasLocalToken: !!localStorage.getItem('token')
    });

    useEffect(() => {
        if (auth.isAuthenticated) {
            navigate('/', { replace: true })
        }
    }, [auth.isAuthenticated, navigate])

    return (
        <div className="min-h-screen flex items-center justify-center p-4 font-sans relative overflow-hidden bg-[#0f172a]">
            {/* Background Blobs for Premium Feel */}
            <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
                <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/5 rounded-full blur-[100px]"></div>
            </div>
            
            <div className="w-full max-w-md bg-slate-900/50 backdrop-blur-xl border border-white/10 rounded-[32px] p-10 text-center relative z-10">
                <div className="mb-10">
                    <div className="flex justify-center mb-6">
                        <div className="relative">
                            <img src={`${import.meta.env.BASE_URL}assets/logos/consulta-rpp-logo.svg`} alt="ConsultaRPP Logo" className="w-24 h-24 object-contain filter brightness-125" />
                            <div className="absolute -inset-2 border border-blue-500/30 rounded-full animate-spin-slow pointer-events-none"></div>
                        </div>
                    </div>
                    <h1 className="text-3xl font-heading font-bold text-white mb-2 tracking-tight">ConsultaRPP</h1>
                    <p className="text-blue-400 font-bold text-xs tracking-[0.2em] uppercase">SISTEMA INTELIGENTE DE CONSULTAS LEGALES</p>
                </div>

                <button
                    onClick={() => void auth.signinRedirect()}
                    disabled={auth.isLoading}
                    className="w-full py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-50 transition-all font-sans font-bold flex items-center justify-center space-x-3 active:scale-95 group shadow-lg shadow-blue-500/20"
                >
                    {auth.isLoading ? <Loader className="animate-spin" size={20} /> : <ShieldCheck size={20} className="group-hover:scale-110 transition-transform" />}
                    <span>{auth.isLoading ? 'CONECTANDO...' : 'INICIAR SESIÓN CON CASMARTS ID'}</span>
                </button>

                <div className="mt-6 text-center">
                    <a 
                        href="https://arquitectura.casmart.internal/if/flow/password-recovery/" 
                        className="text-xs text-white/60 hover:text-white font-medium transition-colors"
                    >
                        ¿Olvidaste tu contraseña?
                    </a>
                </div>

                {auth.error && (
                    <div className="mt-6 p-4 bg-red-950/50 border border-red-500/30 text-red-200 rounded-xl text-xs font-medium uppercase">
                        Error de Conexión: {auth.error.message}
                    </div>
                )}

                <div className="mt-12 text-center border-t border-white/5 pt-6">
                    <p className="text-[9px] text-white/30 font-heading font-bold uppercase tracking-[0.4em]">
                        Powered by Casmarts AI Core
                    </p>
                </div>
            </div>
        </div>
    )
}
