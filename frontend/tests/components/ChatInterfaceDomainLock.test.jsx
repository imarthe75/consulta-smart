/**
 * ChatInterface — bloqueo de tema por dominio (domainLock.js).
 *
 * `chat.teca.ca-smarts.com` es un dominio público dedicado al tenant "teca":
 * el chat debe forzar ese profile_id sin importar lo que traiga la URL, y
 * ocultar el selector de "Asistente Activo" para que no se pueda cambiar de
 * tema desde ahí. En cualquier otro dominio (p. ej. chat.casmart.internal)
 * el comportamiento previo -- selector visible, profile_id por query param --
 * debe seguir intacto.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';

vi.mock('../../src/stores/chatStore');

const getMock = vi.fn((url) => {
    if (url === 'admin/chatbot/profiles') {
        return Promise.resolve({
            data: [
                { id: 'general', name: 'General' },
                { id: 'teca', name: 'Teca' },
            ],
        });
    }
    if (url.startsWith('chat/profiles/')) {
        const pid = url.split('/').pop();
        return Promise.resolve({
            data: {
                title: `Perfil ${pid}`,
                subtitle: '',
                logo_url: '',
                icon: 'Bot',
                welcome_message: '¡Hola!',
                primary_color: '#3b82f6',
            },
        });
    }
    return Promise.reject(new Error('URL no mockeada: ' + url));
});

vi.mock('../../src/services/api', () => ({
    default: { get: (...args) => getMock(...args) },
    chatAPI: {},
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

const originalLocation = window.location;

function setUrl(href) {
    delete window.location;
    window.location = new URL(href);
}

function renderChat(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ChatInterface — bloqueo de tema por dominio', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useChatStore).mockReturnValue({
            messages: [], loading: false, error: null,
            addMessage: vi.fn(), setMessages: vi.fn(), setLoading: vi.fn(),
            setError: vi.fn(), clearMessages: vi.fn(),
        });
    });

    afterEach(() => {
        window.location = originalLocation;
    });

    it('en chat.teca.ca-smarts.com fuerza el perfil "teca" e IGNORA el profile_id de la URL', async () => {
        setUrl('https://chat.teca.ca-smarts.com/?profile_id=general');
        renderChat(<ChatInterface isWidget={false} />);

        await waitFor(() => {
            expect(getMock).toHaveBeenCalledWith('chat/profiles/teca');
        });
        expect(getMock).not.toHaveBeenCalledWith('chat/profiles/general');
    });

    it('en chat.teca.ca-smarts.com oculta el selector de "Asistente Activo"', async () => {
        setUrl('https://chat.teca.ca-smarts.com/');
        renderChat(<ChatInterface isWidget={false} />);

        await waitFor(() => {
            expect(screen.getAllByText('Perfil teca').length).toBeGreaterThan(0);
        });
        expect(screen.queryByText('Asistente Activo')).not.toBeInTheDocument();
    });

    it('en chat.casmart.internal respeta el profile_id de la URL y muestra el selector', async () => {
        setUrl('https://chat.casmart.internal/?profile_id=general');
        renderChat(<ChatInterface isWidget={false} />);

        await waitFor(() => {
            expect(getMock).toHaveBeenCalledWith('chat/profiles/general');
        });
        expect(screen.getByText('Asistente Activo')).toBeInTheDocument();
    });
});
