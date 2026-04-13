# ConsultaRPP - Frontend React 19

Frontend moderno construido con React 19, Vite, Tailwind CSS y Axios.

## 🚀 Características

- ✨ Chat inteligente con sesiones persistentes
- 📄 Carga y gestión de documentos
- 🔍 Búsqueda semántica en documentos
- 🔐 Autenticación segura con JWT
- 🌙 Interfaz moderna y responsiva
- 🇲🇽 100% en Español Mexicano
- ⚡ Vite para desarrollo rápido

## 📋 Requisitos

- Node.js 18+
- npm o yarn

## 🔧 Instalación

```bash
cd frontend
npm install
```

## 🏃 Desarrollo

```bash
npm run dev
```

La aplicación se ejecutará en `http://localhost:5173`

## 🏗️ Estructura

```
src/
├── components/          # Componentes React reutilizables
│   ├── Navigation.jsx   # Navegación lateral
│   ├── ChatInterface.jsx # Chat principal
│   ├── DocumentUpload.jsx # Carga de archivos
│   └── SearchResults.jsx # Resultados de búsqueda
├── pages/              # Páginas de la aplicación
│   ├── ChatPage.jsx
│   ├── DocumentsPage.jsx
│   ├── ResultsPage.jsx
│   └── LoginPage.jsx
├── stores/             # Zustand state management
│   ├── authStore.js
│   ├── chatStore.js
│   └── documentStore.js
├── services/           # Servicios API
│   └── api.js
├── i18n/               # Internacionalización (i18n)
│   └── es.js           # Traducciones español
├── App.jsx
├── main.jsx
└── index.css
```

## 🔌 API Integration

El frontend se conecta al backend FastAPI en `http://localhost:8000/api/v1`

**Endpoints principales:**
- `POST /auth/login` - Iniciar sesión
- `POST /auth/register` - Registro
- `POST /documents/upload` - Cargar documentos
- `GET /documents` - Listar documentos
- `POST /chat/sessions` - Crear sesión de chat
- `POST /chat/query` - Enviar consulta

## 📦 Dependencias Principales

- **React 19** - UI Framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Lucide React** - Icons
- **clsx** - Conditional className

## 🎨 Theming

Los colores principales se encuentran en `tailwind.config.js`:

- Primary: `#1E40AF` (Azul)
- Secondary: `#7C3AED` (Púrpura)
- Accent: `#F59E0B` (Ámbar)

## 📝 Variables de Entorno

Crear `.env` basado en `.env.example`:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=ConsultaRPP
VITE_API_TIMEOUT=30000
```

## 🚢 Build para Producción

```bash
npm run build
```

La salida estará en `dist/`

## 🐛 Troubleshooting

### CORS errors
- Verifica que el backend tiene CORS habilitado
- Asegúrate que `VITE_API_URL` apunta al backend correcto

### API timeouts
- Aumenta `VITE_API_TIMEOUT` en `.env`
- Verifica estado del backend con `/health`

## 📄 Licencia

Todos los derechos reservados - ConsultaRPP 2026
