# Lease Analysis & Contract Parsing Skill

## Overview

Análisis automático de contratos usando LangGraph para extraer información estructurada.

## Folder Structure

```
lease-analysis/
├── SKILL.md              # Documentación completa
├── README.md             # Este archivo
├── examples/             # Contratos de ejemplo
│   ├── sample_lease_1.pdf
│   ├── sample_lease_2.pdf
│   └── extraction_samples.json
├── prompts/              # LLM prompts optimizados
│   ├── entity_extraction.md
│   ├── clause_detection.md
│   └── risk_analysis.md
├── agents/               # LangGraph agents
│   └── lease_analyzer_agent.py
└── tests/                # Tests
    └── test_lease_analysis.py
```

## Key Components

### 1. **LangGraph Workflow**
- Orquesta análisis multi-stage
- Entity extraction, clause detection, risk analysis
- Checkpointing para debugging

### 2. **Prompt Engineering**
- Prompts optimizados para extracción de información
- Few-shot examples incluidos
- Validación de JSON output

### 3. **Schema Validation**
- Pydantic models para validar outputs
- Detección de campos faltantes
- Recovery de errores

### 4. **Caching**
- Cache de análisis de contratos similares
- Reduce llamadas a LLM

## Implementation Checklist

- [ ] Crear LangGraph workflow
- [ ] Definir prompts por node
- [ ] Crear schema de salida (Pydantic)
- [ ] Implementar entity extraction node
- [ ] Implementar clause detection node
- [ ] Implementar risk analysis node
- [ ] Agregar tests end-to-end
- [ ] Integrar con API endpoints

## Quick Start

```python
from app.agents.lease_analyzer_agent import LeaseAnalyzerAgent

agent = LeaseAnalyzerAgent(llm_service=groq_service)
analysis = await agent.analyze(contract_text)

print(analysis['entities'])
print(analysis['risks'])
```

## Performance Targets

- **Analysis Time**: < 10s por contrato
- **Accuracy**: > 90%
- **Risk Detection**: 85%+ precision

## Related Skills

- 🔗 [Document Parsing](../document-parsing/SKILL.md)
- 🔗 [Requirements Extraction](../requirements-extraction/SKILL.md)

---

**Status**: 🟡 In Development  
**Last Updated**: 2026-04-07
