import React, { useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { authAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, Loader, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import keycloak from '../lib/keycloak'

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [username, setUsername] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const navigate = useNavigate()
    const { login } = useAuthStore()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            if (isLogin) {
                const response = await authAPI.login(email, password)
                const { user_id, email: user_email, access_token } = response.data
                const user = { id: user_id, email: user_email }
                login(user, access_token)
                navigate('/', { replace: true })
            } else {
                const response = await authAPI.register(email, username, password)
                const { id, email: user_email } = response.data.data
                setIsLogin(true)
                setError('Registro exitoso. Por favor inicia sesión.')
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Error de autenticación')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="flex justify-center mb-4">
                        <div className="relative">
                            <img src="/consultarpp/assets/logos/consulta-rpp-logo.svg" alt="ConsultaRPP Logo" className="w-20 h-20 rounded-2xl shadow-xl" />
                            <span className="absolute -bottom-2 -right-2 text-3xl">🏛️</span>
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold text-primary mb-2">ConsultaRPP</h1>
                    <p className="text-gray-600 font-medium">Sistema Inteligente de Consultas Legales</p>
                </div>

                {/* Formulario Personalizado */}
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-2 uppercase tracking-wide">
                            Correo Electrónico
                        </label>
                        <div className="relative group">
                            <Mail className="absolute left-4 top-4 text-slate-400 group-focus-within:text-primary transition-colors" size={20} />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                placeholder="usuario@casmarts.com"
                                className="w-full pl-12 pr-4 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:outline-none focus:border-primary focus:bg-white transition-all shadow-inner"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-2 uppercase tracking-wide">
                            Contraseña
                        </label>
                        <div className="relative group">
                            <Lock className="absolute left-4 top-4 text-slate-400 group-focus-within:text-primary transition-colors" size={20} />
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                placeholder="••••••••"
                                className="w-full pl-12 pr-12 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:outline-none focus:border-primary focus:bg-white transition-all shadow-inner"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-4 text-slate-400 hover:text-primary transition-colors focus:outline-none"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="p-4 bg-red-50 border-2 border-red-100 text-red-600 rounded-2xl text-sm font-medium animate-shake">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-4 bg-primary text-white rounded-2xl hover:bg-blue-700 disabled:opacity-50 transition-all font-bold flex items-center justify-center space-x-3 shadow-xl active:scale-95"
                    >
                        {loading ? <Loader className="animate-spin" size={24} /> : <ShieldCheck size={24} />}
                        <span>{loading ? 'Validando...' : 'Iniciar sesión con CASmartS ID'}</span>
                    </button>
                </form>

                <div className="mt-10 text-center">
                    <p className="text-[10px] text-slate-400 uppercase tracking-[0.3em] font-bold">
                        Powered by Casmarts Core & Keycloak
                    </p>
                </div>

                {/* Demo Info */}
                <div className="mt-8 p-6 bg-slate-50 border-2 border-slate-100 rounded-3xl text-xs text-slate-500">
                    <p className="font-bold text-slate-700 mb-3 uppercase tracking-wider">Acceso Demo:</p>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="font-semibold text-primary">Usuario Admin</p>
                            <p>arquiteturacasmarts@gmail.com</p>
                        </div>
                        <div>
                            <p className="font-semibold text-blue-500">Usuario Demo</p>
                            <p>demo@casmarts.com</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
