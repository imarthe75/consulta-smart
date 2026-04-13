/**
 * Phase 4D - E2E Tests
 * Search and Results
 */

describe('Search Flow E2E', () => {
    const baseUrl = 'http://localhost:3000';

    beforeEach(() => {
        cy.visit(`${baseUrl}/login`);
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        cy.url().should('include', '/dashboard');
    });

    it('should perform semantic search', () => {
        cy.get('[data-testid="search-input"]').type('property registration Quintana Roo');
        cy.get('button[data-testid="search-btn"]').click();

        cy.url().should('include', '/search');

        // Results should be displayed
        cy.get('[data-testid="search-results"]').should('be.visible');
        cy.get('[data-testid="search-result-item"]').should('have.length.at.least', 1);
    });

    it('should filter search results by state', () => {
        cy.get('[data-testid="search-input"]').type('property registration');
        cy.get('button[data-testid="search-btn"]').click();

        // Apply state filter
        cy.get('select[data-testid="state-filter"]').select('quintana_roo');

        // Results should update
        cy.get('[data-testid="search-results"] [data-testid="result-state"]')
            .each(($item) => {
                cy.wrap($item).should('contain', 'Quintana Roo');
            });
    });

    it('should sort search results', () => {
        cy.get('[data-testid="search-input"]').type('registration');
        cy.get('button[data-testid="search-btn"]').click();

        // Sort by relevance
        cy.get('select[data-testid="sort-by"]').select('relevance');

        // Should show sorted results
        cy.get('[data-testid="search-results"]').should('contain', 'Relevance');
    });

    it('should display search result details', () => {
        cy.get('[data-testid="search-input"]').type('usufruct');
        cy.get('button[data-testid="search-btn"]').click();

        // Click on first result
        cy.get('[data-testid="search-result-item"]').first().click();

        // Should navigate to result details or expand
        cy.get('[data-testid="result-detail"]').should('be.visible');
        cy.should('contain', 'usufruct');
    });

    it('should show search result highlighting', () => {
        cy.get('[data-testid="search-input"]').type('property');
        cy.get('button[data-testid="search-btn"]').click();

        // Search terms should be highlighted
        cy.get('[data-testid="search-result-item"] mark')
            .should('contain', 'property');
    });

    it('should display no results message', () => {
        cy.get('[data-testid="search-input"]').type('xyzabc123nonexistent');
        cy.get('button[data-testid="search-btn"]').click();

        ci.get('[data-testid="no-results"]')
            .should('contain', 'No results found');
    });

    it('should paginate search results', () => {
        cy.get('[data-testid="search-input"]').type('property');
        cy.get('button[data-testid="search-btn"]').click();

        // If there are many results
        cy.get('[data-testid="pagination"]').then(($pagination) => {
            if ($pagination.find('button').length > 0) {
                // Click next page
                cy.get('button[data-testid="next-page"]').click();

                // Page should update
                cy.get('[data-testid="page-info"]').should('contain', '2');
            }
        });
    });
});

describe('Search within Document E2E', () => {
    beforeEach(() => {
        cy.visit('http://localhost:3000/login');
        cy.get('input[name="email"]').type('test@example.com');
        cy.get('input[name="password"]').type('TestPassword123!');
        cy.get('button[type="submit"]').click();

        // Navigate to documents
        cy.get('a[href*="documents"]').click();

        // Open first document
        cy.get('[data-testid="documents-table"] tr').first().within(() => {
            cy.get('a[data-testid="view-details"]').click();
        });
    });

    it('should search within document', () => {
        cy.get('input[data-testid="document-search"]').type('usufruct');
        cy.get('button[data-testid="search-doc-btn"]').click();

        // Matches should be highlighted
        cy.get('[data-testid="document-preview"] mark')
            .should('contain', 'usufruct');
    });

    it('should navigate through document search matches', () => {
        cy.get('input[data-testid="document-search"]').type('property');
        cy.get('button[data-testid="search-doc-btn"]').click();

        // Should show match count
        cy.get('[data-testid="match-count"]').should('match', /\d+ of \d+/);

        // Navigate to next match
        cy.get('button[data-testid="next-match"]').click();

        // Highlight should move to next
        cy.get('[data-testid="document-preview"]').should('be.visible');
    });
});

describe('Search Accessibility E2E', () => {
    beforeEach(() => {
        cy.visit('http://localhost:3000/dashboard');
    });

    it('should have accessible search input', () => {
        cy.get('[data-testid="search-input"]')
            .should('have.attr', 'aria-label')
            .should('have.attr', 'placeholder');
    });

    it('should show search suggestions', () => {
        cy.get('[data-testid="search-input"]').type('prop');

        // Suggestions should appear
        cy.get('[data-testid="search-suggestions"]').should('be.visible');
        cy.get('[data-testid="search-suggestion-item"]').should('have.length.at.least', 1);
    });

    it('should support arrow key navigation in suggestions', () => {
        cy.get('[data-testid="search-input"]').type('prop');

        // Arrow down to first suggestion
        cy.get('[data-testid="search-input"]').type('{downarrow}');

        // First suggestion should be highlighted
        cy.get('[data-testid="search-suggestion-item"]').first()
            .should('have.class', 'highlighted');
    });
});
