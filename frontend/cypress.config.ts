// Cypress configuration for E2E testing
// cypress.config.ts

import { defineConfig } from 'cypress';

export default defineConfig({
    e2e: {
        baseUrl: 'http://localhost:3000',
        viewportWidth: 1280,
        viewportHeight: 720,
        video: true,
        videoCompression: 32,
        screenshotOnRunFailure: true,
        chromeWebSecurity: false,

        // Test patterns
        specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
        supportFile: 'cypress/support/e2e.ts',

        // Timeouts
        defaultCommandTimeout: 10000,
        requestTimeout: 10000,
        responseTimeout: 10000,

        // Setup hooks
        setupNodeEvents(on, config) {
            // Implement node event listeners here

            // Example: Log to console
            on('task', {
                log(message) {
                    console.log(message);
                    return null;
                },
            });

            return config;
        },

        env: {
            // API endpoints
            apiUrl: 'http://localhost:3003',
            // Test user credentials
            testEmail: 'test@example.com',
            testPassword: 'TestPassword123!',
            // Test timeouts
            networkDelay: 0,
            loadingTimeout: 5000,
        },
    },

    component: {
        devServer: {
            framework: 'react',
            bundler: 'vite',
        },
    },
});
