import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Navigation from './components/Navigation'
import ChatPage from './pages/ChatPage'
import LoginPage from './pages/LoginPage'
import DocumentsPage from './pages/DocumentsPage'
import ResultsPage from './pages/ResultsPage'

function ProtectedRoute({ children }) {
    const { isAuthenticated, token } = useAuthStore()

    if (!isAuthenticated || !token) {
        return <Navigate to="/login" replace />
    }

    return children
}

function AppContent() {
    const { isAuthenticated, token } = useAuthStore()

    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
                path="/*"
                element={
                    <ProtectedRoute>
                        <div className="flex h-screen bg-gray-50">
                            <Navigation />
                            <main className="flex-1 flex flex-col overflow-hidden">
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
        <BrowserRouter>
            <AppContent />
        </BrowserRouter>
    )
}
