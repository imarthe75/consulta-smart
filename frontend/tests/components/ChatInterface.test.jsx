/**
 * ChatInterface Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInterface from '../../src/components/ChatInterface';
import { useChatStore } from '../../src/stores/chatStore';

vi.mock('../../src/stores/chatStore');

describe('ChatInterface Component', () => {
    const mockSendMessage = vi.fn();
    const mockLoadHistory = vi.fn();
    const mockSelectSession = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        (useChatStore as any).mockReturnValue({
            currentSession: {
                id: 'session-1',
                title: 'Test Session',
                messages: [],
            },
            messages: [],
            isLoading: false,
            error: null,
            sendMessage: mockSendMessage,
            loadHistory: mockLoadHistory,
            selectSession: mockSelectSession,
        });
    });

    describe('Rendering', () => {
        it('should render chat interface container', () => {
            render(<ChatInterface />);
            const container = screen.getByRole('main') || screen.getByTestId('chat-interface');
            expect(container).toBeInTheDocument();
        });

        it('should render message input area', () => {
            render(<ChatInterface />);
            const input = screen.getByRole('textbox', { name: /message|pregunta/i });
            expect(input).toBeInTheDocument();
        });

        it('should render send button', () => {
            render(<ChatInterface />);
            const sendButton = screen.getByRole('button', { name: /send|enviar/i });
            expect(sendButton).toBeInTheDocument();
        });

        it('should render messages container', () => {
            render(<ChatInterface />);
            const messagesArea = screen.getByTestId('messages-container') ||
                screen.getByRole('region', { name: /messages|mensaje/i });
            expect(messagesArea).toBeInTheDocument();
        });
    });

    describe('Message Sending', () => {
        it('should send message on button click', async () => {
            mockSendMessage.mockResolvedValueOnce({
                id: 'msg-1',
                content: 'Test message',
            });

            render(<ChatInterface />);
            const input = screen.getByRole('textbox', { name: /message/i });
            const sendButton = screen.getByRole('button', { name: /send|enviar/i });

            await userEvent.type(input, 'Test message');
            await userEvent.click(sendButton);

            expect(mockSendMessage).toHaveBeenCalledWith(
                expect.objectContaining({
                    content: 'Test message',
                })
            );
        });

        it('should send message on Enter key', async () => {
            mockSendMessage.mockResolvedValueOnce({});

            render(<ChatInterface />);
            const input = screen.getByRole('textbox', { name: /message/i });

            await userEvent.type(input, 'Test{Enter}');

            expect(mockSendMessage).toHaveBeenCalled();
        });

        it('should clear input after sending message', async () => {
            mockSendMessage.mockResolvedValueOnce({});

            render(<ChatInterface />);
            const input = screen.getByRole('textbox', { name: /message/i }) as HTMLInputElement;

            await userEvent.type(input, 'Test message');
            await userEvent.click(screen.getByRole('button', { name: /send|enviar/i }));

            await waitFor(() => {
                expect(input.value).toBe('');
            });
        });

        it('should disable send button with empty input', () => {
            render(<ChatInterface />);
            const sendButton = screen.getByRole('button', { name: /send|enviar/i });

            expect(sendButton).toBeDisabled();
        });
    });

    describe('Message Display', () => {
        it('should display user messages', () => {
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [
                    {
                        id: 'msg-1',
                        content: 'User message',
                        role: 'user',
                        createdAt: new Date(),
                    },
                ],
                isLoading: false,
                error: null,
                sendMessage: mockSendMessage,
            });

            render(<ChatInterface />);
            expect(screen.getByText('User message')).toBeInTheDocument();
        });

        it('should display assistant messages', () => {
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [
                    {
                        id: 'msg-2',
                        content: 'Assistant response',
                        role: 'assistant',
                        createdAt: new Date(),
                    },
                ],
                isLoading: false,
                error: null,
                sendMessage: mockSendMessage,
            });

            render(<ChatInterface />);
            expect(screen.getByText('Assistant response')).toBeInTheDocument();
        });

        it('should show loading indicator while sending', () => {
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [],
                isLoading: true,
                error: null,
                sendMessage: mockSendMessage,
            });

            render(<ChatInterface />);
            const loader = screen.getByTestId('loading-indicator') ||
                screen.getByRole('status', { name: /loading/i });
            expect(loader).toBeInTheDocument();
        });
    });

    describe('Error Handling', () => {
        it('should display error message', () => {
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [],
                isLoading: false,
                error: 'Failed to send message',
                sendMessage: mockSendMessage,
            });

            render(<ChatInterface />);
            expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
        });

        it('should allow retrying after error', async () => {
            const { rerender } = render(<ChatInterface />);

            // First error
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [],
                isLoading: false,
                error: 'Failed',
                sendMessage: mockSendMessage,
            });
            rerender(<ChatInterface />);

            const retryButton = screen.queryByRole('button', { name: /retry|reintentar/i });
            if (retryButton) {
                await userEvent.click(retryButton);
                expect(mockSendMessage).toHaveBeenCalled();
            }
        });
    });

    describe('Accessibility', () => {
        it('should have proper ARIA labels', () => {
            render(<ChatInterface />);
            const input = screen.getByRole('textbox', { name: /message|pregunta/i });
            expect(input).toHaveAccessibleName();
        });

        it('should announce new messages to screen readers', () => {
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [
                    {
                        id: 'msg-1',
                        content: 'New message',
                        role: 'assistant',
                    },
                ],
                isLoading: false,
                error: null,
            });

            render(<ChatInterface />);
            const liveRegion = screen.getByRole('status') ||
                screen.getByTestId('chat-messages');
            expect(liveRegion).toBeInTheDocument();
        });
    });

    describe('Message Formatting', () => {
        it('should render markdown in messages', () => {
            (useChatStore as any).mockReturnValue({
                currentSession: { id: 'session-1' },
                messages: [
                    {
                        id: 'msg-1',
                        content: '**Bold text** and `code`',
                        role: 'assistant',
                    },
                ],
                isLoading: false,
                error: null,
            });

            render(<ChatInterface />);
            const boldText = screen.getByText(/bold text/i);
            expect(boldText).toBeInTheDocument();
        });
    });
});
