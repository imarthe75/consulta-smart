/**
 * Phase 4D - E2E Tests
 * Authentication and User Flows
 */

describe('Authentication Flow E2E', () => {
    const baseUrl = 'http://localhost:3000';

    beforeEach(() => {
        cy.visit(`${baseUrl}/login`);
    });

    it('should register a new user successfully', () => {
        // Navigate to register page
        cy.get('a[href="/register"]').click();
        cy.url().should('include', '/register');

        // Fill registration form
        const testEmail = `user-${Date.now()}@example.com`;
        cy.get('input[name="email"]').type(testEmail);
        cy.get('input[name="username"]').type(`testuser-${Date.now()}`);
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('input[name="confirmPassword"]').type('TestPassword123!');
        cy.get('input[name="fullName"]').type('Test User');

        // Accept terms
        cy.get('input[type="checkbox"]').click();

        // Submit form
        cy.get('button[type="submit"]').click();

        // Should redirect to dashboard or login
        cy.url().should('match', /\/(login|dashboard)/);
        cy.get('[role="status"]').should('contain', 'successfully');
    });

    it('should login with valid credentials', () => {
        // Fill login form
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');

        // Submit form
        cy.get('button[type="submit"]').click();

        // Should navigate to dashboard
        cy.url().should('include', '/dashboard');

        // Should show user's name in header
        cy.get('[data-testid="user-profile"]').should('be.visible');
    });

    it('should show error for invalid credentials', () => {
        cy.get('input[name="email"]').type('wrong@example.com');
        cy.get('input[name="password"]').type('wrongpassword');

        cy.get('button[type="submit"]').click();

        // Should show error message
        cy.get('[role="alert"]').should('contain', 'Invalid credentials');

        // Should remain on login page
        cy.url().should('include', '/login');
    });

    it('should handle password reset flow', () => {
        cy.get('a[href*="forgot-password"]').click();
        cy.url().should('include', '/forgot-password');

        cy.get('input[name="email"]').type('test@example.com');
        cy.get('button[type="submit"]').click();

        // Should show confirmation message
        cy.get('[role="status"]').should('contain', 'reset link');
        cy.get('[role="status"]').should('contain', 'email');
    });

    it('should logout successfully', () => {
        // First, login
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        cy.url().should('include', '/dashboard');

        // Click logout button
        cy.get('[data-testid="user-menu"]').click();
        cy.get('[data-testid="logout-button"]').click();

        // Should redirect to login
        cy.url().should('include', '/login');
    });
});

describe('Invalid Authentication E2E', () => {
    beforeEach(() => {
        cy.visit('http://localhost:3000/dashboard');
    });

    it('should redirect to login when not authenticated', () => {
        cy.url().should('include', '/login');
    });

    it('should prevent access to protected routes', () => {
        cy.visit('http://localhost:3000/chat');
        cy.url().should('include', '/login');
    });
});
