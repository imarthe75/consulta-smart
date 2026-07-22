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
                    <h1 className="text-3xl font-heading font-bold text-white mb-2 tracking-tight">Consulta Smart</h1>
                    <p className="text-blue-400 font-bold text-xs tracking-[0.2em] uppercase">SISTEMA INTELIGENTE DE CONSULTAS Y ASESORÍA</p>
                </div>

                <button
                    onClick={() => void auth.signinRedirect()}
                    disabled={auth.isLoading}
                    className="w-full py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-50 transition-all font-sans font-bold flex items-center justify-center space-x-3 active:scale-95 group shadow-lg shadow-blue-500/20"
                >
                    {auth.isLoading ? <Loader className="animate-spin" size={20} /> : <ShieldCheck size={20} className="group-hover:scale-110 transition-transform" />}
                    <span>{auth.isLoading ? 'CONECTANDO...' : 'INICIAR SESIÓN CON CASMARTS ID'}</span>
                </button>

                {auth.error && (
                    <div className="mt-6 p-4 bg-amber-950/60 border border-amber-500/40 text-amber-200 rounded-2xl text-xs font-medium space-y-2 text-left">
                        <div className="flex items-center gap-2 text-amber-400 font-bold uppercase tracking-wider">
                            <ShieldCheck size={16} />
                            <span>Certificado SSL Interno (CA Local)</span>
                        </div>
                        <p className="text-[11px] leading-relaxed text-amber-200/90">
                            El servidor de autenticación utiliza un certificado HTTPS interno. Si es tu primera vez accediendo desde este navegador, debes autorizar el certificado autofirmado:
                        </p>
                        <a 
                            href="https://auth.casmart.internal/application/o/consulta-smart/.well-known/openid-configuration" 
                            target="_blank" 
                            rel="noreferrer"
                            className="inline-block mt-1 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg text-[11px] transition shadow"
                        >
                            🔐 Abrir y Aceptar Certificado SSL en Authentik ↗
                        </a>
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
