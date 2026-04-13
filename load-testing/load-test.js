# k6 Load Testing Configuration for ConsultaRPP

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');
const searchDuration = new Trend('search_duration');
const uploadDuration = new Trend('upload_duration');
const chatDuration = new Trend('chat_duration');
const requestCount = new Counter('requests');

// Options
export const options = {
    // Test scenarios
    scenarios: {
        // Baseline load test
        baseline: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '5m', target: 50 },    // Ramp-up 50 users
                { duration: '10m', target: 50 },   // Stay 50 users
                { duration: '5m', target: 0 },     // Ramp-down
            ],
        },

        // Spike test
        spike: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '2m', target: 100 },   // Quick spike to 100
                { duration: '2m', target: 500 },   // Spike to 500
                { duration: '3m', target: 0 },     // Crash down
            ],
            startTime: '35m',
        },

        // Soak test (23h = 82800s)
        soak: {
            executor: 'constant-vus',
            vus: 50,
            duration: '82800s',
            startTime: '45m',
        },
    },

    // Thresholds
    thresholds: {
        'http_req_duration': ['p(95)<500', 'p(99)<1000'],
        'http_req_failed': ['rate<0.1'],
        'errors': ['rate<0.01'],
    },

    ext: {
        loadimpact: {
            projectID: 3476321,
            name: 'ConsultaRPP Performance Test'
        }
    }
};

// Test data
const baseURL = 'https://api.consulta-rpp.com';
const testUser = {
    email: 'test@consulta-rpp.com',
    password: 'TestPassword123!',
    token: null,
};

// Auth token
let authToken = '';

// Setup
export function setup() {
    // Login and get token
    const loginRes = http.post(`${baseURL}/api/v1/auth/login`, {
        email: testUser.email,
        password: testUser.password,
    });

    check(loginRes, {
        'login successful': (r) => r.status === 200,
    });

    return {
        token: loginRes.json('access_token'),
    };
}

// Main test function
export default function (data) {
    authToken = data.token;

    // Set auth header
    const headers = {
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
        },
    };

    group('Search API', () => {
        const searchRes = http.post(
            `${baseURL}/api/v1/search`,
            JSON.stringify({
                query: 'property tax',
                limit: 20,
            }),
            headers
        );

        check(searchRes, {
            'search successful': (r) => r.status === 200,
            'has results': (r) => r.json('results.length') > 0,
            'response time < 500ms': (r) => r.timings.duration < 500,
        });

        searchDuration.add(searchRes.timings.duration);
        errorRate.add(searchRes.status !== 200);
        requestCount.add(1);

        sleep(1);
    });

    group('Document Management', () => {
        // List documents
        const listRes = http.get(
            `${baseURL}/api/v1/documents?limit=20&offset=0`,
            { headers }
        );

        check(listRes, {
            'list successful': (r) => r.status === 200,
            'response time < 300ms': (r) => r.timings.duration < 300,
        });

        errorRate.add(listRes.status !== 200);
        requestCount.add(1);

        sleep(0.5);
    });

    group('Chat API', () => {
        const chatRes = http.post(
            `${baseURL}/api/v1/chat/message`,
            JSON.stringify({
                session_id: 'test-session',
                message: 'What is property tax compliance?',
            }),
            headers
        );

        check(chatRes, {
            'chat successful': (r) => r.status === 200,
            'has response': (r) => r.json('response') !== null,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
        });

        chatDuration.add(chatRes.timings.duration);
        errorRate.add(chatRes.status !== 200);
        requestCount.add(1);

        sleep(2);
    });

    group('Health Check', () => {
        const healthRes = http.get(`${baseURL}/health`);

        check(healthRes, {
            'health check passed': (r) => r.status === 200,
            'response time < 100ms': (r) => r.timings.duration < 100,
        });

        errorRate.add(healthRes.status !== 200);
        requestCount.add(1);
    });

    sleep(Math.random() * 3 + 1); // Random sleep 1-4 seconds
}

// Teardown
export function teardown(data) {
    // Logout
    http.post(`${baseURL}/api/v1/auth/logout`, null, {
        headers: {
            'Authorization': `Bearer ${authToken}`,
        },
    });
}
