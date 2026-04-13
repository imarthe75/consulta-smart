/**
 * Frontend Tests README
 * Complete guide for running and writing frontend tests
 */

# 🧪 Frontend Tests - Guía de Ejecución

## 📋 Descripción General

Suite completa de tests de frontend con Vitest:
- ✅ Tests de componentes (4 componentes)
- ✅ Tests de páginas (4 páginas)
- ✅ Tests de stores Zustand (3 stores)
- ✅ Tests de servicios API (24+ endpoints)

**Total: 100+ tests en 7 archivos**

---

## 🚀 Instalación de Dependencias

```bash
# Instalar Vitest y herramientas
npm install --save-dev vitest @vitest/ui
npm install --save-dev @testing-library/react @testing-library/jest-dom
npm install --save-dev @testing-library/user-event
npm install --save-dev msw  # Mock Service Worker
npm install --save-dev jsdom  # Virtual DOM

# O si usas pnpm/yarn
pnpm add -D vitest @testing-library/react msw
```

**Verifica que tengas en package.json**:
- vitest
- @testing-library/react
- @testing-library/jest-dom
- msw
- jsdom

---

## ▶️ Ejecución de Tests

### 1️⃣ Ejecutar TODOS los tests
```bash
npm run test
# o
pnpm test
```

### 2️⃣ Ejecutar con modo watch
```bash
npm run test -- --watch
pnpm test --watch
```

### 3️⃣ Ejecutar con UI interactivo
```bash
npm run test -- --ui
pnpm test --ui
```

### 4️⃣ Ejecutar por categoría

#### Tests de Componentes
```bash
npm run test -- tests/components/
```

#### Tests de Páginas
```bash
npm run test -- tests/pages/
```

#### Tests de Stores
```bash
npm run test -- tests/stores/
```

#### Tests de Servicios
```bash
npm run test -- tests/services/
```

### 5️⃣ Ejecutar test específico
```bash
npm run test -- Navigation.test.jsx
npm run test -- ChatInterface.test.jsx
npm run test -- API.test.js
```

---

## 📊 Reportes de Cobertura

### Generar reporte
```bash
npm run test -- --coverage

# O con más detalle
npm run test -- --coverage --reporter=verbose
```

### Ver reporte HTML
```bash
npm run test -- --coverage

# Abre en navegador
open coverage/index.html
```

### Targets de cobertura
- **Componentes**: >70% coverage
- **Páginas**: >60% coverage
- **Stores**: >80% coverage
- **Servicios**: >75% coverage
- **Global**: >60% coverage

---

## 🔧 Configuración

### vitest.config.ts
```typescript
export default defineConfig({
  test: {
    globals: true,           // Permite usar describe, it sin import
    environment: 'jsdom',    // Simula navegador
    setupFiles: ['./tests/setup.ts'],  // Configuración inicial
    coverage: {
      lines: 60,
      functions: 60,
      branches: 60,
      statements: 60,
    },
  },
});
```

### tests/setup.ts
Incluye:
- MSW (Mock Service Worker) para mocking de API
- localStorage/sessionStorage mocks
- window.matchMedia mock para responsive
- Cleanup automático

---

## 📝 Estructura de Archivos

```
frontend/tests/
├── setup.ts                 # Configuración global
├── components/
│   ├── Navigation.test.jsx          # Tests de Navigation
│   ├── ChatInterface.test.jsx       # Tests de Chat
│   ├── DocumentUpload.test.jsx      # Tests de Upload
│   └── SearchResults.test.jsx       # Tests de Búsqueda
├── pages/
│   └── Pages.test.jsx               # Tests de todas las páginas
├── stores/
│   └── Stores.test.js               # Tests de Zustand stores
├── services/
│   └── API.test.js                  # Tests de servicios API
└── __mocks__/
    ├── handlers.ts          # MSW handlers (opcional)
    └── ...
```

---

## 🎯 Patrones Comunes

### Testing de Componentes

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should render component', () => {
  render(<MyComponent />);
  expect(screen.getByText('text')).toBeInTheDocument();
});

it('should handle click', async () => {
  render(<MyComponent />);
  const button = screen.getByRole('button');
  await userEvent.click(button);
  expect(screen.getByText('clicked')).toBeInTheDocument();
});
```

### Testing de Stores Zustand

```typescript
import { renderHook, act } from '@testing-library/react';
import { useMyStore } from '../src/stores/myStore';

it('should update state', () => {
  const { result } = renderHook(() => useMyStore());
  
  act(() => {
    result.current.setValue('new value');
  });
  
  expect(result.current.value).toBe('new value');
});
```

### Testing de Servicios API

```typescript
import { mswServer } from '../setup';

it('should fetch data', async () => {
  mswServer.use(
    http.get('/api/endpoint', () => {
      return HttpResponse.json({ data: 'value' });
    })
  );

  const response = await fetch('/api/endpoint');
  expect(response.status).toBe(200);
});
```

---

## 🐛 Debugging

### Modo verbose
```bash
npm run test -- --reporter=verbose
```

### Debug individual
```bash
npm run test -- Navigation.test.jsx --reporter=verbose
```

### Inspeccionar DOM
```typescript
import { render, screen } from '@testing-library/react';

it('should show structure', () => {
  render(<MyComponent />);
  screen.debug();  // Imprime el DOM
});
```

---

## ✅ Checklist Pre-Commit

```bash
# 1. Tests básicos
npm run test

# 2. Cobertura mínima
npm run test -- --coverage

# 3. Sin errores de lint
npm run lint

# 4. Build exitoso (opcional)
npm run build
```

---

## 📊 Métricas Actuales

**Tests Creados**: 100+
- Componentes: 25+ tests
- Páginas: 15+ tests
- Stores: 30+ tests
- Servicios: 30+ tests

**Cobertura Esperada**: ~60-70%
- Componentes: 70%
- Páginas: 60%
- Stores: 80%
- Servicios: 75%

**Tiempo de Ejecución**: ~10-15 segundos

---

## 🚀 Integrando con CI/CD

### GitHub Actions
```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm run test
      - run: npm run test -- --coverage
```

### Script en package.json
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:watch": "vitest --watch"
  }
}
```

---

## 🔍 Troubleshooting

### Tests no se encuentran
```bash
# Verificar que los archivos cumplan patrón
# *.test.{ts,tsx,js,jsx}

# Listar tests encontrados
npm run test -- --list
```

### localStorage/sessionStorage no funciona
```typescript
// Ya está mockeado en setup.ts
// Pero si necesitas reset manual
localStorage.clear();
sessionStorage.clear();
```

### MSW no intercepta requests
```typescript
import { mswServer } from '../setup';

// Verificar que el handler coincida
mswServer.use(
  http.get('http://localhost:3003/api/endpoint', () => {
    return HttpResponse.json({ data: 'value' });
  })
);
```

### React Router no funciona en tests
```typescript
import { BrowserRouter } from 'react-router-dom';

// Envuelve el componente
render(
  <BrowserRouter>
    <MyComponent />
  </BrowserRouter>
);
```

---

## 📚 Recursos

- [Vitest Docs](https://vitest.dev/)
- [Testing Library Docs](https://testing-library.com/)
- [MSW Documentation](https://mswjs.io/)
- [React Testing Best Practices](https://kentcdodds.com/blog)

---

## ✨ Próximos Pasos

1. ✅ Setup y configuración (DONE)
2. ✅ Tests de componentes (DONE)
3. ✅ Tests de páginas (DONE)
4. ✅ Tests de stores (DONE)
5. ✅ Tests de servicios (DONE)
6. ⏳ E2E tests con Cypress
7. ⏳ Integration tests
8. ⏳ Performance testing

---

**Estado Overall**: Phase 4B - Frontend Tests = 100% ✨ | Phase 4 = 50%

**Próxima fase**: E2E tests con Cypress (10-15 scenarios)
