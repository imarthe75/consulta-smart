/**
 * ChatInterface — el primer mensaje de una sesión de chat nueva (el caso común
 * del widget: cada visita de invitado empieza sin `currentSessionId`) debía
 * quedarse colgado en "Procesando consulta..." para siempre, sin importar si
 * el backend respondía bien o con error.
 *
 * Incidente real 2026-08-14: `currentSessionId` es un `useState` local. Dentro
 * de `sendMessage`, cuando no había sesión previa, el código creaba una sesión
 * nueva, guardaba su id en `activeSessionId`, y llamaba `setCurrentSessionId(id)`
 * -- pero ese `setState` no se refleja en `currentSessionId` sino hasta el
 * siguiente render (cierre de React). Las comprobaciones `activeSessionId ===
 * currentSessionId` de después (para aplicar la respuesta y apagar `loading`)
 * comparaban el id nuevo contra el `null` capturado en el cierre, así que
 * SIEMPRE eran falsas para el primer mensaje de una sesión nueva: la respuesta
 * nunca se agregaba y `setLoading(false)` nunca se ejecutaba.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';

vi.mock('../../src/stores/chatStore');

const setLoadingMock = vi.fn();
const addMessageMock = vi.fn();

vi.mock('../../src/services/api', () => ({
    default: {
        get: vi.fn((url) => {
            if (url === 'admin/chatbot/profiles') return Promise.resolve({ data: [] });
            if (url.startsWith('chat/profiles/')) {
                return Promise.resolve({
                    data: {
                        title: 'Centinela-AI',
                        subtitle: 'Omni XDR',
                        logo_url: '',
                        icon: 'Bot',
                        welcome_message: '¡Hola! ¿En qué puedo ayudarte?',
                        primary_color: '#3b82f6',
                    },
                });
            }
            return Promise.reject(new Error('URL no mockeada: ' + url));
        }),
    },
    chatAPI: {
        createSession: vi.fn(() =>
            Promise.resolve({ data: { data: { id: 'sesion-nueva-real' } } })
        ),
        sendQuery: vi.fn(() =>
            Promise.resolve({
                data: { data: { response: 'Respuesta real del asistente', sources: [] } },
            })
        ),
        getSessions: vi.fn(() => Promise.resolve({ data: { data: [] } })),
        getSession: vi.fn(() => Promise.reject(new Error('no aplica en este test'))),
    },
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

function renderWidget(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ChatInterface — primer mensaje de una sesión nueva', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useChatStore).mockReturnValue({
            messages: [],
            loading: false,
            error: null,
            addMessage: addMessageMock,
            setMessages: vi.fn(),
            setLoading: setLoadingMock,
            setError: vi.fn(),
            clearMessages: vi.fn(),
        });
    });

    it('agrega la respuesta y apaga loading, sin sesión previa', async () => {
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
        await user.type(input, '¿Cómo calcula Centinela el Centinela Risk Score (CRS)?');
        fireEvent.submit(input.closest('form'));

        await waitFor(() => {
            expect(addMessageMock).toHaveBeenCalledWith(
                expect.objectContaining({ role: 'assistant', content: 'Respuesta real del asistente' })
            );
        });

        // Regresión real: antes del fix, esta llamada nunca ocurría para el
        // primer mensaje de una sesión nueva y el spinner quedaba colgado.
        expect(setLoadingMock).toHaveBeenCalledWith(false);
    });
});
