import { create } from 'zustand'

const getSavedToken = () => {
    try {
        return typeof window !== 'undefined' ? localStorage.getItem('token') : null
    } catch (error) {
        return null
    }
}

const savedToken = getSavedToken()

export const useAuthStore = create((set) => ({
    isAuthenticated: !!savedToken,
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
