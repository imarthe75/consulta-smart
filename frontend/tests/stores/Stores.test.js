/**
 * Store Tests - Zustand Store Testing
 * authStore, chatStore, documentStore
 *
 * HALLAZGO (auditoría 2026-07-29, TEST-001): la versión anterior de este archivo redefinía
 * cada store como `vi.fn(() => ({ ...forma falsa... }))` en vez de importar el store real —
 * las 100+ aserciones pasaban sin ejecutar ni una sola línea del código real de
 * src/stores/*.js. Se reescribió para importar y ejercitar la implementación real.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'

// ============================================================================
// Auth Store Tests
// ============================================================================

describe('authStore', () => {
    // authAPI se mockea para controlar exactamente qué "rol real" devuelve el backend,
    // sin depender de una API viva — el store solo debe confiar en esta respuesta, nunca
    // en el contenido del email/username del usuario (ver hallazgo de backdoor eliminado
    // documentado en el propio src/stores/authStore.js).
    vi.mock('../../src/services/api', () => ({
        authAPI: {
            me: vi.fn(),
            guestLogin: vi.fn(),
        },
    }))

    beforeEach(() => {
        localStorage.clear()
        vi.clearAllMocks()
        vi.resetModules()
    })

    it('arranca sin sesión si no hay token guardado', async () => {
        const { useAuthStore } = await import('../../src/stores/authStore')
        const state = useAuthStore.getState()
        expect(state.isAuthenticated).toBe(false)
        expect(state.token).toBeNull()
        expect(state.user).toBeNull()
    })

    it('login() NUNCA otorga el rol admin por el contenido del email/username (regresión del backdoor de escalación de privilegios eliminado)', async () => {
        const { authAPI } = await import('../../src/services/api')
        authAPI.me.mockRejectedValue(new Error('network error'))
        const { useAuthStore } = await import('../../src/stores/authStore')

        // Un email que contenga literalmente "admin" no debe bastar para escalar el rol.
        useAuthStore.getState().login({ email: 'admin@empresa.com', username: 'admin' }, 'fake-token')

        const state = useAuthStore.getState()
        expect(state.isAuthenticated).toBe(true)
        expect(state.token).toBe('fake-token')
        expect(state.user.role).toBe('user')
    })

    it('login() solo asigna el rol admin cuando authAPI.me() lo confirma explícitamente', async () => {
        const { authAPI } = await import('../../src/services/api')
        authAPI.me.mockResolvedValue({ data: { roles: ['admin'] } })
        const { useAuthStore } = await import('../../src/stores/authStore')

        useAuthStore.getState().login({ email: 'real-admin@empresa.com' }, 'fake-token')
        await new Promise((resolve) => setTimeout(resolve, 0))

        expect(useAuthStore.getState().user.role).toBe('admin')
    })

    it('login() conserva el rol provisional "user" (fail-closed) si authAPI.me() falla', async () => {
        const { authAPI } = await import('../../src/services/api')
        authAPI.me.mockRejectedValue(new Error('401 unauthorized'))
        const { useAuthStore } = await import('../../src/stores/authStore')

        useAuthStore.getState().login({ email: 'x@empresa.com' }, 'fake-token')
        await new Promise((resolve) => setTimeout(resolve, 0))

        expect(useAuthStore.getState().user.role).toBe('user')
    })

    it('login() persiste el token en localStorage', async () => {
        const { authAPI } = await import('../../src/services/api')
        authAPI.me.mockRejectedValue(new Error('network error'))
        const { useAuthStore } = await import('../../src/stores/authStore')

        useAuthStore.getState().login({ email: 'x@empresa.com' }, 'token-123')

        // localStorage está mockeado globalmente en tests/setup.ts (vi.fn() por método, sin
        // almacenamiento real); se verifica la llamada, no un getItem() posterior.
        expect(localStorage.setItem).toHaveBeenCalledWith('token', 'token-123')
    })

    it('logout() limpia el estado y llama a localStorage.removeItem', async () => {
        const { authAPI } = await import('../../src/services/api')
        authAPI.me.mockRejectedValue(new Error('network error'))
        const { useAuthStore } = await import('../../src/stores/authStore')

        useAuthStore.getState().login({ email: 'x@empresa.com' }, 'token-123')
        useAuthStore.getState().logout()

        const state = useAuthStore.getState()
        expect(state.isAuthenticated).toBe(false)
        expect(state.user).toBeNull()
        expect(state.token).toBeNull()
        expect(localStorage.removeItem).toHaveBeenCalledWith('token')
    })
})

// ============================================================================
// Chat Store Tests
// ============================================================================

describe('chatStore', () => {
    let useChatStore

    beforeEach(async () => {
        vi.resetModules()
        ;({ useChatStore } = await import('../../src/stores/chatStore'))
        useChatStore.setState({
            sessions: [],
            currentSessionId: null,
            messages: [],
            loading: false,
            error: null,
        })
    })

    it('arranca con estado vacío', () => {
        const state = useChatStore.getState()
        expect(state.sessions).toEqual([])
        expect(state.messages).toEqual([])
        expect(state.currentSessionId).toBeNull()
    })

    it('addMessage agrega al final sin mutar el arreglo previo', () => {
        const { addMessage } = useChatStore.getState()
        addMessage({ role: 'user', content: 'hola' })
        addMessage({ role: 'assistant', content: 'hola, ¿en qué puedo ayudarte?' })

        const { messages } = useChatStore.getState()
        expect(messages).toHaveLength(2)
        expect(messages[0].content).toBe('hola')
        expect(messages[1].role).toBe('assistant')
    })

    it('clearMessages vacía el historial sin afectar sessions', () => {
        useChatStore.getState().setSessions([{ id: 's1' }])
        useChatStore.getState().addMessage({ role: 'user', content: 'hola' })

        useChatStore.getState().clearMessages()

        const state = useChatStore.getState()
        expect(state.messages).toEqual([])
        expect(state.sessions).toEqual([{ id: 's1' }])
    })

    it('setLoading y setError actualizan el estado independientemente', () => {
        useChatStore.getState().setLoading(true)
        expect(useChatStore.getState().loading).toBe(true)

        useChatStore.getState().setError('algo falló')
        expect(useChatStore.getState().error).toBe('algo falló')
        expect(useChatStore.getState().loading).toBe(true)

        useChatStore.getState().clearError()
        expect(useChatStore.getState().error).toBeNull()
    })

    it('setCurrentSession actualiza el id de sesión activa', () => {
        useChatStore.getState().setCurrentSession('session-42')
        expect(useChatStore.getState().currentSessionId).toBe('session-42')
    })
})

// ============================================================================
// Document Store Tests
// ============================================================================

describe('documentStore', () => {
    let useDocumentStore

    beforeEach(async () => {
        vi.resetModules()
        ;({ useDocumentStore } = await import('../../src/stores/documentStore'))
        useDocumentStore.setState({
            documents: [],
            loading: false,
            error: null,
            uploadProgress: 0,
        })
    })

    it('arranca con estado vacío', () => {
        const state = useDocumentStore.getState()
        expect(state.documents).toEqual([])
        expect(state.uploadProgress).toBe(0)
    })

    it('addDocument agrega sin duplicar el arreglo previo', () => {
        useDocumentStore.getState().addDocument({ id: 'doc-1', filename: 'a.pdf' })
        useDocumentStore.getState().addDocument({ id: 'doc-2', filename: 'b.pdf' })

        expect(useDocumentStore.getState().documents).toHaveLength(2)
    })

    it('removeDocument elimina solo el documento indicado', () => {
        useDocumentStore.getState().setDocuments([
            { id: 'doc-1' }, { id: 'doc-2' }, { id: 'doc-3' },
        ])

        useDocumentStore.getState().removeDocument('doc-2')

        const ids = useDocumentStore.getState().documents.map((d) => d.id)
        expect(ids).toEqual(['doc-1', 'doc-3'])
    })

    it('setUploadProgress y clearError actualizan el estado', () => {
        useDocumentStore.getState().setUploadProgress(42)
        expect(useDocumentStore.getState().uploadProgress).toBe(42)

        useDocumentStore.getState().setError('fallo de subida')
        expect(useDocumentStore.getState().error).toBe('fallo de subida')

        useDocumentStore.getState().clearError()
        expect(useDocumentStore.getState().error).toBeNull()
    })
})
