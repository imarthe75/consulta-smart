/**
 * ChatInterface — el ícono con nombre configurado en el admin (ICON_MAP, ej.
 * "ShieldCheck") debe reflejarse en el avatar/header del chat real, no solo
 * en el "Probador Sandbox" del panel admin.
 *
 * Incidente real 2026-08-14: el selector de íconos del admin (biblioteca de
 * 12 íconos con nombre) guardaba correctamente `icon` en la BD y el sandbox
 * de preview lo mostraba bien, pero ChatInterface.jsx (el chat real, incluido
 * el widget embebido) ignoraba `profileConfig.icon` por completo y siempre
 * mostraba el emoji 🤖 genérico, sin importar la selección.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';

vi.mock('../../src/stores/chatStore');

vi.mock('../../src/services/api', () => ({
    default: {
        get: vi.fn((url) => {
            if (url === 'admin/chatbot/profiles') return Promise.resolve({ data: [] });
            if (url.startsWith('chat/profiles/')) {
                return Promise.resolve({
                    data: {
                        title: 'Centinela-AI',
                        subtitle: 'Omni XDR',
                        logo_url: '',          // sin logo custom -- debe caer al ICON_MAP
                        icon: 'ShieldCheck',    // seleccionado en el admin
                        welcome_message: '¡Hola! ¿En qué puedo ayudarte?',
                        primary_color: '#06B6D4',
                    },
                });
            }
            return Promise.reject(new Error('URL no mockeada: ' + url));
        }),
    },
    chatAPI: {},
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

function renderWidget(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ChatInterface — ícono con nombre del perfil (ICON_MAP)', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useChatStore).mockReturnValue({
            messages: [], loading: false, error: null,
            addMessage: vi.fn(), setMessages: vi.fn(), setLoading: vi.fn(),
            setError: vi.fn(), clearMessages: vi.fn(),
        });
    });

    it('usa el ícono ShieldCheck configurado en el admin, NO el emoji 🤖 genérico', async () => {
        renderWidget(<ChatInterface isWidget={true} />);

        await waitFor(() => {
            // lucide-react renderiza cada ícono como <svg class="lucide lucide-shield-check ...">
            const svg = document.querySelector('svg.lucide-shield-check');
            expect(svg).toBeTruthy();
        });

        // El emoji generico NO debe aparecer en ningun lado del avatar/header
        expect(screen.queryByText('🤖')).not.toBeInTheDocument();
    });
});
