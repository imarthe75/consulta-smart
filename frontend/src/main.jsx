import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import keycloak from './lib/keycloak'

// En una implementación personalizada con formulario, no necesitamos inicializar 
// el adaptador de Keycloak de forma bloqueante si el navegador está en modo inseguro (HTTP).
// El login se manejará vía REST API desde el backend.

const renderApp = () => {
    ReactDOM.createRoot(document.getElementById('root')).render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    )
}

try {
    const isSecure = window.isSecureContext || window.location.protocol === 'https:';
    
    keycloak.init({ 
        onLoad: isSecure ? 'check-sso' : undefined,
        silentCheckSsoRedirectUri: isSecure ? `${window.location.origin}${import.meta.env.BASE_URL}silent-check-sso.html` : undefined,
        pkceMethod: 'S256',
        checkLoginIframe: isSecure // Disable login iframe in insecure context
    }).then(() => {
        renderApp()
    }).catch((error) => {
        console.warn('Keycloak init suppressed (Insecure context or error):', error)
        renderApp()
    })
} catch (e) {
    console.error('Critical failure in Keycloak client:', e)
    renderApp()
}
