/**
 * ChatInterface — sugerencias de seguimiento (chips clicables tras cada
 * respuesta del asistente) y el interruptor por tema `show_sources`.
 *
 * A diferencia de los demás tests de este componente, aquí se usa el store de
 * Zustand REAL (no mockeado) porque hace falta reactividad real: los chips
 * dependen de que `messages` refleje lo que `addMessage` va agregando durante
 * el flujo real de envío, no de un array estático mockeado.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';
import { chatAPI } from '../../src/services/api';

function defaultGetImpl(url) {
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
                show_sources: true,
            },
        });
    }
    return Promise.reject(new Error('URL no mockeada: ' + url));
}

const getMock = vi.fn(defaultGetImpl);

// `getMock.mockImplementation(...)` en un test (ej. el de show_sources=false) sobrevive
// a `vi.clearAllMocks()` -- solo limpia llamadas/resultados, no la implementación --
// así que sin este reset global, un test posterior heredaría esa implementación vieja.
beforeEach(() => {
    getMock.mockImplementation(defaultGetImpl);
});

const sendQueryMock = vi.fn();

vi.mock('../../src/services/api', () => ({
    default: { get: (...args) => getMock(...args) },
    chatAPI: {
        createSession: vi.fn(() => Promise.resolve({ data: { data: { id: 'sesion-1' } } })),
        sendQuery: (...args) => sendQueryMock(...args),
        getSessions: vi.fn(() => Promise.resolve({ data: { data: [] } })),
        getSession: vi.fn(() => Promise.resolve({ data: { data: { messages: [] } } })),
    },
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

function renderWidget(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

async function sendMessageViaInput(user, text) {
    const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
    await user.type(input, text);
    fireEvent.submit(input.closest('form'));
}

describe('ChatInterface — sugerencias de seguimiento', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.setState({
            sessions: [], currentSessionId: null, messages: [], loading: false, error: null,
        });
    });

    it('muestra los chips de sugerencias cuando la respuesta trae `suggestions`', async () => {
        sendQueryMock.mockResolvedValue({
            data: { data: { response: 'Respuesta', sources: [], suggestions: ['¿Cuánto cuesta?', '¿Dónde se hace?'] } },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, '¿Cómo inicio el trámite?');

        await waitFor(() => {
            expect(screen.getByText('¿Cuánto cuesta?')).toBeInTheDocument();
        });
        expect(screen.getByText('¿Dónde se hace?')).toBeInTheDocument();
        expect(screen.getByText('También puedes preguntar')).toBeInTheDocument();
    });

    it('NO muestra chips cuando `suggestions` viene vacío o ausente', async () => {
        sendQueryMock.mockResolvedValue({
            data: { data: { response: 'Respuesta sin sugerencias', sources: [] } },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, '¿Cómo inicio el trámite?');

        await waitFor(() => {
            expect(screen.getByText('Respuesta sin sugerencias')).toBeInTheDocument();
        });
        expect(screen.queryByText('También puedes preguntar')).not.toBeInTheDocument();
    });

    it('clic en un chip envía ese texto como si el usuario lo hubiera escrito', async () => {
        sendQueryMock.mockResolvedValue({
            data: { data: { response: 'Respuesta', sources: [], suggestions: ['¿Y los requisitos?'] } },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, 'Primera pregunta');
        const chip = await screen.findByText('¿Y los requisitos?');

        await user.click(chip);

        await waitFor(() => {
            expect(sendQueryMock).toHaveBeenCalledTimes(2);
        });
        expect(sendQueryMock.mock.calls[1][1]).toBe('¿Y los requisitos?');
        expect(screen.getByText('¿Y los requisitos?', { selector: 'div, p, span' })).toBeInTheDocument();
    });

    it('solo el último mensaje del asistente muestra chips', async () => {
        sendQueryMock
            .mockResolvedValueOnce({
                data: { data: { response: 'Primera respuesta', sources: [], suggestions: ['Sugerencia vieja'] } },
            })
            .mockResolvedValueOnce({
                data: { data: { response: 'Segunda respuesta', sources: [], suggestions: ['Sugerencia nueva'] } },
            });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, 'Primera pregunta');
        await screen.findByText('Sugerencia vieja');

        await sendMessageViaInput(user, 'Segunda pregunta');

        await waitFor(() => {
            expect(screen.getByText('Sugerencia nueva')).toBeInTheDocument();
        });
        expect(screen.queryByText('Sugerencia vieja')).not.toBeInTheDocument();
    });
});

describe('ChatInterface — interruptor show_sources por tema', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.setState({
            sessions: [], currentSessionId: null, messages: [], loading: false, error: null,
        });
    });

    it('con show_sources=false, NO renderiza "Fuentes Oficiales" aunque el mensaje traiga sources', async () => {
        getMock.mockImplementation((url) => {
            if (url === 'admin/chatbot/profiles') return Promise.resolve({ data: [] });
            if (url.startsWith('chat/profiles/')) {
                return Promise.resolve({
                    data: {
                        title: 'Centinela-AI', subtitle: '', logo_url: '', icon: 'Bot',
                        welcome_message: '¡Hola!', primary_color: '#3b82f6',
                        show_sources: false,
                    },
                });
            }
            return Promise.reject(new Error('URL no mockeada: ' + url));
        });
        sendQueryMock.mockResolvedValue({
            data: { data: { response: 'Respuesta con fuentes', sources: [{ filename: 'doc.pdf', title: 'doc.pdf' }] } },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, '¿Cómo inicio el trámite?');

        await waitFor(() => {
            expect(screen.getByText('Respuesta con fuentes')).toBeInTheDocument();
        });
        expect(screen.queryByText('Fuentes Oficiales')).not.toBeInTheDocument();
    });
});

describe('ChatInterface — interruptor enable_feedback_buttons por tema', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.setState({
            sessions: [], currentSessionId: null, messages: [], loading: false, error: null,
        });
    });

    it('con enable_feedback_buttons=false, NO renderiza los botones de 👍/👎', async () => {
        getMock.mockImplementation((url) => {
            if (url === 'admin/chatbot/profiles') return Promise.resolve({ data: [] });
            if (url.startsWith('chat/profiles/')) {
                return Promise.resolve({
                    data: {
                        title: 'Centinela-AI', subtitle: '', logo_url: '', icon: 'Bot',
                        welcome_message: '¡Hola!', primary_color: '#3b82f6',
                        enable_feedback_buttons: false,
                    },
                });
            }
            return Promise.reject(new Error('URL no mockeada: ' + url));
        });
        sendQueryMock.mockResolvedValue({
            data: { data: { response: 'Respuesta sin feedback', sources: [] } },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, '¿Cómo inicio el trámite?');

        await waitFor(() => {
            expect(screen.getByText('Respuesta sin feedback')).toBeInTheDocument();
        });
        expect(screen.queryByText('¿Fue útil esta respuesta?')).not.toBeInTheDocument();
    });
});

describe('ChatInterface — el nombre de una fuente larga nunca desborda el widget', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.setState({
            sessions: [], currentSessionId: null, messages: [], loading: false, error: null,
        });
    });

    it('el span del nombre de archivo trae `truncate` + `min-w-0` (sin min-w-0 un flex item nunca se encoge por debajo de su texto, y `truncate` no logra recortarlo)', async () => {
        sendQueryMock.mockResolvedValue({
            data: {
                data: {
                    response: 'Respuesta con fuente de nombre muy largo',
                    sources: [{ filename: 'CA-PGO-D-E-05-Manual_de_usuario_Administracion_Privilegios_Muy_Largo.pdf', title: 'CA-PGO-D-E-05-Manual_de_usuario_Administracion_Privilegios_Muy_Largo.pdf' }],
                },
            },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, '¿Cómo inicio el trámite?');

        const sourceSpan = await screen.findByText('CA-PGO-D-E-05-Manual_de_usuario_Administracion_Privilegios_Muy_Largo.pdf');
        expect(sourceSpan.className).toContain('truncate');
        expect(sourceSpan.className).toContain('min-w-0');
    });

    it('el contenedor de mensajes tiene overflow-x-hidden como barrera final contra desbordes', async () => {
        sendQueryMock.mockResolvedValue({
            data: { data: { response: 'Respuesta', sources: [] } },
        });
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        await sendMessageViaInput(user, '¿Cómo inicio el trámite?');
        const messageText = await screen.findByText('Respuesta');

        const scrollContainer = messageText.closest('.overflow-y-auto');
        expect(scrollContainer.className).toContain('overflow-x-hidden');
    });
});
