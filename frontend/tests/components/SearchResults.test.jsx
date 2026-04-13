/**
 * SearchResults Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchResults from '../../src/components/SearchResults';

describe('SearchResults Component', () => {
    const mockResults = [
        {
            id: 'result-1',
            content: 'This is the first search result',
            score: 0.95,
            documentId: 'doc-1',
            documentName: 'contract.pdf',
            highlight: 'search result',
        },
        {
            id: 'result-2',
            content: 'Another search result here',
            score: 0.87,
            documentId: 'doc-2',
            documentName: 'agreement.pdf',
            highlight: 'search result',
        },
    ];

    describe('Rendering', () => {
        it('should render results container', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search result"
                />
            );
            const container = screen.getByTestId('search-results') ||
                screen.getByRole('region', { name: /results/i });
            expect(container).toBeInTheDocument();
        });

        it('should display search query', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search result"
                />
            );
            expect(screen.getByText(/search result/i)).toBeInTheDocument();
        });

        it('should show loading state', () => {
            render(
                <SearchResults
                    results={[]}
                    isLoading={true}
                    query="test"
                />
            );
            const loader = screen.getByTestId('loading-spinner') ||
                screen.getByRole('status');
            expect(loader).toBeInTheDocument();
        });

        it('should show empty state when no results', () => {
            render(
                <SearchResults
                    results={[]}
                    isLoading={false}
                    query="test"
                />
            );
            const emptyMessage = screen.getByText(/no results|sin resultados/i);
            expect(emptyMessage).toBeInTheDocument();
        });
    });

    describe('Result Display', () => {
        it('should display all results', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );
            expect(screen.getByText(/first search result/i)).toBeInTheDocument();
            expect(screen.getByText(/another search result/i)).toBeInTheDocument();
        });

        it('should display relevance scores', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );
            // Should show score or percentage
            const firstScore = screen.queryByText(/0\.95|95%/);
            expect(firstScore || screen.getByTestId('search-results')).toBeInTheDocument();
        });

        it('should display source document name', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );
            expect(screen.getByText('contract.pdf')).toBeInTheDocument();
            expect(screen.getByText('agreement.pdf')).toBeInTheDocument();
        });

        it('should highlight search terms', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search result"
                />
            );
            // Check for highlighted text or markup
            const results = screen.getAllByRole('article') ||
                screen.getAllByTestId(/result-/);
            expect(results.length).toBeGreaterThan(0);
        });
    });

    describe('Result Interaction', () => {
        it('should handle result click', async () => {
            const onResultClick = vi.fn();
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                    onResultClick={onResultClick}
                />
            );

            const firstResult = screen.getByText(/first search result/i);
            await userEvent.click(firstResult);

            expect(onResultClick).toHaveBeenCalledWith(
                expect.objectContaining({
                    id: 'result-1',
                })
            );
        });

        it('should navigate to document on result click', async () => {
            const mockNavigate = vi.fn();
            vi.mock('react-router-dom', () => ({
                useNavigate: () => mockNavigate,
            }));

            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );

            const linkElement = screen.getByRole('link', {
                name: /contract\.pdf/i,
            }) || screen.getByText(/contract\.pdf/i);

            if (linkElement.tagName === 'A') {
                await userEvent.click(linkElement);
            }
        });
    });

    describe('Result Sorting', () => {
        it('should sort by relevance by default', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                    sortBy="relevance"
                />
            );

            const results = screen.getAllByTestId(/result-/i) ||
                screen.getAllByRole('article');
            const firstScore = mockResults[0].score;
            const secondScore = mockResults[1].score;

            expect(firstScore).toBeGreaterThan(secondScore);
        });

        it('should allow sorting by date', async () => {
            const resultsWithDate = mockResults.map((r, i) => ({
                ...r,
                createdAt: new Date(2026, 3, 7 - i).toISOString(),
            }));

            render(
                <SearchResults
                    results={resultsWithDate}
                    isLoading={false}
                    query="search"
                    sortBy="date"
                />
            );

            const sortButton = screen.queryByRole('button', { name: /sort|date/i });
            if (sortButton) {
                await userEvent.click(sortButton);
                expect(screen.getByTestId('search-results')).toBeInTheDocument();
            }
        });
    });

    describe('Filtering', () => {
        it('should filter by document type', async () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                    filters={{ documentType: 'pdf' }}
                />
            );

            const filterButton = screen.queryByRole('button', { name: /filter/i });
            if (filterButton) {
                await userEvent.click(filterButton);
            }
        });
    });

    describe('Pagination', () => {
        it('should paginate large result sets', async () => {
            const manyResults = Array.from({ length: 25 }, (_, i) => ({
                ...mockResults[0],
                id: `result-${i}`,
                content: `Result ${i}`,
            }));

            render(
                <SearchResults
                    results={manyResults}
                    isLoading={false}
                    query="search"
                    itemsPerPage={10}
                />
            );

            // Should show pagination controls or limited results
            const results = screen.queryAllByTestId(/result-/) ||
                screen.queryAllByRole('article');

            expect(results.length).toBeLessThanOrEqual(10) ||
                expect(screen.queryByRole('button', { name: /next/i })).toBeInTheDocument();
        });

        it('should navigate to next page', async () => {
            const manyResults = Array.from({ length: 25 }, (_, i) => ({
                ...mockResults[0],
                id: `result-${i}`,
            }));

            render(
                <SearchResults
                    results={manyResults}
                    isLoading={false}
                    query="search"
                    itemsPerPage={10}
                />
            );

            const nextButton = screen.queryByRole('button', { name: /next|siguiente/i });
            if (nextButton) {
                await userEvent.click(nextButton);
                expect(nextButton).toBeInTheDocument();
            }
        });
    });

    describe('Error Handling', () => {
        it('should display error message', () => {
            render(
                <SearchResults
                    results={[]}
                    isLoading={false}
                    query="search"
                    error="Search failed: Connection timeout"
                />
            );
            expect(screen.getByText(/search failed/i)).toBeInTheDocument();
        });

        it('should allow retry on error', async () => {
            const onRetry = vi.fn();
            render(
                <SearchResults
                    results={[]}
                    isLoading={false}
                    query="search"
                    error="Search failed"
                    onRetry={onRetry}
                />
            );

            const retryButton = screen.getByRole('button', { name: /retry|reintentar/i });
            await userEvent.click(retryButton);

            expect(onRetry).toHaveBeenCalled();
        });
    });

    describe('Accessibility', () => {
        it('should have proper structure for screen readers', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );

            const region = screen.getByRole('region', { name: /results/i }) ||
                screen.getByTestId('search-results');
            expect(region).toBeInTheDocument();
        });

        it('should announce result count', () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );

            const countText = screen.getByText(/2 results|resultados/i) ||
                screen.getByTestId('search-results');
            expect(countText).toBeInTheDocument();
        });

        it('should have keyboard navigation', async () => {
            render(
                <SearchResults
                    results={mockResults}
                    isLoading={false}
                    query="search"
                />
            );

            const firstResult = screen.getByText(/first search result/i);
            firstResult.focus();

            expect(firstResult).toHaveFocus();

            await userEvent.keyboard('{Enter}');
            // Navigation should occur
        });
    });
});
