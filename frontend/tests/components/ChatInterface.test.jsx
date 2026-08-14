/**
 * ChatInterface Component Tests (modo escritorio, isWidget=false)
 *
 * Reescrito 2026-08-14: la versión anterior probaba una API imaginaria del
 * store (`currentSession`, `isLoading`, `sendMessage` como acción del store)
 * que nunca existió -- el componente real usa `chatAPI.sendQuery` directo
 * (services/api.js) y el store solo expone `messages/loading/error/
 * addMessage/setMessages/setLoading/setError/clearMessages`. El input tampoco
 * tiene accessible name "message": se identifica por su placeholder real.
 * Ver `ChatInterfaceProfileIcon.test.jsx`, `ChatInterfaceWidgetTheming.test.jsx`
 * y `ChatInterfaceNewSessionSend.test.jsx` para la cobertura de modo widget,
 * ícono e inicio de sesión nueva -- este archivo cubre el modo escritorio.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';

vi.mock('../../src/stores/chatStore');

const addMessageMock = vi.fn();
const setLoadingMock = vi.fn();
const setErrorMock = vi.fn();
const clearMessagesMock = vi.fn();

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
        post: vi.fn(() => Promise.resolve({ data: {} })),
    },
    chatAPI: {
        getSessions: vi.fn(() => Promise.resolve({ data: { data: [] } })),
        getSession: vi.fn(() => Promise.reject(new Error('no aplica en este test'))),
        createSession: vi.fn(() => Promise.resolve({ data: { data: { id: 'sesion-1' } } })),
        sendQuery: vi.fn(() =>
            Promise.resolve({ data: { data: { response: 'Respuesta real', sources: [] } } })
        ),
    },
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

function renderChat(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ChatInterface Component (escritorio)', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.mockReturnValue({
            messages: [],
            loading: false,
            error: null,
            addMessage: addMessageMock,
            setMessages: vi.fn(),
            setLoading: setLoadingMock,
            setError: setErrorMock,
            clearMessages: clearMessagesMock,
        });
    });

    describe('Rendering', () => {
        it('should render the message input and send button', async () => {
            renderChat(<ChatInterface />);
            const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
            expect(input).toBeInTheDocument();
            expect(input.closest('form').querySelector('button[type="submit"]')).toBeInTheDocument();
        });

        it('should disable the send button with empty input', async () => {
            renderChat(<ChatInterface />);
            const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
            const sendButton = input.closest('form').querySelector('button[type="submit"]');
            expect(sendButton).toBeDisabled();
        });

        it('should show the empty-state welcome message when there are no messages', async () => {
            renderChat(<ChatInterface />);
            // El welcome_message se pinta tanto en el banner superior como en el
            // avatar de estado vacío (ambos siempre visibles, no solo en widget) --
            // basta con confirmar que aparece al menos una vez.
            const matches = await screen.findAllByText('¡Hola! ¿En qué puedo ayudarte?');
            expect(matches.length).toBeGreaterThan(0);
        });
    });

    describe('Message sending', () => {
        it('should send the typed message and display the response', async () => {
            const user = userEvent.setup();
            renderChat(<ChatInterface />);

            const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
            await user.type(input, 'Hola, tengo una pregunta');
            fireEvent.submit(input.closest('form'));

            await waitFor(() => {
                expect(addMessageMock).toHaveBeenCalledWith(
                    expect.objectContaining({ role: 'assistant', content: 'Respuesta real' })
                );
            });
        });

        it('should clear the input after sending', async () => {
            const user = userEvent.setup();
            renderChat(<ChatInterface />);

            const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
            await user.type(input, 'Test message');
            fireEvent.submit(input.closest('form'));

            await waitFor(() => {
                expect(input.value).toBe('');
            });
        });

        it('should disable the input while loading', async () => {
            useChatStore.mockReturnValue({
                messages: [],
                loading: true,
                error: null,
                addMessage: addMessageMock,
                setMessages: vi.fn(),
                setLoading: setLoadingMock,
                setError: setErrorMock,
                clearMessages: clearMessagesMock,
            });

            renderChat(<ChatInterface />);
            const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
            expect(input).toBeDisabled();
            expect(screen.getByText('Procesando consulta...')).toBeInTheDocument();
        });
    });

    describe('Message display', () => {
        it('should display user messages', async () => {
            useChatStore.mockReturnValue({
                messages: [{ role: 'user', content: 'Mensaje del usuario', timestamp: new Date().toISOString() }],
                loading: false,
                error: null,
                addMessage: addMessageMock,
                setMessages: vi.fn(),
                setLoading: setLoadingMock,
                setError: setErrorMock,
                clearMessages: clearMessagesMock,
            });

            renderChat(<ChatInterface />);
            expect(await screen.findByText('Mensaje del usuario')).toBeInTheDocument();
        });

        it('should display assistant messages', async () => {
            useChatStore.mockReturnValue({
                messages: [{ role: 'assistant', content: 'Respuesta del asistente', timestamp: new Date().toISOString() }],
                loading: false,
                error: null,
                addMessage: addMessageMock,
                setMessages: vi.fn(),
                setLoading: setLoadingMock,
                setError: setErrorMock,
                clearMessages: clearMessagesMock,
            });

            renderChat(<ChatInterface />);
            expect(await screen.findByText('Respuesta del asistente')).toBeInTheDocument();
        });
    });

    describe('Error handling', () => {
        it('should display the error banner with a retry button', async () => {
            useChatStore.mockReturnValue({
                messages: [],
                loading: false,
                error: 'Error al enviar mensaje: network error',
                addMessage: addMessageMock,
                setMessages: vi.fn(),
                setLoading: setLoadingMock,
                setError: setErrorMock,
                clearMessages: clearMessagesMock,
            });

            renderChat(<ChatInterface />);
            expect(await screen.findByText(/network error/i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument();
        });
    });
});
