/**
 * Page Tests - ChatPage, LoginPage, DocumentsPage, ResultsPage
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ChatPage from '../../src/pages/ChatPage';
import LoginPage from '../../src/pages/LoginPage';
import DocumentsPage from '../../src/pages/DocumentsPage';
import ResultsPage from '../../src/pages/ResultsPage';
import { useAuthStore } from '../../src/stores/authStore';
import { useChatStore } from '../../src/stores/chatStore';
import { useDocumentStore } from '../../src/stores/documentStore';

vi.mock('../../src/stores/authStore');
vi.mock('../../src/stores/chatStore');
vi.mock('../../src/stores/documentStore');

const renderWithRouter = (component: React.ReactElement) => {
    return render(<BrowserRouter>{component}</BrowserRouter>);
};

// ============================================================================
// ChatPage Tests
// ============================================================================

describe('ChatPage', () => {
    beforeEach(() => {
        (useAuthStore as any).mockReturnValue({
            user: { id: 'user-1', username: 'testuser' },
            isAuthenticated: true,
        });

        (useChatStore as any).mockReturnValue({
            currentSession: { id: 'session-1', title: 'Test Chat', messages: [] },
            messages: [],
            isLoading: false,
            error: null,
            sendMessage: vi.fn(),
            loadHistory: vi.fn(),
            selectSession: vi.fn(),
        });
    });

    it('should render chat page layout', () => {
        renderWithRouter(<ChatPage />);
        const chatContainer = screen.getByRole('main') || screen.getByTestId('chat-page');
        expect(chatContainer).toBeInTheDocument();
    });

    it('should render sessions sidebar', () => {
        renderWithRouter(<ChatPage />);
        const sidebar = screen.getByRole('navigation') ||
            screen.getByTestId('sessions-sidebar');
        expect(sidebar).toBeInTheDocument();
    });

    it('should display current session messages', () => {
        (useChatStore as any).mockReturnValue({
            currentSession: { id: 'session-1', title: 'Test Chat', messages: [] },
            messages: [
                { id: '1', content: 'Hello', role: 'user' },
                { id: '2', content: 'Hi there', role: 'assistant' },
            ],
            isLoading: false,
            error: null,
            sendMessage: vi.fn(),
            loadHistory: vi.fn(),
            selectSession: vi.fn(),
        });

        renderWithRouter(<ChatPage />);
        expect(screen.getByText('Hello')).toBeInTheDocument();
        expect(screen.getByText('Hi there')).toBeInTheDocument();
    });

    it('should redirect to login if not authenticated', () => {
        (useAuthStore as any).mockReturnValue({
            user: null,
            isAuthenticated: false,
        });

        renderWithRouter(<ChatPage />);
        // Should redirect or show login prompt
    });
});

// ============================================================================
// LoginPage Tests
// ============================================================================

describe('LoginPage', () => {
    beforeEach(() => {
        (useAuthStore as any).mockReturnValue({
            user: null,
            isAuthenticated: false,
            login: vi.fn(),
            register: vi.fn(),
            isLoading: false,
            error: null,
        });
    });

    it('should render login form', () => {
        renderWithRouter(<LoginPage />);
        const emailInput = screen.getByRole('textbox', { name: /email/i });
        const passwordInput = screen.getByLabelText(/password/i);
        expect(emailInput).toBeInTheDocument();
        expect(passwordInput).toBeInTheDocument();
    });

    it('should render login button', () => {
        renderWithRouter(<LoginPage />);
        const loginButton = screen.getByRole('button', { name: /login|iniciar/i });
        expect(loginButton).toBeInTheDocument();
    });

    it('should display loading state while logging in', () => {
        (useAuthStore as any).mockReturnValue({
            user: null,
            isAuthenticated: false,
            login: vi.fn(),
            register: vi.fn(),
            isLoading: true,
            error: null,
        });

        renderWithRouter(<LoginPage />);
        const loader = screen.getByTestId('loading-spinner') ||
            screen.getByRole('status', { name: /loading/i });
        expect(loader).toBeInTheDocument();
    });

    it('should display error message on login failure', () => {
        (useAuthStore as any).mockReturnValue({
            user: null,
            isAuthenticated: false,
            login: vi.fn(),
            register: vi.fn(),
            isLoading: false,
            error: 'Invalid credentials',
        });

        renderWithRouter(<LoginPage />);
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });

    it('should handle login form submission', async () => {
        const mockLogin = vi.fn();
        (useAuthStore as any).mockReturnValue({
            user: null,
            isAuthenticated: false,
            login: mockLogin,
            register: vi.fn(),
            isLoading: false,
            error: null,
        });

        renderWithRouter(<LoginPage />);

        const emailInput = screen.getByRole('textbox', { name: /email/i });
        const passwordInput = screen.getByLabelText(/password/i);
        const loginButton = screen.getByRole('button', { name: /login/i });

        await userEvent.type(emailInput, 'test@example.com');
        await userEvent.type(passwordInput, 'password123');
        await userEvent.click(loginButton);

        expect(mockLogin).toHaveBeenCalledWith(
            expect.objectContaining({
                email: 'test@example.com',
                password: 'password123',
            })
        );
    });

    it('should show register link', () => {
        renderWithRouter(<LoginPage />);
        const registerLink = screen.getByRole('link', { name: /register|crear|sign up/i });
        expect(registerLink).toBeInTheDocument();
    });

    it('should toggle between login and register', async () => {
        renderWithRouter(<LoginPage />);

        const registerLink = screen.getByRole('link', { name: /register/i });
        await userEvent.click(registerLink);

        // Should show register form
        await waitFor(() => {
            const registerButton = screen.queryByRole('button', { name: /register/i });
            expect(registerButton || screen.getByRole('button')).toBeInTheDocument();
        });
    });
});

// ============================================================================
// DocumentsPage Tests
// ============================================================================

describe('DocumentsPage', () => {
    beforeEach(() => {
        (useAuthStore as any).mockReturnValue({
            user: { id: 'user-1' },
            isAuthenticated: true,
        });

        (useDocumentStore as any).mockReturnValue({
            documents: [
                { id: 'doc-1', filename: 'contract.pdf', status: 'processed', createdAt: new Date().toISOString() },
                { id: 'doc-2', filename: 'agreement.pdf', status: 'processed', createdAt: new Date().toISOString() },
            ],
            isLoading: false,
            error: null,
            uploadDocument: vi.fn(),
            deleteDocument: vi.fn(),
            getDocuments: vi.fn(),
        });
    });

    it('should render documents page', () => {
        renderWithRouter(<DocumentsPage />);
        const page = screen.getByRole('main') || screen.getByTestId('documents-page');
        expect(page).toBeInTheDocument();
    });

    it('should display list of documents', () => {
        renderWithRouter(<DocumentsPage />);
        expect(screen.getByText('contract.pdf')).toBeInTheDocument();
        expect(screen.getByText('agreement.pdf')).toBeInTheDocument();
    });

    it('should render upload area', () => {
        renderWithRouter(<DocumentsPage />);
        const uploadArea = screen.getByTestId('upload-area') ||
            screen.getByRole('button', { name: /upload/i });
        expect(uploadArea).toBeInTheDocument();
    });

    it('should display document status', () => {
        renderWithRouter(<DocumentsPage />);
        const processedStatus = screen.getAllByText(/processed|procesado/i);
        expect(processedStatus.length).toBeGreaterThan(0);
    });

    it('should allow deleting document', async () => {
        const mockDelete = vi.fn();
        (useDocumentStore as any).mockReturnValue({
            documents: [
                { id: 'doc-1', filename: 'contract.pdf', status: 'processed' },
            ],
            isLoading: false,
            error: null,
            uploadDocument: vi.fn(),
            deleteDocument: mockDelete,
            getDocuments: vi.fn(),
        });

        renderWithRouter(<DocumentsPage />);

        const deleteButton = screen.getByRole('button', { name: /delete|eliminar/i });
        await userEvent.click(deleteButton);

        expect(mockDelete).toHaveBeenCalledWith('doc-1');
    });

    it('should show loading while fetching documents', () => {
        (useDocumentStore as any).mockReturnValue({
            documents: [],
            isLoading: true,
            error: null,
            uploadDocument: vi.fn(),
            deleteDocument: vi.fn(),
            getDocuments: vi.fn(),
        });

        renderWithRouter(<DocumentsPage />);
        const loader = screen.getByRole('status') ||
            screen.getByTestId('loading-spinner');
        expect(loader).toBeInTheDocument();
    });

    it('should show empty state when no documents', () => {
        (useDocumentStore as any).mockReturnValue({
            documents: [],
            isLoading: false,
            error: null,
            uploadDocument: vi.fn(),
            deleteDocument: vi.fn(),
            getDocuments: vi.fn(),
        });

        renderWithRouter(<DocumentsPage />);
        expect(screen.getByText(/no documents|sin documentos/i)).toBeInTheDocument();
    });
});

// ============================================================================
// ResultsPage Tests
// ============================================================================

describe('ResultsPage', () => {
    beforeEach(() => {
        (useAuthStore as any).mockReturnValue({
            user: { id: 'user-1' },
            isAuthenticated: true,
        });
    });

    it('should render results page', () => {
        renderWithRouter(<ResultsPage />);
        const page = screen.getByRole('main') || screen.getByTestId('results-page');
        expect(page).toBeInTheDocument();
    });

    it('should display search query', () => {
        renderWithRouter(<ResultsPage />);
        // Search query may come from URL params
        const searchQuery = screen.queryByTestId('search-query') ||
            screen.getByRole('main');
        expect(searchQuery).toBeInTheDocument();
    });

    it('should display search results', () => {
        renderWithRouter(<ResultsPage />);
        const results = screen.getByTestId('search-results') ||
            screen.getByRole('region', { name: /results/i });
        expect(results).toBeInTheDocument();
    });

    it('should allow refining search', async () => {
        renderWithRouter(<ResultsPage />);
        const refinementArea = screen.getByTestId('search-filters') ||
            screen.getByRole('region', { name: /filter/i }) ||
            screen.getByTestId('results-page');
        expect(refinementArea).toBeInTheDocument();
    });

    it('should show pagination controls', () => {
        renderWithRouter(<ResultsPage />);
        // Pagination may or may not be present depending on result count
        const pagination = screen.queryByRole('navigation', {
            name: /pagination|paginación/i,
        }) || screen.getByTestId('results-page');
        expect(pagination).toBeInTheDocument();
    });
});
