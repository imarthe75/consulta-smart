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
        // Only redirect to app if we have BOTH OIDC auth AND our local token
        if (auth.isAuthenticated && localStorage.getItem('token')) {
            navigate('/', { replace: true })
        }
    }, [auth.isAuthenticated, navigate])

    return (
        <div className="min-h-screen flex items-center justify-center p-4 font-sans relative overflow-hidden" style={{ background: 'radial-gradient(circle at center, #003a66 0%, #002A4C 100%)' }}>
            <div className="w-full max-w-md bg-white rounded-[40px] p-10 text-center relative z-10 border-none">
                <div className="mb-10">
                    <div className="flex justify-center mb-6">
                        <div className="relative">
                            <img src={`${import.meta.env.BASE_URL}assets/logos/consulta-rpp-logo.svg`} alt="ConsultaRPP Logo" className="w-24 h-24 object-contain" />
                            <div className="absolute -inset-2 border border-primaryLight/30 rounded-full animate-spin-slow pointer-events-none"></div>
                        </div>
                    </div>
                    <h1 className="text-3xl font-heading font-bold text-[#002A4C] mb-2 tracking-tight">ConsultaRPP</h1>
                    <p className="text-[#BDC3C7] font-bold text-xs tracking-[0.2em] uppercase">SISTEMA INTELIGENTE DE CONSULTAS LEGALES</p>
                </div>

                <button
                    onClick={() => void auth.signinRedirect()}
                    disabled={auth.isLoading}
                    className="w-full py-4 bg-[#002A4C] text-white rounded-lg hover:bg-primaryLight disabled:opacity-50 transition-all font-sans font-bold flex items-center justify-center space-x-3 active:scale-95 group"
                >
                    {auth.isLoading ? <Loader className="animate-spin" size={20} /> : <ShieldCheck size={20} className="group-hover:scale-110 transition-transform" />}
                    <span>{auth.isLoading ? 'CONECTANDO...' : 'INICIAR SESIÓN CON CASMARTS ID'}</span>
                </button>

                <div className="mt-6 text-center">
                    <a 
                        href="https://arquitectura.casmart.internal/if/flow/password-recovery/" 
                        className="text-xs text-[#002A4C]/60 hover:text-[#002A4C] font-medium transition-colors"
                    >
                        ¿Olvidaste tu contraseña?
                    </a>
                </div>

                {auth.error && (
                    <div className="mt-6 p-4 bg-red-50 border border-danger/30 text-danger rounded-lg text-xs font-medium">
                        Error de Conexión: {auth.error.message}
                    </div>
                )}

                <div className="mt-12 text-center border-t border-slate-100 pt-6">
                    <p className="text-[9px] text-slate-400 font-heading font-bold uppercase tracking-[0.4em]">
                        Powered by Casmarts AI Core
                    </p>
                </div>
            </div>
        </div>
    )
}
