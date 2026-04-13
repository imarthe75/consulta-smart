/**
 * Phase 4D - E2E Tests
 * Chat and Conversation Flow
 */

describe('Chat Flow E2E', () => {
    const baseUrl = 'http://localhost:3000';

    beforeEach(() => {
        // Login
        cy.visit(`${baseUrl}/login`);
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        // Navigate to chat
        cy.url().should('include', '/dashboard');
        cy.get('a[href*="chat"]').click();
        cy.url().should('include', '/chat');
    });

    it('should create a new chat session', () => {
        cy.get('button[data-testid="new-chat-btn"]').click();

        // Modal should appear
        cy.get('[role="dialog"]').should('be.visible');

        // Enter session title
        cy.get('input[name="title"]').type('Property Registration Information');

        // Create button
        cy.get('button[data-testid="create-session-btn"]').click();

        // Should create and navigate to session
        cy.get('[data-testid="chat-header"]').should('contain', 'Property Registration');
    });

    it('should send and receive chat messages', () => {
        // Create session first
        cy.get('button[data-testid="new-chat-btn"]').click();
        cy.get('input[name="title"]').type('Test Chat');
        cy.get('button[data-testid="create-session-btn"]').click();

        // Type message
        cy.get('textarea[data-testid="message-input"]').type(
            'How do I register a property in Quintana Roo?'
        );

        // Send message
        cy.get('button[data-testid="send-btn"]').click();

        // User message should appear
        cy.get('[data-testid="message-list"]')
            .should('contain', 'How do I register a property');

        // Assistant response should appear
        cy.get('[data-testid="assistant-message"]', { timeout: 10000 })
            .should('be.visible');
    });

    it('should display conversation history', () => {
        // Send multiple messages
        cy.get('textarea[data-testid="message-input"]').type('First question');
        cy.get('button[data-testid="send-btn"]').click();

        cy.get('textarea[data-testid="message-input"]', { timeout: 5000 }).type('Second question');
        cy.get('button[data-testid="send-btn"]').click();

        // All messages should be visible
        cy.get('[data-testid="message-list"] [data-testid="chat-message"]')
            .should('have.length.at.least', 2);
    });

    it('should show loading state during response', () => {
        cy.get('textarea[data-testid="message-input"]').type('Processing question');
        cy.get('button[data-testid="send-btn"]').click();

        // Loading indicator should appear
        cy.get('[data-testid="loading-indicator"]', { timeout: 2000 }).should('be.visible');

        // Loading should disappear after response
        cy.get('[data-testid="assistant-message"]', { timeout: 10000 }).should('be.visible');
        cy.get('[data-testid="loading-indicator"]').should('not.exist');
    });

    it('should list past chat sessions', () => {
        cy.get('[data-testid="sessions-list"]').should('be.visible');

        // Each session should be clickable
        cy.get('[data-testid="sessions-list"] li').each(($item) => {
            cy.wrap($item).should('have.css', 'cursor', 'pointer');
        });
    });

    it('should switch between chat sessions', () => {
        // Get first session
        cy.get('[data-testid="sessions-list"] li').first().click();
        cy.get('[data-testid="chat-header"]').should('be.visible');

        const firstSessionTitle = cy.get('[data-testid="chat-header"]').invoke('text');

        // Get second session
        cy.get('[data-testid="sessions-list"] li').eq(1).click();

        // Chat header should change
        cy.get('[data-testid="chat-header"]').invoke('text').should('not.equal', firstSessionTitle);
    });

    it('should delete a chat session', () => {
        cy.get('[data-testid="sessions-list"] li').first().within(() => {
            cy.get('button[data-testid="delete-session"]').click();
        });

        // Confirmation dialog
        cy.get('[role="dialog"]').should('contain', 'confirm');
        cy.get('button[data-testid="confirm-delete"]').click();

        // Success message
        cy.get('[role="status"]').should('contain', 'deleted');
    });

    it('should handle formatting in messages', () => {
        cy.get('textarea[data-testid="message-input"]')
            .type('What is **property registration** and how does it work?');
        cy.get('button[data-testid="send-btn"]').click();

        // Response with formatting should be visible
        cy.get('[data-testid="assistant-message"] strong', { timeout: 10000 })
            .should('be.visible');
    });

    it('should handle code blocks in responses', () => {
        cy.get('textarea[data-testid="message-input"]')
            .type('Show me example documentation');
        cy.get('button[data-testid="send-btn"]').click();

        // Code block should be rendered
        cy.get('[data-testid="assistant-message"] pre', { timeout: 10000 })
            .should('be.visible');
    });

    it('should handle lists in responses', () => {
        cy.get('textarea[data-testid="message-input"]')
            .type('What are the steps for property registration?');
        cy.get('button[data-testid="send-btn"]').click();

        // List should be rendered
        cy.get('[data-testid="assistant-message"] li', { timeout: 10000 })
            .should('have.length.at.least', 1);
    });

    it('should copy message content', () => {
        cy.get('textarea[data-testid="message-input"]').type('Test message');
        cy.get('button[data-testid="send-btn"]').click();

        // User message hover copy button
        cy.get('[data-testid="user-message"]').first().within(() => {
            cy.get('button[data-testid="copy-btn"]').click();
        });

        cy.get('[role="status"]').should('contain', 'Copied');
    });
});

describe('Chat Accessibility E2E', () => {
    beforeEach(() => {
        cy.visit('http://localhost:3000/login');
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        cy.visit('http://localhost:3000/chat');
    });

    it('should have proper ARIA labels', () => {
        cy.get('textarea[data-testid="message-input"]')
            .should('have.attr', 'aria-label');

        cy.get('button[data-testid="send-btn"]')
            .should('have.attr', 'aria-label');
    });

    it('should support keyboard navigation', () => {
        cy.get('textarea[data-testid="message-input"]').type('Test');

        // Send with Ctrl+Enter
        cy.get('textarea[data-testid="message-input"]')
            .type('{ctrl}{enter}');

        // Message should be sent
        cy.get('[data-testid="message-list"]').should('contain', 'Test');
    });

    it('should announce messages to screen readers', () => {
        cy.get('textarea[data-testid="message-input"]').type('Test question');
        cy.get('button[data-testid="send-btn"]').click();

        // Should have aria-live region
        cy.get('[data-testid="message-list"]')
            .should('have.attr', 'aria-live', 'polite');
    });
});
