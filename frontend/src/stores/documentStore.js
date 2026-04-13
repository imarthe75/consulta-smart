import { create } from 'zustand'

export const useDocumentStore = create((set) => ({
    documents: [],
    loading: false,
    error: null,
    uploadProgress: 0,

    setDocuments: (documents) => set({ documents }),

    addDocument: (document) => {
        set((state) => ({
            documents: [...state.documents, document]
        }))
    },

    removeDocument: (documentId) => {
        set((state) => ({
            documents: state.documents.filter(d => d.id !== documentId)
        }))
    },

    setLoading: (loading) => set({ loading }),

    setError: (error) => set({ error }),

    setUploadProgress: (progress) => set({ uploadProgress: progress }),

    clearError: () => set({ error: null }),
}))
