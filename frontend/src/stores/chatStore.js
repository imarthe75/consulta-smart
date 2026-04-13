import { create } from 'zustand'

export const useChatStore = create((set, get) => ({
    sessions: [],
    currentSessionId: null,
    messages: [],
    loading: false,
    error: null,

    setSessions: (sessions) => set({ sessions }),

    setCurrentSession: (sessionId) => {
        set({ currentSessionId: sessionId })
    },

    addMessage: (message) => {
        set((state) => ({
            messages: [...state.messages, message]
        }))
    },

    setMessages: (messages) => set({ messages }),

    setLoading: (loading) => set({ loading }),

    setError: (error) => set({ error }),

    clearMessages: () => set({ messages: [] }),

    clearError: () => set({ error: null }),
}))
