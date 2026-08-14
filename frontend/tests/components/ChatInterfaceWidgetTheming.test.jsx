/**
 * ChatInterface — propagación real de tenantId/themeColor/title vía query params
 * (modo widget). Verifica que el `<iframe src=".../widget?tenantId=X&themeColor=Y">`
 * que genera public/widget.js realmente termina pintando el color solicitado, y no
 * el primary_color guardado en la BD del perfil -- ese es el bug reportado por el
 * usuario (2026-08-14): "por qué no respeta el color?".
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';

function renderWidget(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

vi.mock('../../src/stores/chatStore');

vi.mock('../../src/services/api', () => {
    return {
        default: {
            get: vi.fn((url) => {
                if (url === 'admin/chatbot/profiles') {
                    return Promise.resolve({ data: [] });
                }
                if (url.startsWith('chat/profiles/')) {
                    // Simula el perfil REAL guardado en la BD para el tenant --
                    // con un primary_color DISTINTO al que pide el query param,
                    // para detectar si el query param realmente gana o no.
                    return Promise.resolve({
                        data: {
                            title: 'Centinela-AI',
                            subtitle: 'Plataforma de seguridad',
                            logo_url: '',
                            icon: 'Bot',
                            welcome_message: '¡Hola! ¿En qué puedo ayudarte?',
                            primary_color: '#3b82f6', // color "de fábrica" en la BD
                        },
                    });
                }
                return Promise.reject(new Error('URL no mockeada: ' + url));
            }),
        },
        chatAPI: {},
    };
});

// jsdom no implementa scrollIntoView; ChatInterface lo llama en cada render de mensajes.
window.HTMLElement.prototype.scrollIntoView = vi.fn();

const originalLocation = window.location;

function setWidgetUrl(search) {
    delete window.location;
    window.location = new URL('http://localhost/widget' + search);
}

describe('ChatInterface — theming vía query params (modo widget)', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useChatStore).mockReturnValue({
            messages: [],
            loading: false,
            error: null,
            addMessage: vi.fn(),
            setMessages: vi.fn(),
            setLoading: vi.fn(),
            setError: vi.fn(),
            clearMessages: vi.fn(),
        });
    });

    afterEach(() => {
        window.location = originalLocation;
    });

    it('usa el themeColor del query param (el que manda widget.js) en vez del primary_color de la BD', async () => {
        setWidgetUrl('?tenantId=centinela-ai&themeColor=%2306b6d4&title=Centinela-AI');
        renderWidget(<ChatInterface isWidget={true} />);

        // El avatar del estado vacio se pinta con profileConfig.primary_color
        await waitFor(() => {
            // El avatar ya no renderiza el emoji 🤖 literal -- desde el fix de
            // ícono con nombre (ICON_MAP), sin logo_url ni icon configurado cae
            // al ícono real "Bot" de lucide-react (ver ChatInterfaceProfileIcon.test.jsx).
            // Desde el rediseño del header del widget (2026-08-14) hay un SEGUNDO
            // svg.lucide-bot en el DOM (la insignia del header, w-8 h-8, sin color
            // inline) -- se acota al avatar grande del estado vacio (w-16 h-16) para
            // no matchear el del header.
            const avatar = document.querySelector('.w-16.h-16 svg.lucide-bot').closest('div');
            expect(avatar.style.backgroundColor).toBe('rgb(6, 182, 212)'); // #06b6d4, NO #3b82f6
        });
    });

    it('sin themeColor en la URL, cae correctamente al primary_color de la BD', async () => {
        setWidgetUrl('?tenantId=centinela-ai&title=Centinela-AI');
        renderWidget(<ChatInterface isWidget={true} />);

        await waitFor(() => {
            // El avatar ya no renderiza el emoji 🤖 literal -- desde el fix de
            // ícono con nombre (ICON_MAP), sin logo_url ni icon configurado cae
            // al ícono real "Bot" de lucide-react (ver ChatInterfaceProfileIcon.test.jsx).
            // Ver nota arriba: se acota al avatar w-16 h-16 para no matchear el
            // svg.lucide-bot de la insignia del header (w-8 h-8).
            const avatar = document.querySelector('.w-16.h-16 svg.lucide-bot').closest('div');
            expect(avatar.style.backgroundColor).toBe('rgb(59, 130, 246)'); // #3b82f6 de la BD
        });
    });

    it('ya no muestra el subtitulo hardcodeado de tramites para un tenant no-tramite', async () => {
        setWidgetUrl('?tenantId=centinela-ai&themeColor=%2306b6d4');
        renderWidget(<ChatInterface isWidget={true} />);

        await waitFor(() => {
            expect(screen.getAllByText('¡Hola! ¿En qué puedo ayudarte?').length).toBeGreaterThan(0);
        });
        expect(screen.queryByText(/trámites, requisitos o normativa oficial/i)).not.toBeInTheDocument();
        expect(screen.getByText('Plataforma de seguridad')).toBeInTheDocument();
    });
});
