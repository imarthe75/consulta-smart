import { create } from 'zustand'

// Inicializar de forma segura
const getSavedToken = () => {
    try {
        return typeof window !== 'undefined' ? localStorage.getItem('token') : null
    } catch (error) {
        console.error('Error reading localStorage:', error)
        return null
    }
}

const savedToken = getSavedToken()

export const useAuthStore = create((set) => ({
    isAuthenticated: !!savedToken,  // Init as true if token exists
    user: null,
    token: savedToken || null,

    login: (user, token) => {
        localStorage.setItem('token', token)
        set({ isAuthenticated: true, user, token })
    },

    logout: () => {
        localStorage.removeItem('token')
        set({ isAuthenticated: false, user: null, token: null })
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
