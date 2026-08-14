import { create } from 'zustand'

export const useDocumentStore = create((set) => ({
    documents: [],
    loading: false,
    error: null,
    uploadProgress: 0,

    // Acepta un array directo O una función actualizadora (state => newState), igual
    // que React.setState -- DocumentUpload.jsx::handleReindex la llama como
    // setDocuments(prev => prev.map(...)), lo cual con un setter plano guardaba la
    // función misma como valor de `documents` en vez del array mapeado.
    setDocuments: (documentsOrUpdater) => set((state) => ({
        documents: typeof documentsOrUpdater === 'function'
            ? documentsOrUpdater(state.documents)
            : documentsOrUpdater
    })),

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
