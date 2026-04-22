import { create } from 'zustand'
import keycloak from '../lib/keycloak'

const getSavedToken = () => {
    if (keycloak.token) return keycloak.token
    try {
        return typeof window !== 'undefined' ? localStorage.getItem('token') : null
    } catch (error) {
        return null
    }
}

const savedToken = getSavedToken()

export const useAuthStore = create((set) => ({
    isAuthenticated: !!savedToken,  // Init as true if token exists
    user: null,
    token: savedToken || null,

    login: (user, token) => {
        set({ isAuthenticated: true, user, token })
    },

    logout: () => {
        if (keycloak.authenticated) {
            keycloak.logout()
        } else {
            localStorage.removeItem('token')
            set({ isAuthenticated: false, user: null, token: null })
        }
    },

    setUser: (user) => set({ user }),
    setAuthenticated: (isAuth) => set({ isAuthenticated: isAuth }),
    
    guestLogin: async () => {
        try {
            const { authAPI } = await import('../services/api')
            const response = await authAPI.guestLogin()
            const { access_token, user_id, email, role } = response.data
            localStorage.setItem('token', access_token)
            set({ 
                isAuthenticated: true, 
                user: { id: user_id, email, role }, 
                token: access_token 
            })
            return response.data
        } catch (error) {
            console.error('Guest login failed:', error)
            throw error
        }
    }
}))
