/**
 * Cypress Support File for E2E Tests
 * Global setup and custom commands
 */

import '@cypress/code-coverage/support';

// Example: Custom command for login
Cypress.Commands.add('login', (email: string, password: string) => {
    cy.visit('/login');
    cy.get('input[name="email"]').type(email);
    cy.get('input[name="password"]').type(password);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
});

// Example: Custom command for document upload
Cypress.Commands.add('uploadDocument', (filePath: string) => {
    cy.get('button[data-testid="upload-btn"]').click();
    cy.get('input[type="file"]').attachFile(filePath);
    cy.get('button[data-testid="submit-upload"]').click();
});

// Example: Custom command for creating chat session
Cypress.Commands.add('createChatSession', (title: string) => {
    cy.get('button[data-testid="new-chat-btn"]').click();
    cy.get('[role="dialog"]').should('be.visible');
    cy.get('input[name="title"]').type(title);
    cy.get('button[data-testid="create-session-btn"]').click();
});

// Global error handling
Cypress.on('uncaught:exception', (err) => {
    // Return false to prevent Cypress from failing the test
    // For specific errors that are expected
    if (err.message.includes('Expected')) {
        return false;
    }
});

// Wait for app to be ready
beforeEach(() => {
    cy.visit('/');
    cy.window().should('have.property', 'React');
});

// After each test: Clear application state
afterEach(() => {
    // Clear localStorage
    cy.window().then((win) => {
        win.localStorage.clear();
    });

    // Clear sessionStorage
    cy.window().then((win) => {
        win.sessionStorage.clear();
    });
});
