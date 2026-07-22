import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from 'react-oidc-context'
import { Log } from 'oidc-client-ts'
import { useAuthStore } from './stores/authStore'
import Navigation from './components/Navigation'
import ChatPage from './pages/ChatPage'
import LoginPage from './pages/LoginPage'
import WidgetPage from './pages/WidgetPage'
import DocumentsPage from './pages/DocumentsPage'
import ResultsPage from './pages/ResultsPage'
import AdminPage from './pages/AdminPage'


const baseUrl = window.location.origin + import.meta.env.BASE_URL
const oidcConfig = {
    authority: "https://auth.casmart.internal/application/o/consulta-smart/",
    client_id: "consulta-smart",
    redirect_uri: baseUrl,
    post_logout_redirect_uri: baseUrl,
    response_type: "code",
    scope: "openid profile email",
    automaticSilentRenew: false,
    monitorSession: false,
    loadUserInfo: true,  // Load user info for better session handling
    staleStateInSeconds: 300,  // Validate state within 5 minutes
    onSigninCallback: (_user) => {
        // Clear the URL parameters (code, state) after successful login
        window.history.replaceState(
            {},
            document.title,
            window.location.pathname
        );
    }
}


import WidgetIntegrationPage from './pages/WidgetIntegrationPage'
import DocumentationPage from './pages/DocumentationPage'

function ProtectedRoute({ children }) {
    const auth = useAuth()
    const { login } = useAuthStore()

    // Sync to local store when authenticated
    React.useEffect(() => {
        if (auth.isAuthenticated && auth.user) {
            login(auth.user.profile, auth.user.access_token)
        }
    }, [auth.isAuthenticated, auth.user, login])

    if (auth.isLoading) {
        return (
            <div className="flex h-screen w-screen items-center justify-center bg-[#0f172a] relative overflow-hidden font-sans">
                {/* Background Blobs for Premium Feel */}
                <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
                    <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]"></div>
                    <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/5 rounded-full blur-[100px]"></div>
                </div>
                <div className="flex flex-col items-center gap-4 text-white relative z-10">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-400"></div>
                    <p className="font-semibold animate-pulse text-blue-400 tracking-wider text-sm">Sincronizando Identidad CASMARTS...</p>
                </div>
            </div>
        )
    }

    if (!auth.isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return children
}

function AppContent() {
    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/widget" element={<WidgetPage />} />
            <Route
                path="/*"
                element={
                    <ProtectedRoute>
                        <div className="h-screen w-full bg-white flex">
                            <Navigation />
                            <main className="flex-1 h-full overflow-y-auto">
                                <Routes>
                                    <Route path="/" element={<ChatPage />} />
                                    <Route path="/documentos" element={<DocumentsPage />} />
                                    <Route path="/guia-widget" element={<WidgetIntegrationPage />} />
                                    <Route path="/documentacion" element={<DocumentationPage />} />
                                    <Route path="/resultados" element={<ResultsPage />} />
                                    <Route path="/admin" element={<AdminPage />} />
                                </Routes>
                            </main>
                        </div>
                    </ProtectedRoute>
                }
            />
        </Routes>
    )
}

export default function App() {
    return (
        <AuthProvider {...oidcConfig}>
            <BrowserRouter 
                basename={import.meta.env.BASE_URL}
                future={{
                    v7_startTransition: true,
                    v7_relativeSplatPath: true,
                }}
            >
                <AppContent />
            </BrowserRouter>
        </AuthProvider>
    )
}

