---
name: "Lease Analysis & Contract Parsing"
version: 1.0
domain: "legal-analysis"
difficulty: "high"
applies_to: ["python"]
tags: ["langgraph", "llm", "contract-analysis"]
---

# Skill: Lease Analysis & Contract Parsing

## 📋 Descripción General

Analizar contratos de arrendamiento y documentos legales para extraer información estructurada (duración, cláusulas, montos, restricciones).

## 🎯 Objetivo

Dado un contrato de arriendo, extraer automáticamente:
- ✅ Partes (arrendador, arrendatario)
- ✅ Duración (fecha inicio/fin)
- ✅ Renta mensual
- ✅ Depósito de garantía
- ✅ Cláusulas importantes
- ✅ Restricciones

## 🏗️ Arquitectura

```
Contract Text
     ↓
[LangGraph Router]
     ├─ Route 1: Entity Extraction
     │   └─ Names, dates, amounts
     │
     ├─ Route 2: Clause Detection
     │   └─ Identify key clauses
     │
     └─ Route 3: Risk Analysis
         └─ Flag potential issues
     ↓
Structured Output (JSON)
```

## 💻 Implementación

### Backend: LangGraph Agent

```python
# backend/app/agents/lease_analyzer_agent/agent.py

from langgraph.graph import StateGraph, State
from typing import TypedDict, Annotated
import operator

class LeaseAnalysisState(TypedDict):
    """State for lease analysis workflow"""
    contract_text: str
    extracted_entities: dict
    identified_clauses: list
    risks: list
    final_report: dict

class LeaseAnalyzerAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        graph = StateGraph(LeaseAnalysisState)
        
        # Add nodes
        graph.add_node("extract_entities", self._extract_entities)
        graph.add_node("identify_clauses", self._identify_clauses)
        graph.add_node("analyze_risks", self._analyze_risks)
        graph.add_node("generate_report", self._generate_report)
        
        # Add edges
        graph.set_entry_point("extract_entities")
        graph.add_edge("extract_entities", "identify_clauses")
        graph.add_edge("identify_clauses", "analyze_risks")
        graph.add_edge("analyze_risks", "generate_report")
        graph.set_finish_point("generate_report")
        
        return graph.compile()
    
    async def _extract_entities(self, state: LeaseAnalysisState) -> LeaseAnalysisState:
        """Step 1: Extract entities (parties, dates, amounts)"""
        prompt = f"""
        Analiza este contrato de arrendamiento y extrae:
        - Nombres de partes (arrendador, arrendatario)
        - Fechas (inicio, fin)
        - Montos (renta, depósito)
        - Ubicación de la propiedad
        
        Contrato:
        {state['contract_text']}
        
        Retorna JSON estructurado.
        """
        
        response = await self.llm.chat(prompt)
        state['extracted_entities'] = self._parse_json_response(response)
        return state
    
    async def _identify_clauses(self, state: LeaseAnalysisState) -> LeaseAnalysisState:
        """Step 2: Identify key clauses"""
        prompt = f"""
        En este contrato, identifica cláusulas importantes:
        - Cláusulas de rescisión
        - Cláusulas de ruptura
        - Restricciones de uso
        - Responsabilidades de mantenimiento
        - Cuotas de servicios
        
        Contrato:
        {state['contract_text']}
        """
        
        response = await self.llm.chat(prompt)
        state['identified_clauses'] = self._parse_list_response(response)
        return state
    
    async def _analyze_risks(self, state: LeaseAnalysisState) -> LeaseAnalysisState:
        """Step 3: Analyze potential risks"""
        prompt = f"""
        Analiza riesgos para el arrendatario en este contrato:
        - Clausulas desfavorables
        - Restricciones excesivas
        - Montos inusuales
        
        Contrato:
        {state['contract_text']}
        
        Retorna lista de riesgos si existen.
        """
        
        response = await self.llm.chat(prompt)
        state['risks'] = self._parse_list_response(response)
        return state
    
    async def _generate_report(self, state: LeaseAnalysisState) -> LeaseAnalysisState:
        """Step 4: Generate final report"""
        state['final_report'] = {
            'entities': state['extracted_entities'],
            'clauses': state['identified_clauses'],
            'risks': state['risks'],
            'summary': f"Contrato entre {state['extracted_entities'].get('landlord')} "
                      f"y {state['extracted_entities'].get('tenant')} "
                      f"por ${state['extracted_entities'].get('rent')}/mes"
        }
        return state
    
    async def analyze(self, contract_text: str) -> dict:
        """Execute analysis workflow"""
        initial_state = LeaseAnalysisState(
            contract_text=contract_text,
            extracted_entities={},
            identified_clauses=[],
            risks=[],
            final_report={}
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state['final_report']


# backend/app/application/usecases/analyze_lease.py

class AnalyzeLeaseUseCase(UseCase):
    def __init__(self, lease_agent: LeaseAnalyzerAgent, doc_repo: DocumentRepository):
        self.lease_agent = lease_agent
        self.doc_repo = doc_repo
    
    async def execute(self, document_id: str) -> dict:
        """Analyze lease document"""
        # 1. Load document
        doc = await self.doc_repo.find_by_id(document_id)
        
        # 2. Get document text
        # (from vector store or re-parse from SeaweedFS)
        contract_text = await self._get_document_text(doc)
        
        # 3. Analyze with agent
        analysis = await self.lease_agent.analyze(contract_text)
        
        # 4. Store analysis in metadata
        doc.metadata['analysis'] = analysis
        await self.doc_repo.update(doc)
        
        return analysis


# backend/app/routes/analysis.py

@router.post("/api/v1/documents/{doc_id}/analyze-lease")
async def analyze_lease(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    usecase: AnalyzeLeaseUseCase = Depends()
) -> APIResponse:
    """Analyze lease document"""
    try:
        analysis = await usecase.execute(doc_id)
        return APIResponse.success(data=analysis)
    except Exception as e:
        return APIResponse.error(str(e))
```

### Frontend: Analysis Display

```typescript
// frontend/src/components/LeaseAnalysis/AnalysisViewer.tsx

import React, { useState, useEffect } from 'react';
import * as api from '../../services/api';

export const AnalysisViewer: React.FC<{ documentId: string }> = ({ documentId }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true);
      try {
        const response = await api.analyzeLeaseDocument(documentId);
        setAnalysis(response.data);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalysis();
  }, [documentId]);
  
  if (loading) return <div>Analizando contrato...</div>;
  if (!analysis) return <div>Sin análisis disponible</div>;
  
  return (
    <div className="analysis-container">
      <section className="entities">
        <h3>Información Básica</h3>
        <p><strong>Arrendador:</strong> {analysis.entities.landlord}</p>
        <p><strong>Arrendatario:</strong> {analysis.entities.tenant}</p>
        <p><strong>Renta:</strong> ${analysis.entities.rent}/mes</p>
        <p><strong>Duración:</strong> {analysis.entities.start_date} → {analysis.entities.end_date}</p>
      </section>
      
      <section className="clauses">
        <h3>Cláusulas Identificadas</h3>
        <ul>
          {analysis.clauses.map((clause, idx) => (
            <li key={idx}>{clause}</li>
          ))}
        </ul>
      </section>
      
      {analysis.risks.length > 0 && (
        <section className="risks" style={{ backgroundColor: '#fff3cd' }}>
          <h3>⚠️ Riesgos Identificados</h3>
          <ul>
            {analysis.risks.map((risk, idx) => (
              <li key={idx}>{risk}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
};
```

## 🧠 LangGraph Workflow

```python
# Workflow visualization
graph = StateGraph(LeaseAnalysisState)
#
#  extract_entities
#       ↓
#  identify_clauses
#       ↓
#  analyze_risks
#       ↓
#  generate_report (FINISH)
```

## 📋 Output Schema

```json
{
  "entities": {
    "landlord": "Juan García",
    "tenant": "María López",
    "rent": 1500,
    "deposit": 3000,
    "property_address": "Calle Principal 123",
    "start_date": "2026-01-01",
    "end_date": "2027-12-31"
  },
  "clauses": [
    "Cláusula de rescisión: 30 días previo",
    "Responsabilidad de mantenimiento: arrendatario",
    "Prohibición de subarriendo"
  ],
  "risks": [
    "Depósito de garantía sin intereses",
    "Cláusula de aumento de renta anual sin límite"
  ],
  "summary": "Contrato entre Juan García y María López..."
}
```

## 🎯 Best Practices

1. **Prompt Engineering**: Refinar prompts para máxima precisión
2. **Validation**: Validar que extracciones tengan sentido
3. **Checkpointing**: Usar checkPoints en LangGraph para debugging
4. **Streaming**: Usar `stream()` para feedback en tiempo real
5. **Caching**: Cache de análisis de contratos similares

## 🧪 Testing

```python
# backend/tests/agents/test_lease_analyzer.py

@pytest.mark.asyncio
async def test_lease_analysis_extracts_parties():
    contract = """
    Arrendador: Juan García
    Arrendatario: María López
    Renta: $1500/mes
    """
    
    agent = LeaseAnalyzerAgent(mock_llm)
    result = await agent.analyze(contract)
    
    assert result['entities']['landlord'] == 'Juan García'
    assert result['entities']['tenant'] == 'María López'
```

## 📚 Referencias

- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Pydantic for structured output](https://docs.pydantic.dev/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

**Version**: 1.0  
**Updated**: 2026-04-07  
**Status**: ✅ Ready for Implementation
