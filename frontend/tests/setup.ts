/**
 * Test Setup Configuration
 * Vitest + React Testing Library + MSW
 */

import { expect, afterEach, beforeEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Cleanup after each test
afterEach(() => {
    cleanup();
});

// Mock window.matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock,
});

// MSW Server Setup
export const mswServer = setupServer(
    // Default handlers - can be overridden in tests
    http.get('http://localhost:3003/health', () => {
        return HttpResponse.json({ status: 'ok', version: '1.0.0' });
    }),

    http.post('http://localhost:3003/api/v1/auth/login', () => {
        return HttpResponse.json({
            token: 'mock_jwt_token',
            user: {
                id: 'user-123',
                email: 'test@example.com',
                username: 'testuser',
            },
        });
    }),

    http.get('http://localhost:3003/api/v1/documents', () => {
        return HttpResponse.json([
            {
                id: 'doc-1',
                filename: 'test.pdf',
                status: 'processed',
                createdAt: new Date().toISOString(),
            },
        ]);
    }),

    http.get('http://localhost:3003/api/v1/chat/sessions', () => {
        return HttpResponse.json([
            {
                id: 'session-1',
                title: 'Test Chat',
                createdAt: new Date().toISOString(),
            },
        ]);
    }),

    http.get('http://localhost:3003/api/v1/search', () => {
        return HttpResponse.json([
            {
                id: 'result-1',
                content: 'Search result',
                score: 0.95,
            },
        ]);
    })
);

// Enable MSW requests interception
beforeEach(() => {
    mswServer.listen({ onUnhandledRequest: 'warn' });
});

// Cleanup MSW after tests
afterEach(() => {
    mswServer.resetHandlers();
    mswServer.close();
});

// Global test utilities
export const waitFor = (callback: () => void, options = {}) => {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Wait timeout'));
        }, 3000);

        const interval = setInterval(() => {
            try {
                callback();
                clearInterval(interval);
                clearTimeout(timeout);
                resolve(true);
            } catch (e) {
                // Continue waiting
            }
        }, 50);
    });
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
    constructor() { }
    disconnect() { }
    observe() { }
    takeRecords() {
        return [];
    }
    unobserve() { }
} as any;

// Suppress console errors in tests (optional)
const originalError = console.error;
beforeEach(() => {
    console.error = (...args: any[]) => {
        if (
            typeof args[0] === 'string' &&
            args[0].includes('Warning: useLayoutEffect does nothing on the server')
        ) {
            return;
        }
        originalError.call(console, ...args);
    };
});

afterEach(() => {
    console.error = originalError;
});
