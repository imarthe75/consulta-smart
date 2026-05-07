import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useAuth } from 'react-oidc-context'
import { LogOut, MessageSquare, FileText, Search } from 'lucide-react'

export default function Navigation() {
    const location = useLocation()
    const { user, logout } = useAuthStore()
    const auth = useAuth()

    const handleLogout = () => {
        // Clear local store and trigger standard OIDC logout
        logout();
        auth.signoutRedirect();
    }

    const isActive = (path) => location.pathname === path

    const allNavItems = [
        { path: '/', label: 'Chat', icon: MessageSquare },
        { path: '/documentos', label: 'Documentos', icon: FileText, adminOnly: true },
        { path: '/resultados', label: 'Búsqueda', icon: Search, adminOnly: true },
    ]

    const navItems = allNavItems.filter(item => {
        if (!item.adminOnly) return true;
        return user?.role === 'admin';
    })

    return (
        <nav className="w-64 bg-white border-r border-gray-200 flex flex-col">
            {/* Header with Logo */}
            <div className="p-4 border-b border-gray-200">
                <div className="flex items-center space-x-3 mb-3">
                    <img src={`${import.meta.env.BASE_URL}assets/logos/consulta-rpp-logo.svg`} alt="ConsultaRPP" className="w-10 h-10 rounded-lg object-contain" />
                    <div>
                        <h1 className="text-lg font-bold text-primary">ConsultaRPP</h1>
                        <p className="text-xs text-gray-500">Consultas Legales</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="flex-1 p-4 space-y-2">
                {navItems.map(({ path, label, icon: Icon }) => (
                    <Link
                        key={path}
                        to={path}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive(path)
                            ? 'bg-primary text-white'
                            : 'text-gray-700 hover:bg-gray-100'
                            }`}
                    >
                        <Icon size={20} />
                        <span>{label}</span>
                    </Link>
                ))}
            </div>

            {/* User Section */}
            <div className="border-t border-gray-200 p-4">
                <div className="flex items-center justify-between">
                    <div className="flex-1">
                        <p className="text-sm font-medium text-gray-800">
                            {user?.username || 'Usuario'}
                        </p>
                        <p className="text-xs text-gray-500">{user?.email || ''}</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-2 text-gray-600 hover:text-red-600 transition-colors"
                        title="Cerrar sesión"
                    >
                        <LogOut size={20} />
                    </button>
                </div>
            </div>
        </nav>
    )
}
