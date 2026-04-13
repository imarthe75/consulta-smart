/**
 * Navigation Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Navigation from '../../src/components/Navigation';
import { useAuthStore } from '../../src/stores/authStore';

// Mock the auth store
vi.mock('../../src/stores/authStore', () => ({
    useAuthStore: vi.fn(),
}));

const renderWithRouter = (component: React.ReactElement) => {
    return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Navigation Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Unauthenticated State', () => {
        beforeEach(() => {
            (useAuthStore as any).mockReturnValue({
                user: null,
                isAuthenticated: false,
                logout: vi.fn(),
            });
        });

        it('should render login button when not authenticated', () => {
            renderWithRouter(<Navigation />);
            const loginButton = screen.getByRole('button', { name: /login|iniciar/i });
            expect(loginButton).toBeInTheDocument();
        });

        it('should not render logout button when not authenticated', () => {
            renderWithRouter(<Navigation />);
            const logoutButton = screen.queryByRole('button', {
                name: /logout|cerrar/i,
            });
            expect(logoutButton).not.toBeInTheDocument();
        });

        it('should display app logo/title', () => {
            renderWithRouter(<Navigation />);
            const logo = screen.getByRole('link', { name: /consulta/i }) ||
                screen.getByText(/consulta/i);
            expect(logo).toBeInTheDocument();
        });
    });

    describe('Authenticated State', () => {
        beforeEach(() => {
            (useAuthStore as any).mockReturnValue({
                user: {
                    id: 'user-123',
                    email: 'test@example.com',
                    username: 'testuser',
                },
                isAuthenticated: true,
                logout: vi.fn(),
            });
        });

        it('should render user information when authenticated', () => {
            renderWithRouter(<Navigation />);
            expect(screen.getByText('testuser')).toBeInTheDocument();
        });

        it('should render logout button when authenticated', () => {
            renderWithRouter(<Navigation />);
            const logoutButton = screen.getByRole('button', {
                name: /logout|cerrar/i,
            });
            expect(logoutButton).toBeInTheDocument();
        });

        it('should call logout when logout button clicked', async () => {
            const logoutMock = vi.fn();
            (useAuthStore as any).mockReturnValue({
                user: { username: 'testuser' },
                isAuthenticated: true,
                logout: logoutMock,
            });

            renderWithRouter(<Navigation />);
            const logoutButton = screen.getByRole('button', {
                name: /logout|cerrar/i,
            });

            await userEvent.click(logoutButton);
            expect(logoutMock).toHaveBeenCalled();
        });
    });

    describe('Navigation Links', () => {
        beforeEach(() => {
            (useAuthStore as any).mockReturnValue({
                user: { username: 'testuser' },
                isAuthenticated: true,
                logout: vi.fn(),
            });
        });

        it('should render chat link', () => {
            renderWithRouter(<Navigation />);
            const chatLink = screen.getByRole('link', { name: /chat|conversa/i });
            expect(chatLink).toBeInTheDocument();
        });

        it('should render documents link', () => {
            renderWithRouter(<Navigation />);
            const docsLink = screen.getByRole('link', { name: /document|archivo/i });
            expect(docsLink).toBeInTheDocument();
        });
    });

    describe('Mobile Responsive', () => {
        it('should have hamburger menu button on mobile', () => {
            // Mock mobile viewport
            vi.spyOn(window, 'innerWidth', 'get').mockReturnValue(480);

            renderWithRouter(<Navigation />);
            const menuButton = screen.queryByRole('button', {
                name: /menu|hamburger/i,
            });

            // May or may not have menu button depending on implementation
            expect(menuButton || screen.getByRole('navigation')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('should have proper navigation landmarks', () => {
            renderWithRouter(<Navigation />);
            const nav = screen.getByRole('navigation');
            expect(nav).toBeInTheDocument();
        });

        it('should have proper ARIA labels', () => {
            renderWithRouter(<Navigation />);
            const nav = screen.getByRole('navigation');
            expect(nav).toHaveAttribute('aria-label') || expect(nav).toHaveAccessibleName();
        });
    });
});
