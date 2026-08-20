/**
 * WidgetPage — un tema con config_metadata.enable_widget_embed=false no debe
 * inicializar el chat embebible en absoluto (ni siquiera llamar guestLogin),
 * y debe mostrar un mensaje de bloqueo en vez del chat real.
 *
 * Si la verificación misma falla (red, tema inexistente), el widget debe
 * seguir funcionando con normalidad ("fail-open") -- un error de red no debe
 * bloquear un embed que de otro modo sería válido.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WidgetPage from '../../src/pages/WidgetPage';

vi.mock('../../src/components/ChatInterface', () => ({
    default: () => <div data-testid="chat-interface-real">Chat real montado</div>,
}));

const guestLoginMock = vi.fn();
const getMock = vi.fn();

vi.mock('../../src/stores/authStore', () => ({
    useAuthStore: () => ({
        isAuthenticated: false,
        guestLogin: guestLoginMock,
    }),
}));

vi.mock('../../src/services/api', () => ({
    default: { get: (...args) => getMock(...args) },
}));

function setUrl(href) {
    delete window.location;
    window.location = new URL(href);
}

describe('WidgetPage — permiso de embed por tema', () => {
    const originalLocation = window.location;

    beforeEach(() => {
        vi.clearAllMocks();
        guestLoginMock.mockResolvedValue({ access_token: 'guest-token-real', user_id: 'guest-1', email: 'widget@casmarts.com', role: 'user' });
    });

    afterEach(() => {
        window.location = originalLocation;
    });

    it('con enable_widget_embed=false, muestra el bloqueo y NUNCA llama guestLogin', async () => {
        setUrl('http://localhost/widget?tenantId=teca');
        getMock.mockResolvedValue({ data: { enable_widget_embed: false } });

        render(
            <MemoryRouter>
                <WidgetPage />
            </MemoryRouter>
        );

        await screen.findByText(/no está disponible para uso embebido/i);
        expect(guestLoginMock).not.toHaveBeenCalled();
        expect(screen.queryByTestId('chat-interface-real')).not.toBeInTheDocument();
    });

    it('con enable_widget_embed=true (o ausente), el widget funciona normal', async () => {
        setUrl('http://localhost/widget?tenantId=teca');
        getMock.mockResolvedValue({ data: { enable_widget_embed: true } });

        render(
            <MemoryRouter>
                <WidgetPage />
            </MemoryRouter>
        );

        await screen.findByTestId('chat-interface-real');
        expect(guestLoginMock).toHaveBeenCalledTimes(1);
    });

    it('si la verificación de permiso falla (red), el widget sigue funcionando (fail-open)', async () => {
        setUrl('http://localhost/widget?tenantId=teca');
        getMock.mockRejectedValue(new Error('network error'));

        render(
            <MemoryRouter>
                <WidgetPage />
            </MemoryRouter>
        );

        await screen.findByTestId('chat-interface-real');
        expect(guestLoginMock).toHaveBeenCalledTimes(1);
    });
});
