import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useAuth } from 'react-oidc-context'
import { LogOut, MessageSquare, FileText, Search, SunMoon } from 'lucide-react'
import { CivikaThemeManager } from '../lib/CivikaThemeManager'

export default function Navigation() {
    const location = useLocation()
    const { user, logout } = useAuthStore()
    const auth = useAuth()

    const themeManager = React.useMemo(() => new CivikaThemeManager(), [])
    const [currentTheme, setCurrentTheme] = React.useState('system')

    React.useEffect(() => {
        setCurrentTheme(themeManager.getStoredTheme())
    }, [themeManager])

    const handleThemeChange = (e) => {
        const selected = e.target.value
        themeManager.setTheme(selected)
        setCurrentTheme(selected)
    }

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
        <nav className="w-64 bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 flex flex-col transition-colors duration-150">
            {/* Header with Logo */}
            <div className="p-4 border-b border-gray-200 dark:border-slate-800">
                <div className="flex items-center space-x-3 mb-3">
                    <img src={`${import.meta.env.BASE_URL}assets/logos/consulta-rpp-logo.svg`} alt="ConsultaRPP" className="w-10 h-10 rounded-lg object-contain" />
                    <div>
                        <h1 className="text-lg font-bold text-primary dark:text-blue-400">ConsultaRPP</h1>
                        <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Consultas Legales</p>
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
                            ? 'bg-primary text-white dark:bg-blue-600'
                            : 'text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800'
                            }`}
                    >
                        <Icon size={20} />
                        <span>{label}</span>
                    </Link>
                ))}
            </div>

            {/* Selector de Tema */}
            <div className="border-t border-gray-200 dark:border-slate-800 p-4">
                <div className="flex items-center space-x-2 text-gray-700 dark:text-slate-300 mb-2">
                    <SunMoon size={16} className="text-slate-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider">Tema Visual</span>
                </div>
                <select
                    value={currentTheme}
                    onChange={handleThemeChange}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg px-3 py-2 text-xs font-medium text-gray-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-blue-500 cursor-pointer"
                >
                    <option value="system">Sistema (Automático)</option>
                    <option value="light">Modo Claro</option>
                    <option value="dark">Modo Oscuro</option>
                </select>
            </div>

            {/* User Section */}
            <div className="border-t border-gray-200 dark:border-slate-800 p-4 bg-slate-50/50 dark:bg-slate-950/20">
                <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0 mr-2">
                        <p className="text-sm font-semibold text-gray-800 dark:text-slate-200 truncate">
                            {user?.username || 'Usuario'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{user?.email || ''}</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-2 text-gray-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                        title="Cerrar sesión"
                    >
                        <LogOut size={20} />
                    </button>
                </div>
            </div>
        </nav>
    )
}
