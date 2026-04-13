---
name: "Requirements Extraction & Cost Calculator"
version: 1.0
domain: "property-services"
difficulty: "medium"
applies_to: ["python"]
tags: ["extraction", "classification", "llm"]
---

# Skill: Requirements Extraction & Cost Calculator

## 📋 Descripción General

Extraer automáticamente requisitos y costos de trámites del Registro Público de la Propiedad a partir de documentos.

## 🎯 Objetivo

Para cada trámite (inscripción, transferencia, etc):
- ✅ Listar requisitos (documentos necesarios)
- ✅ Calcular costos totales
- ✅ Estimar tiempo de trámite
- ✅ Identificar documentos obligatorios vs. opcionales

## 🏗️ Arquitectura

```
Documento de Trámite
        ↓
[LLM Analysis]
├─ Tipo de trámite
├─ Requisitos
├─ Costos
└─ Timeline
        ↓
Structured Data
        ↓
Almacenamiento para búsqueda
```

## 💻 Implementación

### Backend: Requirements Service

```python
# backend/app/schemas/requirement.py

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class DocumentType(str, Enum):
    OBLIGATORIO = "obligatorio"
    CONDICIONAL = "condicional"
    OPCIONAL = "opcional"


class Requirement(BaseModel):
    """Requisito para un trámite"""
    name: str
    description: Optional[str] = None
    type: DocumentType = DocumentType.OBLIGATORIO
    documentation: List[str] = []  # e.g., ["cédula", "pasaporte"]
    can_be_substituted: bool = False
    alternatives: List[str] = []


class Cost(BaseModel):
    """Costo asociado a un trámite"""
    description: str
    amount: float
    category: str  # "aranceles", "extras", "seguros", etc
    is_variable: bool = False
    notes: Optional[str] = None


class TramiProcessSchema(BaseModel):
    """Esquema de un trámite"""
    name: str
    category: str
    requirements: List[Requirement]
    costs: List[Cost]
    estimated_time_days: int
    steps: List[str]
    can_be_done_online: bool
    notes: Optional[str] = None
    
    def calculate_total_cost(self) -> float:
        """Calcular costo total"""
        return sum(cost.amount for cost in self.costs if not cost.is_variable)


# backend/app/services/requirements_extractor.py

class RequirementsExtractorService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    async def extract_requirements(self, document_text: str) -> TramiProcessSchema:
        """Extract requirements from document using LLM"""
        
        system_prompt = """
        Eres un experto en procedimientos del Registro Público de la Propiedad.
        Analiza documentos legales y extrae información estructurada sobre trámites.
        
        Siempre retorna un JSON válido con esta estructura:
        {
            "name": "Nombre del trámite",
            "category": "inscripcion|transferencia|hipoteca",
            "requirements": [
                {
                    "name": "Documento requerido",
                    "type": "obligatorio|condicional|opcional",
                    "documentation": ["cédula", "pasaporte"],
                    "alternatives": []
                }
            ],
            "costs": [
                {
                    "description": "Arancel de inscripción",
                    "amount": 150000,
                    "category": "aranceles"
                }
            ],
            "estimated_time_days": 10,
            "steps": ["Paso 1", "Paso 2"],
            "can_be_done_online": true
        }
        """
        
        user_prompt = f"""
        Analiza este documento sobre trámites del Registro Público:
        
        {document_text}
        
        Extrae toda la información en JSON.
        """
        
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower temp for structured output
            response_format={"type": "json_object"}
        )
        
        # Parse response as TramiProcessSchema
        data = json.loads(response.content)
        return TramiProcessSchema(**data)


# backend/app/application/usecases/extract_requirements.py

class ExtractRequirementsUseCase(UseCase):
    def __init__(
        self,
        service: RequirementsExtractorService,
        doc_repo: DocumentRepository
    ):
        self.service = service
        self.doc_repo = doc_repo
    
    async def execute(self, document_id: str) -> TramiProcessSchema:
        """Extract requirements from document"""
        # 1. Load document
        doc = await self.doc_repo.find_by_id(document_id)
        
        # 2. Get text content
        text = await self._get_document_text(doc)
        
        # 3. Extract requirements
        schema = await self.service.extract_requirements(text)
        
        # 4. Store schema in document metadata
        doc.metadata['trami_schema'] = schema.dict()
        await self.doc_repo.update(doc)
        
        return schema


# backend/app/routes/requirements.py

@router.get("/api/v1/tramites")
async def list_tramites(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> APIResponse:
    """List all extracted tramites"""
    try:
        # Query documents with trami_schema in metadata
        query = """
        SELECT 
            id, title, 
            metadata->'trami_schema' as schema
        FROM documents 
        WHERE metadata->'trami_schema' IS NOT NULL
        """
        if category:
            query += f" AND metadata->'trami_schema'->>'category' = '{category}'"
        
        results = db.execute(query)
        tramites = [TramiProcessSchema(**row['schema']) for row in results]
        
        return APIResponse.success(data=tramites)
    except Exception as e:
        return APIResponse.error(str(e))


@router.get("/api/v1/tramites/{trami_name}/details")
async def get_trami_details(
    trami_name: str,
    current_user: User = Depends(get_current_user)
) -> APIResponse:
    """Get detailed info for a specific trami"""
    try:
        # Find document with this trami
        doc = await doc_repo.find_by_title(trami_name)
        schema = TramiProcessSchema(**doc.metadata['trami_schema'])
        
        return APIResponse.success(data={
            'name': schema.name,
            'requirements': [r.dict() for r in schema.requirements],
            'costs': [c.dict() for c in schema.costs],
            'total_cost': schema.calculate_total_cost(),
            'estimated_time_days': schema.estimated_time_days,
            'steps': schema.steps,
            'can_be_done_online': schema.can_be_done_online
        })
    except Exception as e:
        return APIResponse.error(str(e))
```

### Frontend: Requirements Display

```typescript
// frontend/src/pages/TramitesPage.tsx

import React, { useState, useEffect } from 'react';
import * as api from '../services/api';

interface Trami {
  name: string;
  category: string;
  requirements: Requirement[];
  costs: Cost[];
  estimated_time_days: number;
}

export const TramitesPage: React.FC = () => {
  const [tramites, setTramites] = useState<Trami[]>([]);
  const [selectedTrami, setSelectedTrami] = useState<Trami | null>(null);
  
  useEffect(() => {
    const fetchTramites = async () => {
      const response = await api.listTramites();
      setTramites(response.data);
    };
    
    fetchTramites();
  }, []);
  
  return (
    <div className="tramites-container">
      <h1>Trámites Disponibles</h1>
      
      <div className="tramites-grid">
        {tramites.map((trami) => (
          <card 
            key={trami.name} 
            onClick={() => setSelectedTrami(trami)}
            className="trami-card"
          >
            <h3>{trami.name}</h3>
            <p className="category">{trami.category}</p>
            <p className="time">
              ⏱️ {trami.estimated_time_days} días aprox.
            </p>
          </card>
        ))}
      </div>
      
      {selectedTrami && (
        <TramiDetails trami={selectedTrami} />
      )}
    </div>
  );
};


const TramiDetails: React.FC<{ trami: Trami }> = ({ trami }) => {
  const totalCost = trami.costs.reduce((sum, c) => sum + c.amount, 0);
  
  return (
    <div className="trami-details">
      <h2>{trami.name}</h2>
      
      <section className="costs">
        <h3>💰 Costos</h3>
        <table>
          <thead>
            <tr>
              <th>Descripción</th>
              <th>Monto</th>
            </tr>
          </thead>
          <tbody>
            {trami.costs.map((cost, idx) => (
              <tr key={idx}>
                <td>{cost.description}</td>
                <td>${cost.amount.toLocaleString()}</td>
              </tr>
            ))}
            <tr className="total">
              <td><strong>Total</strong></td>
              <td><strong>${totalCost.toLocaleString()}</strong></td>
            </tr>
          </tbody>
        </table>
      </section>
      
      <section className="requirements">
        <h3>📋 Requisitos</h3>
        {trami.requirements.map((req, idx) => (
          <div key={idx} className="requirement">
            <span className="badge">{req.type}</span>
            <strong>{req.name}</strong>
            {req.documentation.length > 0 && (
              <p>Documentos aceptados: {req.documentation.join(', ')}</p>
            )}
          </div>
        ))}
      </section>
    </div>
  );
};
```

## 📊 Output Schema

```json
{
  "name": "Inscripción de Propiedad",
  "category": "inscripcion",
  "requirements": [
    {
      "name": "Cédula de identidad",
      "type": "obligatorio",
      "documentation": ["cédula", "pasaporte"],
      "alternatives": []
    },
    {
      "name": "Comprobante de pago",
      "type": "condicional",
      "documentation": ["recibo", "transferencia"],
      "alternatives": ["factura del banco"]
    }
  ],
  "costs": [
    {
      "description": "Arancel de inscripción",
      "amount": 150000,
      "category": "aranceles",
      "is_variable": false
    },
    {
      "description": "Gaveta de escritura",
      "amount": 50000,
      "category": "extras",
      "is_variable": false
    }
  ],
  "estimated_time_days": 10,
  "steps": [
    "Reunir documentos",
    "Pago de aranceles",
    "Presentar solicitud",
    "Revisión de documentos",
    "Inscripción en registro"
  ],
  "can_be_done_online": true
}
```

## 🎯 Best Practices

1. **Validation**: Validar que costos sean monedas válidas
2. **Localization**: Traducir nombres de requisitos según idioma
3. **Updates**: Mantener tramites actualizados periódicamente
4. **Caching**: Cache de tramites porque cambian poco
5. **Fallback**: Si extraction falla, mostrar PDF original

## 🧪 Testing

```python
# backend/tests/services/test_requirements_extractor.py

@pytest.mark.asyncio
async def test_extract_requirements():
    document = """
    Inscripción de Propiedad
    
    Requisitos:
    1. Cédula de identidad (OBLIGATORIO)
    2. Comprobante de pago (OBLIGATORIO)
    3. Plano de la propiedad (CONDICIONAL)
    
    Costos:
    - Arancel: $150.000
    - Gaveta: $50.000
    Total: $200.000
    
    Tiempo estimado: 10 días
    """
    
    service = RequirementsExtractorService(mock_llm)
    schema = await service.extract_requirements(document)
    
    assert schema.name == "Inscripción de Propiedad"
    assert len(schema.requirements) == 3
    assert schema.calculate_total_cost() == 200000
```

---

**Version**: 1.0  
**Updated**: 2026-04-07  
**Status**: ✅ Ready for Implementation
