/**
 * WidgetPage — el widget SIEMPRE debe establecer su propia sesion de invitado,
 * incluso si ya existe un token en localStorage (ej. una sesion real de admin
 * expirada del panel /admin, que vive en el MISMO origen chat.casmart.internal
 * y por lo tanto comparte localStorage con el <iframe> del widget).
 *
 * Incidente real 2026-08-14: WidgetPage solo llamaba a guestLogin() cuando
 * `!isAuthenticated`, y `isAuthenticated` se inicializaba en true con
 * CUALQUIER token preexistente -- el widget terminaba intentando usar una
 * sesion de admin ajena y expirada, disparando un 401 que un interceptor
 * global redirigia a /login DENTRO del iframe embebido en un sitio de
 * terceros.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WidgetPage from '../../src/pages/WidgetPage';

vi.mock('../../src/components/ChatInterface', () => ({
    default: () => <div data-testid="chat-interface-real">Chat real montado</div>,
}));

const guestLoginMock = vi.fn();

vi.mock('../../src/stores/authStore', () => ({
    useAuthStore: () => ({
        isAuthenticated: true, // token preexistente (ej. sesion de admin expirada)
        guestLogin: guestLoginMock,
    }),
}));

describe('WidgetPage — aislamiento de sesion de invitado', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        guestLoginMock.mockResolvedValue({ access_token: 'guest-token-real', user_id: 'guest-1', email: 'widget@casmarts.com', role: 'user' });
    });

    it('llama a guestLogin() SIEMPRE, aunque isAuthenticated ya sea true por un token viejo', async () => {
        render(
            <MemoryRouter>
                <WidgetPage />
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(guestLoginMock).toHaveBeenCalledTimes(1);
        });

        // Debe terminar mostrando el chat real, no un estado de error/login
        await screen.findByTestId('chat-interface-real');
    });

    it('si guestLogin falla, muestra el mensaje de error del widget (nunca un login real)', async () => {
        guestLoginMock.mockRejectedValueOnce(new Error('500'));

        render(
            <MemoryRouter>
                <WidgetPage />
            </MemoryRouter>
        );

        await screen.findByText(/Error al conectar con el asistente/i);
        expect(screen.queryByTestId('chat-interface-real')).not.toBeInTheDocument();
    });
});
