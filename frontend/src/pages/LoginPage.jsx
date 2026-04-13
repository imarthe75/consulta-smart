import React, { useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { authAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, Loader } from 'lucide-react'

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [username, setUsername] = useState('')
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
                    <h1 className="text-4xl font-bold text-primary mb-2">ConsultaRPP</h1>
                    <p className="text-gray-600">Sistema Inteligente de Consultas Legales</p>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Email */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Correo Electrónico
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                placeholder="tu@email.com"
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                    </div>

                    {/* Username (Solo para registro) */}
                    {!isLogin && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Nombre de Usuario
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                placeholder="usuario123"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                    )}

                    {/* Password */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Contraseña
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                placeholder="••••••••"
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium flex items-center justify-center space-x-2"
                    >
                        {loading && <Loader className="animate-spin" size={20} />}
                        <span>{isLogin ? 'Iniciar sesión' : 'Registrarse'}</span>
                    </button>
                </form>

                {/* Toggle */}
                <div className="mt-6 text-center">
                    <p className="text-gray-600 text-sm">
                        {isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}{' '}
                        <button
                            onClick={() => {
                                setIsLogin(!isLogin)
                                setError(null)
                            }}
                            className="text-primary hover:underline font-medium"
                        >
                            {isLogin ? 'Registrarse' : 'Inicia sesión'}
                        </button>
                    </p>
                </div>

                {/* Demo Info */}
                <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                    <p className="font-semibold mb-2">Demo Credentials:</p>
                    <p>Email: demo@example.com</p>
                    <p>Password: password123</p>
                </div>
            </div>
        </div>
    )
}
