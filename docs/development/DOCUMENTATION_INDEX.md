# ConsultaRPP - Índice de Documentación

## Descripción General
ConsultaRPP es un chatbot inteligente para consultas legales sobre el Registro Público de la Propiedad. Sistema de Inteligencia Artificial con RAG (Retrieval-Augmented Generation).

---

## 📋 Main Documentation

### Getting Started
- [QUICK_START.md](./QUICK_START.md) - 5 minutos para empezar
- [README.md](../README.md) - Overview del proyecto
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitectura hexagonal

### Development
- [PHASE_2_REPORT.md](./PHASE_2_REPORT.md) - Infrastructure Implementation Complete
- [Project_History.md](./Project_History.md) - Evolución del proyecto
- [CHANGELOG.md](./CHANGELOG.md) - Changes by version

### Features & Skills
- [skills/document-parsing/SKILL.md](../skills/document-parsing/SKILL.md) - Document pipeline
- [skills/property-search/SKILL.md](../skills/property-search/SKILL.md) - Semantic search
- [skills/lease-analysis/SKILL.md](../skills/lease-analysis/SKILL.md) - Lease analysis
- [skills/requirements-extraction/SKILL.md](../skills/requirements-extraction/SKILL.md) - Extract requirements

### Deployment & Operations
- [RunPod_Deployment_Guide.md](./RunPod_Deployment_Guide.md) - Cloud deployment
- [OPTIMIZATION_DOCLING.md](./OPTIMIZATION_DOCLING.md) - Performance tuning

---

## 🏗️ Architecture

### Layers
1. **Domain Layer** - Pure business logic
   - Entities: User, Document, ChatSession, ChatMessage
   - Interfaces: Repository, VectorStore, FileStorage
   - Exceptions: Custom domain exceptions

2. **Application Layer** - Use cases & orchestration
   - DTOs: Data transfer objects
   - Use Cases: ProcessDocument, SearchDocuments, ChatQuery
   - Services: Business logic coordination

3. **Infrastructure Layer** - External integrations
   - Database: PostgreSQL + pgvector
   - Repositories: Concrete implementations
   - External: LLM, SeaweedFS, Docling

### Technology Stack
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React 19 + Vite + Tailwind
- **Database**: PostgreSQL + pgvector
- **Cache**: Valkey/Redis
- **Storage**: SeaweedFS
- **LLM**: Groq, Gemini, OpenAI, Anthropic
- **OCR**: Docling
- **Tasks**: Celery + Redis
- **Deployment**: Docker Compose

---

## 🚀 Quick Commands

### Setup & Start
```bash
make setup      # Initial setup
make start      # Start all services
make stop       # Stop all services
make health     # Check service health
```

### Development
```bash
make backend-dev    # Start backend locally
make frontend-dev   # Start frontend locally
make logs SERVICE=backend  # View logs
```

### Database
```bash
make db-init        # Initialize DB
make db-shell       # PostgreSQL shell
make db-migrate     # Run migrations
```

### Quality
```bash
make lint       # Run linters
make format     # Format code
make test       # Run tests
```

---

## 📁 File Structure

```
propquery/
├── backend/
│   ├── app/
│   │   ├── core/              # Config, logging, database
│   │   ├── domain/            # Business entities & interfaces
│   │   ├── application/       # DTOs & use cases
│   │   ├── infrastructure/    # DB, repos, external services
│   │   └── routes/            # API endpoints
│   ├── main.py                # FastAPI entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API calls
│   │   └── utils/             # Helpers
│   └── package.json
│
├── skills/                    # Domain-specific knowledge
│   ├── document-parsing/
│   ├── property-search/
│   ├── lease-analysis/
│   └── requirements-extraction/
│
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Service orchestration
└── Makefile                   # Development commands
```

---

## 🔑 Key Features

### Document Processing
- Upload PDFs, Word documents, images
- Automatic OCR with Docling
- Text extraction & cleaning
- Auto-chunking with overlap

### Intelligence
- Semantic search with pgvector
- Multi-provider LLM support
- RAG (Retrieval-Augmented Generation)
- Context-aware responses

### Legal Focus
- Property registry documents
- Lease analysis & extraction
- Requirements identification
- Cost calculations

---

## 📞 Support

### Documentation by Topic
- Configuration: `.env` section in `.env.example`
- Database: `ARCHITECTURE.md`
- Frontend: `frontend/README.md`
- Deployment: `RunPod_Deployment_Guide.md`

### Common Issues
1. Database connection → Check `DB_*` env vars
2. LLM not working → Verify `*_API_KEY` env vars
3. Frontend not loading → Check CORS settings
4. Docker issues → Run `docker-compose logs`

### Getting Help
- Check logs: `docker-compose logs -f [service]`
- Health check: `make health`
- Database: `make db-shell`

---

## 📊 Phase Progress

| Phase | Status | Details |
|-------|--------|---------|
| Phase 1 | ✅ Complete | Project structure & architecture |
| Phase 2 | ✅ Complete | Infrastructure & backend |
| Phase 3 | 🔄 In Progress | Frontend & integration |
| Phase 4 | ⏳ Planned | Deployment & optimization |

---

## 🔗 Related Resources

- [everything-claude-code](https://github.com/codecrafters-io/everything-claude-code) - Reference architecture
- [Docling Documentation](https://docs.docling.ai) - OCR & parsing
- [FastAPI Docs](https://fastapi.tiangolo.com) - Web framework
- [SQLAlchemy ORM](https://docs.sqlalchemy.org) - Database ORM
- [Celery Documentation](https://docs.celeryproject.io) - Task queue

---

**Last Updated**: Phase 2 Complete
**Status**: ✅ Ready for development and testing
