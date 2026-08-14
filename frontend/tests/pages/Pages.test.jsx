/**
 * Page Tests - ChatPage, LoginPage, DocumentsPage, ResultsPage
 *
 * Reescrito 2026-08-14: la versión anterior probaba páginas imaginarias --
 * un LoginPage con formulario email/password + link de registro (el real usa
 * SSO vía Authentik/OIDC, botón único "INICIAR SESIÓN CON CASMARTS ID"), un
 * DocumentsPage con acciones de store `uploadDocument/deleteDocument` (el
 * real delega todo a `DocumentUpload`, que sube directo vía `api`), y un
 * ResultsPage/ChatPage con props/store que no coinciden con los componentes
 * reales. Ver `src/pages/*.jsx`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ChatPage from '../../src/pages/ChatPage';
import LoginPage from '../../src/pages/LoginPage';
import DocumentsPage from '../../src/pages/DocumentsPage';
import ResultsPage from '../../src/pages/ResultsPage';
import { useChatStore } from '../../src/stores/chatStore';
import { useDocumentStore } from '../../src/stores/documentStore';
import { useAuth } from 'react-oidc-context';
import api from '../../src/services/api';

vi.mock('../../src/stores/chatStore', () => ({
    useChatStore: vi.fn(),
}));

vi.mock('../../src/stores/documentStore', () => ({
    useDocumentStore: vi.fn(),
}));

vi.mock('react-oidc-context', () => ({
    useAuth: vi.fn(),
}));

vi.mock('../../src/services/api', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
        delete: vi.fn(),
    },
    chatAPI: {
        getSessions: vi.fn(() => Promise.resolve({ data: { data: [] } })),
        getSession: vi.fn(() => Promise.reject(new Error('no aplica en este test'))),
        createSession: vi.fn(() => Promise.resolve({ data: { data: { id: 'sesion-1' } } })),
        sendQuery: vi.fn(() => Promise.resolve({ data: { data: { response: 'ok', sources: [] } } })),
    },
    searchAPI: {
        search: vi.fn(() => Promise.resolve({ data: { data: [] } })),
    },
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

const renderWithRouter = (component) => {
    return render(<MemoryRouter>{component}</MemoryRouter>);
};

// ============================================================================
// ChatPage Tests -- wrapper delgado sobre ChatInterface (cobertura completa
// de ChatInterface en tests/components/ChatInterface.test.jsx)
// ============================================================================

describe('ChatPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.mockReturnValue({
            messages: [],
            loading: false,
            error: null,
            addMessage: vi.fn(),
            setMessages: vi.fn(),
            setLoading: vi.fn(),
            setError: vi.fn(),
            clearMessages: vi.fn(),
        });
        // ChatInterface.jsx también lee `documents` de useDocumentStore (lista
        // de documentos indexados disponibles para citar) -- sin este mock
        // vi.fn() no devuelve nada y el destructuring revienta el render.
        useDocumentStore.mockReturnValue({ documents: [] });
        api.get.mockImplementation((url) => {
            if (url === 'admin/chatbot/profiles') return Promise.resolve({ data: [] });
            if (url.startsWith('chat/profiles/')) {
                return Promise.resolve({ data: { title: 'Asistente', welcome_message: 'Hola' } });
            }
            return Promise.reject(new Error('URL no mockeada: ' + url));
        });
    });

    it('should render the chat input from ChatInterface', async () => {
        renderWithRouter(<ChatPage />);
        expect(await screen.findByPlaceholderText('Escribe tu consulta aquí...')).toBeInTheDocument();
    });

    it('should display messages from the chat store', async () => {
        useChatStore.mockReturnValue({
            messages: [{ role: 'user', content: 'Hola', timestamp: new Date().toISOString() }],
            loading: false,
            error: null,
            addMessage: vi.fn(),
            setMessages: vi.fn(),
            setLoading: vi.fn(),
            setError: vi.fn(),
            clearMessages: vi.fn(),
        });

        renderWithRouter(<ChatPage />);
        expect(await screen.findByText('Hola')).toBeInTheDocument();
    });
});

// ============================================================================
// LoginPage Tests -- SSO vía Authentik/OIDC (react-oidc-context), no hay
// formulario local de email/password ni registro.
// ============================================================================

describe('LoginPage', () => {
    const signinRedirectMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        useAuth.mockReturnValue({
            isLoading: false,
            isAuthenticated: false,
            error: null,
            signinRedirect: signinRedirectMock,
        });
    });

    it('should render the SSO login button', () => {
        renderWithRouter(<LoginPage />);
        expect(screen.getByRole('button', { name: /iniciar sesión con casmarts id/i })).toBeInTheDocument();
    });

    it('should call signinRedirect() when the button is clicked', async () => {
        const user = userEvent.setup();
        renderWithRouter(<LoginPage />);

        await user.click(screen.getByRole('button', { name: /iniciar sesión con casmarts id/i }));

        expect(signinRedirectMock).toHaveBeenCalled();
    });

    it('should show a connecting state and disable the button while OIDC is loading', () => {
        useAuth.mockReturnValue({
            isLoading: true,
            isAuthenticated: false,
            error: null,
            signinRedirect: signinRedirectMock,
        });

        renderWithRouter(<LoginPage />);
        expect(screen.getByText(/conectando/i)).toBeInTheDocument();
        expect(screen.getByRole('button')).toBeDisabled();
    });

    it('should show the SSL certificate help when OIDC reports an error', () => {
        useAuth.mockReturnValue({
            isLoading: false,
            isAuthenticated: false,
            error: new Error('certificate error'),
            signinRedirect: signinRedirectMock,
        });

        renderWithRouter(<LoginPage />);
        expect(screen.getByText(/certificado ssl interno/i)).toBeInTheDocument();
    });
});

// ============================================================================
// DocumentsPage Tests -- delega la subida/lista real a DocumentUpload
// (cobertura completa en tests/components/DocumentUpload.test.jsx); aquí solo
// se cubre el filtro de aplicativo/tenant propio de esta página.
// ============================================================================

describe('DocumentsPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useDocumentStore.mockReturnValue({
            documents: [],
            loading: false,
            error: null,
            uploadProgress: 0,
            setDocuments: vi.fn(),
            setLoading: vi.fn(),
            setError: vi.fn(),
            setUploadProgress: vi.fn(),
            clearError: vi.fn(),
        });
        api.get.mockImplementation((url) => {
            if (url === 'admin/chatbot/profiles') {
                return Promise.resolve({
                    data: [{ id: 'centinela-ai', name: 'Centinela-AI' }, { id: 'rpp', name: 'RPP' }],
                });
            }
            if (url === 'admin/chatbot/documents') return Promise.resolve({ data: [] });
            return Promise.reject(new Error('URL no mockeada: ' + url));
        });
    });

    it('should render the module banner and the tenant filter', async () => {
        renderWithRouter(<DocumentsPage />);
        expect(screen.getByText('Documentos de Soporte RAG')).toBeInTheDocument();
        expect(await screen.findByText('Todos los Aplicativos (Global)')).toBeInTheDocument();
    });

    it('should populate the tenant filter from the real chatbot profiles', async () => {
        renderWithRouter(<DocumentsPage />);
        // El mismo perfil aparece en 2 selects independientes en esta página: el
        // filtro propio de DocumentsPage y el selector interno de DocumentUpload.
        expect((await screen.findAllByText('Centinela-AI (centinela-ai)')).length).toBeGreaterThan(0);
        expect(screen.getAllByText('RPP (rpp)').length).toBeGreaterThan(0);
    });

    it('should filter documents by tenant when a profile is selected', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DocumentsPage />);

        await screen.findAllByText('Centinela-AI (centinela-ai)');
        api.get.mockClear();

        const select = screen.getByDisplayValue('Todos los Aplicativos (Global)');
        await user.selectOptions(select, 'centinela-ai');

        // DocumentUpload reacciona al cambio de `tenantId` re-consultando documentos.
        await waitFor(() => {
            expect(api.get).toHaveBeenCalledWith('admin/chatbot/documents');
        });
    });
});

// ============================================================================
// ResultsPage Tests
// ============================================================================

describe('ResultsPage', () => {
    it('should render the module banner and the search form', () => {
        renderWithRouter(<ResultsPage />);
        expect(screen.getByText('Búsqueda de Documentos')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Busca en documentos...')).toBeInTheDocument();
    });

    it('should show the empty state before searching', () => {
        renderWithRouter(<ResultsPage />);
        expect(screen.getByPlaceholderText('Busca en documentos...')).toHaveValue('');
    });
});
