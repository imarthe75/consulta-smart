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
        // Rol provisional ('user') hasta resolver el rol real contra el backend.
        set({ isAuthenticated: true, user: { ...user, role: user?.role || 'user' }, token })

        // El rol real SIEMPRE se resuelve consultando al backend (tabla `users`,
        // fuente de verdad), nunca adivinando por substring en email/username del
        // perfil OIDC. Ver hallazgo de auditoría: aquí existía un backdoor de
        // escalación de privilegios que otorgaba 'admin' a cualquier cuenta cuyo
        // email/username contuviera ciertas substrings — fue eliminado.
        import('../services/api').then(({ authAPI }) => {
            authAPI.me()
                .then((res) => {
                    const roles = res.data?.roles || []
                    set((state) => ({
                        user: { ...state.user, role: roles.includes('admin') ? 'admin' : 'user' }
                    }))
                })
                .catch(() => {
                    // Si falla la resolución de rol, se conserva el rol provisional 'user'
                    // (fail-closed: nunca se asume admin por defecto).
                })
        })
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
