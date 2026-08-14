/**
 * ChatInterface — el primer mensaje de una sesión de chat nueva (el caso común
 * del widget: cada visita de invitado empieza sin `currentSessionId`) tenía DOS
 * bugs reales encadenados, ambos relacionados con la creación de la sesión:
 *
 * 1. (corregido antes) `currentSessionId` es un `useState` local. Dentro de
 *    `sendMessage`, cuando no había sesión previa, el código creaba una sesión
 *    nueva y llamaba `setCurrentSessionId(id)` -- pero ese `setState` no se
 *    refleja en `currentSessionId` sino hasta el siguiente render (cierre de
 *    React). Las comprobaciones `activeSessionId === currentSessionId` de
 *    después (para aplicar la respuesta y apagar `loading`) comparaban el id
 *    nuevo contra el `null` capturado en el cierre, así que SIEMPRE eran
 *    falsas: la respuesta nunca se agregaba y `setLoading(false)` nunca se
 *    ejecutaba -- spinner colgado indefinidamente.
 *
 * 2. (corregido 2026-08-14, este archivo) el efecto "cargar historial al
 *    cambiar de sesión" (`useEffect(..., [currentSessionId])`) se dispara
 *    también cuando `currentSessionId` cambia porque se acaba de crear una
 *    sesión NUEVA dentro de `sendMessage` -- en ese instante el backend
 *    todavía no tiene guardado el mensaje del usuario (la petición de envío
 *    ni siquiera ha llegado o terminado). El efecto consulta el historial,
 *    lo encuentra vacío, y llama `clearMessages()` -- borrando la burbuja del
 *    mensaje del usuario que se acababa de agregar de forma optimista.
 *    Síntoma real reportado por el usuario: "cada que hago una pregunta sigue
 *    desapareciendo del chat... no deberían ocultarse/desaparecer las
 *    preguntas, aunque no reaccione el LLM".
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';
import { chatAPI } from '../../src/services/api';

vi.mock('../../src/stores/chatStore');

const setLoadingMock = vi.fn();
const addMessageMock = vi.fn();
const setMessagesMock = vi.fn();
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
        // Simula la respuesta real que da el backend justo tras crear la sesión:
        // la sesión existe, pero todavía sin mensajes (el envío está en curso).
        // Si el bug de la carrera sigue presente, esto dispara clearMessages().
        getSession: vi.fn(() => Promise.resolve({ data: { data: { messages: [] } } })),
    },
}));

window.HTMLElement.prototype.scrollIntoView = vi.fn();

function renderWidget(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ChatInterface — primer mensaje de una sesión nueva', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useChatStore.mockReturnValue({
            messages: [],
            loading: false,
            error: null,
            addMessage: addMessageMock,
            setMessages: setMessagesMock,
            setLoading: setLoadingMock,
            setError: vi.fn(),
            clearMessages: clearMessagesMock,
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

    it('no borra el mensaje del usuario recién agregado al crear la sesión (carrera con la carga de historial)', async () => {
        const user = userEvent.setup();
        renderWidget(<ChatInterface isWidget={true} />);

        const input = await screen.findByPlaceholderText('Escribe tu consulta aquí...');
        await user.type(input, 'Primera pregunta de una sesión nueva');
        fireEvent.submit(input.closest('form'));

        await waitFor(() => {
            expect(addMessageMock).toHaveBeenCalledWith(
                expect.objectContaining({ role: 'user', content: 'Primera pregunta de una sesión nueva' })
            );
        });

        // Dar tiempo a que, SI el bug estuviera presente, el efecto de historial
        // (disparado por el cambio de currentSessionId) alcance a resolverse y
        // borrar el mensaje.
        await waitFor(() => {
            expect(addMessageMock).toHaveBeenCalledWith(
                expect.objectContaining({ role: 'assistant' })
            );
        });

        // Regresión real: el efecto de "cargar historial al cambiar de sesión"
        // no debe dispararse para una sesión que se acaba de crear en este mismo
        // envío -- ni limpiar los mensajes optimistas ni reemplazarlos con el
        // (vacío) historial que el backend todavía no tiene guardado.
        expect(clearMessagesMock).not.toHaveBeenCalled();
        expect(setMessagesMock).not.toHaveBeenCalled();
        expect(chatAPI.getSession).not.toHaveBeenCalled();
    });
});
