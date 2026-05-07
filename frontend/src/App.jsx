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

const baseUrl = window.location.origin + import.meta.env.BASE_URL
const oidcConfig = {
    authority: window.location.origin + "/application/o/consulta-smart/",
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


function ProtectedRoute({ children }) {
    const auth = useAuth()
    const { login } = useAuthStore()

    // Sync to local store when authenticated
    React.useEffect(() => {
        console.log("Auth State Changed:", {
            isLoading: auth.isLoading,
            isAuthenticated: auth.isAuthenticated,
            error: auth.error?.message,
            pathname: window.location.pathname
        });

        if (auth.isAuthenticated && auth.user) {
            login(auth.user.profile, auth.user.access_token)
        }

        // CRITICAL FIX: If we cleared our local token but OIDC still thinks it's auth, force it to clear
        // This only runs if we are authenticated but DON'T have a token even after trying to login above
        if (!localStorage.getItem('token') && auth.isAuthenticated && !auth.isLoading) {
            console.warn("Session Mismatch Detected: Token missing but OIDC authenticated. Clearing OIDC user.");
            if (auth.removeUser) auth.removeUser();
            return;
        }
    }, [auth.isAuthenticated, auth.user, auth.isLoading, auth.error, login])

    if (auth.isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-textmain text-white font-sans">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primaryLight mb-4 mx-auto"></div>
                    <p className="text-xs uppercase tracking-widest opacity-50">Sincronizando Identidad...</p>
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
                        <div className="h-screen w-full bg-white">
                            <main className="h-full w-full overflow-hidden">
                                <Routes>
                                    <Route path="/" element={<ChatPage />} />
                                    <Route path="/documentos" element={<DocumentsPage />} />
                                    <Route path="/resultados" element={<ResultsPage />} />
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
            <BrowserRouter basename={import.meta.env.BASE_URL}>
                <AppContent />
            </BrowserRouter>
        </AuthProvider>
    )
}

