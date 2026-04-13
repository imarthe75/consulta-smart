# Requirements Extraction & Cost Calculator Skill

## Overview

Extracción automática de requisitos y costos de trámites del Registro Público de la Propiedad.

## Folder Structure

```
requirements-extraction/
├── SKILL.md              # Documentación completa
├── README.md             # Este archivo
├── examples/             # Documentos de ejemplo
│   └── sample_trami_docs.pdf
├── schemas/              # Esquemas Pydantic
│   ├── trami_schema.py
│   ├── requirement.py
│   └── cost.py
├── services/             # Servicios de extracción
│   └── requirements_extractor.py
└── tests/                # Tests
    └── test_extraction.py
```

## Key Components

### 1. **Requirements Extractor Service**
- Analiza documentos con LLM
- Extrae requisitos estructurados
- Clasifica por tipo (obligatorio, condicional, opcional)

### 2. **Cost Calculator**
- Calcula costos totales
- Maneja montos variables
- Agrupa por categoría

### 3. **Trami Schema**
- Representa información de un trámite
- Validado con Pydantic
- JSON serializable

### 4. **Timeline Estimator**
- Estima tiempo de trámite
- Basado en datos históricos
- Actualizable

## Implementation Checklist

- [ ] Crear servicio extractor con LLM
- [ ] Definir schemas (Requirement, Cost, TramiSchema)
- [ ] Implementar validación de datos
- [ ] Crear use case para extracción
- [ ] Agregar API endpoints
- [ ] Crear fronted UI para mostrar resultados
- [ ] Tests de extracción
- [ ] Integration tests

## Quick Start

```python
from app.application.usecases import ExtractRequirementsUseCase

usecase = ExtractRequirementsUseCase(
    service=requirements_extractor,
    doc_repo=doc_repository
)

schema = await usecase.execute(document_id="doc_123")

print(f"Trámite: {schema.name}")
print(f"Costo Total: ${schema.calculate_total_cost()}")
print(f"Tiempo estimado: {schema.estimated_time_days} días")
```

## Frontend Example

```typescript
// Display requirements and costs
<div className="trami-details">
  <h2>{trami.name}</h2>
  
  <CostTable costs={trami.costs} />
  <RequirementsList requirements={trami.requirements} />
  <TimelineInfo days={trami.estimated_time_days} />
</div>
```

## Performance Targets

- **Extraction Time**: < 5s per document
- **Accuracy**: > 95%
- **False Positives**: < 2%

## Related Skills

- 🔗 [Document Parsing](../document-parsing/SKILL.md)
- 🔗 [Property Search](../property-search/SKILL.md)

---

**Status**: 🟡 In Development  
**Last Updated**: 2026-04-07
