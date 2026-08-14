/**
 * Navigation Component Tests
 *
 * Reescrito 2026-08-14: la versión anterior probaba una Navigation imaginaria
 * (botón de login/logout condicional a `isAuthenticated`, sin sidebar) que no
 * coincidía con el componente real -- un sidebar fijo con enlaces, selector de
 * tema y sesión resuelta vía Authentik/OIDC (`react-oidc-context`), no un login
 * local por email/password. Ver `src/components/Navigation.jsx`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Navigation from '../../src/components/Navigation';
import { useAuthStore } from '../../src/stores/authStore';
import { useAuth } from 'react-oidc-context';

vi.mock('../../src/stores/authStore', () => ({
    useAuthStore: vi.fn(),
}));

vi.mock('react-oidc-context', () => ({
    useAuth: vi.fn(),
}));

const renderWithRouter = (component) => {
    return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Navigation Component', () => {
    const logoutMock = vi.fn();
    const signoutRedirectMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        useAuthStore.mockReturnValue({
            user: { id: 'user-1', username: 'testuser', email: 'testuser@example.com' },
            logout: logoutMock,
        });
        useAuth.mockReturnValue({
            signoutRedirect: signoutRedirectMock,
        });
    });

    describe('Rendering', () => {
        it('should display app title', () => {
            renderWithRouter(<Navigation />);
            expect(screen.getByText('Consulta Smart')).toBeInTheDocument();
        });

        it('should render the username from the store', () => {
            renderWithRouter(<Navigation />);
            expect(screen.getByText('testuser')).toBeInTheDocument();
        });

        it('should fall back to "Usuario" when there is no username', () => {
            useAuthStore.mockReturnValue({
                user: { id: 'user-1', email: 'sin-username@example.com' },
                logout: logoutMock,
            });
            renderWithRouter(<Navigation />);
            expect(screen.getByText('Usuario')).toBeInTheDocument();
        });

        it('should display the user email', () => {
            renderWithRouter(<Navigation />);
            expect(screen.getByText('testuser@example.com')).toBeInTheDocument();
        });
    });

    describe('Navigation Links', () => {
        it('should render the chat link', () => {
            renderWithRouter(<Navigation />);
            const chatLink = screen.getByRole('link', { name: /chat/i });
            expect(chatLink).toHaveAttribute('href', '/');
        });

        it('should render the documents link', () => {
            renderWithRouter(<Navigation />);
            const docsLink = screen.getByRole('link', { name: /documentos rag/i });
            expect(docsLink).toHaveAttribute('href', '/documentos');
        });

        it('should render the administration link', () => {
            renderWithRouter(<Navigation />);
            const adminLink = screen.getByRole('link', { name: /administración/i });
            expect(adminLink).toHaveAttribute('href', '/admin');
        });
    });

    describe('Logout', () => {
        it('should call store logout() and OIDC signoutRedirect() when the logout button is clicked', async () => {
            renderWithRouter(<Navigation />);
            const logoutButton = screen.getByTitle('Cerrar sesión');

            await userEvent.click(logoutButton);

            expect(logoutMock).toHaveBeenCalled();
            expect(signoutRedirectMock).toHaveBeenCalled();
        });
    });

    describe('Theme Selector', () => {
        it('should render the theme selector with the 3 expected options', () => {
            renderWithRouter(<Navigation />);
            expect(screen.getByText('Sistema (Automático)')).toBeInTheDocument();
            expect(screen.getByText('Modo Claro')).toBeInTheDocument();
            expect(screen.getByText('Modo Oscuro')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('should expose a navigation landmark', () => {
            renderWithRouter(<Navigation />);
            expect(screen.getByRole('navigation')).toBeInTheDocument();
        });
    });
});
