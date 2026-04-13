/**
 * Phase 4D - E2E Tests
 * Document Upload and Processing
 */

describe('Document Upload Flow E2E', () => {
    const baseUrl = 'http://localhost:3000';

    beforeEach(() => {
        // Login first
        cy.visit(`${baseUrl}/login`);
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        // Navigate to documents page
        cy.url().should('include', '/dashboard');
        cy.get('a[href*="documents"]').click();
        cy.url().should('include', '/documents');
    });

    it('should upload a single PDF file', () => {
        // Click upload button
        cy.get('button[data-testid="upload-btn"]').click();

        // Should show upload modal
        cy.get('[role="dialog"]').should('be.visible');

        // Upload file
        cy.get('input[type="file"]').attachFile('sample.pdf');

        // Should show file in list
        cy.get('[data-testid="file-list"]').should('contain', 'sample.pdf');

        // Submit upload
        cy.get('button[data-testid="submit-upload"]').click();

        // Should show progress
        cy.get('[role="progressbar"]').should('be.visible');

        // Should complete
        cy.get('[data-testid="upload-success"]', { timeout: 10000 }).should('be.visible');
    });

    it('should upload multiple files', () => {
        cy.get('button[data-testid="upload-btn"]').click();
        cy.get('[role="dialog"]').should('be.visible');

        // Upload multiple files
        cy.get('input[type="file"]').attachFile('sample1.pdf');
        cy.get('input[type="file"]').attachFile('sample2.pdf');
        cy.get('input[type="file"]').attachFile('sample3.pdf');

        // Should show all files
        cy.get('[data-testid="file-list"] li').should('have.length', 3);

        // Submit
        cy.get('button[data-testid="submit-upload"]').click();

        // Should upload all files
        cy.get('[data-testid="upload-success"]', { timeout: 15000 }).should('be.visible');
    });

    it('should display upload progress', () => {
        cy.get('button[data-testid="upload-btn"]').click();
        cy.get('input[type="file"]').attachFile('large.pdf');
        cy.get('button[data-testid="submit-upload"]').click();

        // Progress bar should be visible and updating
        cy.get('[role="progressbar"]').should('be.visible');
        cy.get('[data-testid="upload-percentage"]').invoke('text').should('match', /\d+%/);
    });

    it('should handle upload errors', () => {
        cy.get('button[data-testid="upload-btn"]').click();
        cy.get('input[type="file"]').attachFile('invalid.txt');
        cy.get('button[data-testid="submit-upload"]').click();

        // Should show error message
        cy.get('[role="alert"]', { timeout: 5000 }).should('contain', 'only PDF files');
    });

    it('should show uploaded documents in list', () => {
        // Should display documents table
        cy.get('[data-testid="documents-table"]').should('be.visible');

        // Each document should have actions
        cy.get('[data-testid="documents-table"] tr').each(($row) => {
            cy.wrap($row).should('contain', 'Delete');
            cy.wrap($row).should('contain', 'View Details');
        });
    });

    it('should delete a document', () => {
        // Get first document delete button
        cy.get('[data-testid="documents-table"] tr').first().within(() => {
            cy.get('button[data-testid="delete-btn"]').click();
        });

        // Should show confirmation dialog
        cy.get('[role="dialog"]').should('contain', 'confirm');

        // Confirm deletion
        cy.get('button[data-testid="confirm-delete"]').click();

        // Should show success message
        cy.get('[role="status"]').should('contain', 'deleted');
    });

    it('should track document processing status', () => {
        // Document should show processing status badge
        cy.get('[data-testid="documents-table"]').within(() => {
            cy.should('contain', 'Processing') || cy.should('contain', 'Completed');
        });

        // After processing completes, should show "Completed"
        cy.get('[data-testid="status-badge"]', { timeout: 30000 })
            .should('contain', 'Completed');
    });

    it('should drag and drop file for upload', () => {
        // Show drag and drop area
        cy.get('button[data-testid="upload-btn"]').click();
        cy.get('[data-testid="drag-drop-area"]').should('be.visible');

        // Simulate drag and drop
        cy.get('[data-testid="drag-drop-area"]').selectFile('sample.pdf', { action: 'drag-drop' });

        // File should be selected
        cy.get('[data-testid="file-list"]').should('contain', 'sample.pdf');
    });
});

describe('Document Details E2E', () => {
    beforeEach(() => {
        cy.visit('http://localhost:3000/login');
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        cy.visit('http://localhost:3000/documents');
        cy.get('[data-testid="documents-table"] tr').first().within(() => {
            cy.get('a[data-testid="view-details"]').click();
        });
    });

    it('should display document information', () => {
        // Should show document title
        cy.get('[data-testid="document-title"]').should('be.visible');

        // Should show metadata
        cy.get('[data-testid="document-metadata"]').should('contain', 'Uploaded');
        cy.get('[data-testid="document-metadata"]').should('contain', 'Pages');
    });

    it('should display document preview', () => {
        cy.get('[data-testid="document-preview"]').should('be.visible');
        cy.get('iframe[data-testid="pdf-viewer"]').should('exist');
    });
});
