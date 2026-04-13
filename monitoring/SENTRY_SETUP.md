# Sentry Configuration for ConsultaRPP

## Backend Setup (Python/FastAPI)

### 1. Install Sentry SDK
```bash
pip install sentry-sdk
```

### 2. Configure in Backend Code

Add to `backend/app/core/config.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

if ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of traces for performance monitoring
        profiles_sample_rate=0.1,  # 10% profiling
        environment=ENVIRONMENT,
        release=VERSION,
        include_local_variables=True,
        attach_stacktrace=True,
    )
```

### 3. Add Sentry Middleware

```python
from sentry_sdk.integrations.fastapi import FastApiIntegration

app.add_middleware(SentryAsgiMiddleware)
```

## Frontend Setup (React)

### 1. Install Sentry SDK
```bash
npm install @sentry/react @sentry/tracing
```

### 2. Configure in React

Add to `frontend/src/main.tsx`:

```typescript
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

if (import.meta.env.VITE_ENV === "production") {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      new BrowserTracing(),
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    environment: import.meta.env.VITE_ENV,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}
```

### 3. Add Error Boundary

```typescript
const sentryEnhancedRoutes = Sentry.withSentryRouting(routes);

<ErrorBoundary fallback={<ErrorPage />}>
  <Routes>
    {sentryEnhancedRoutes}
  </Routes>
</ErrorBoundary>
```

## Configuration Details

### Exception Types Tracked

1. **Backend Exceptions**
   - Unhandled exceptions
   - Database errors
   - API request failures
   - Authentication errors
   - File upload failures

2. **Frontend Errors**
   - JavaScript exceptions
   - React component errors
   - API call failures
   - Network timeouts
   - User click tracking (optional)

### Performance Monitoring

```
Transactions tracked:
- API endpoint requests
- Database queries
- Frontend page loads
- Component rendering
- Redux state updates
```

### Release Tracking

```
Format: version-build-timestamp
Example: 1.0.0-build-20260407
```

## Alerting Configuration

### Create Alert Rules in Sentry

1. **Error Rate High** (> 1% in 5 min)
   - Action: Slack notification to #alerts-critical

2. **New Issues** 
   - Action: Email to ops-team@consulta-rpp.com

3. **Release Issues**
   - Action: Notify after first deployment

4. **Crash Rate** (> 2%)
   - Action: PagerDuty integration

## Environment Variables

Add to `.env.production`:

```
# Sentry Configuration
SENTRY_DSN=https://key@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_REPLAY_SAMPLE_RATE=0.1
SENTRY_PROFILE_SAMPLE_RATE=0.1
```

## Sentry Issues Dashboard

Access at: https://sentry.io/organizations/consulta-rpp/issues/

### Key Metrics
- Issues per day
- Event count by severity
- Affected users
- Release-based filtering
- Environment filtering

## Team Access

1. **Admin**: Full access (devops@consulta-rpp.com)
2. **Developers**: View/resolve access
3. **Ops**: View access + alerts

## Best Practices

1. **Context Information**
   ```python
   sentry_sdk.set_context("user", {
       "id": user.id,
       "email": user.email,
       "plan": user.plan,
   })
   ```

2. **Breadcrumbs**
   ```python
   sentry_sdk.capture_message("User searched", level="info")
   ```

3. **Tagged Issues**
   ```python
   sentry_sdk.set_tag("service", "backend")
   sentry_sdk.set_tag("endpoint", "/api/v1/search")
   ```

4. **Custom Metrics**
   ```typescript
   Sentry.captureMessage(`Document uploaded: ${size}MB`, "info");
   ```

## Maintenance

- Review issues weekly
- Update SDK monthly
- Test error tracking in staging before production
- Monitor quota usage (events/month)
- Archive resolved issues after 30 days
