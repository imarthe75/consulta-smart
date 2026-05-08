import re
from typing import Dict, List, Optional, Any

class HeuristicsEngine:
    """
    Motor de Heurísticas para ConsultaRPP.
    Optimiza la detección de jurisdicción y previene alucinaciones mediante validación de grounding.
    """
    
    def __init__(self):
        self.jurisdictions = {
            "puebla": ["puebla", "ircep", "cholula", "tehuacan", "atlixco"],
            "quintana-roo": ["quintana roo", "qroo", "cancun", "playa del carmen", "tulum", "chetumal", "cozumel", "isla mujeres"]
        }
        
        self.critical_keywords = {
            "fre": ["fre", "folio real electrónico", "folio real electronico", "nomenclatura"],
            "qr": ["qr", "código qr", "codigo qr", "boleta"],
            "costos": ["costo", "precio", "arancel", "derecho", "pago", "linea de captura", "cuanto cuesta"],
            "copias": ["copia", "certificada", "hoja", "pagina", "acto especifico"]
        }

    def detect_jurisdiction(self, query: str) -> Optional[str]:
        """Detecta si la consulta es específica de una jurisdicción."""
        query_lower = query.lower()
        for jurisdiction, keywords in self.jurisdictions.items():
            if any(k in query_lower for k in keywords):
                return jurisdiction
        return None

    def extract_critical_entities(self, query: str) -> List[str]:
        """Extrae entidades críticas para mejorar el boosting de RAG."""
        query_lower = query.lower()
        found = []
        for entity, keywords in self.critical_keywords.items():
            if any(k in query_lower for k in keywords):
                found.append(entity)
        return found

    def apply_search_logic(self, query: str) -> Dict[str, Any]:
        """Retorna parámetros optimizados para la búsqueda RAG."""
        jurisdiction = self.detect_jurisdiction(query)
        entities = self.extract_critical_entities(query)
        
        filters = {}
        if jurisdiction:
            filters["category"] = jurisdiction # Asumiendo que la categoría en DB mapea al estado
            
        return {
            "jurisdiction": jurisdiction,
            "entities": entities,
            "filters": filters
        }

    def is_answer_grounded(self, answer: str, context: str) -> bool:
        """
        Verificación heurística de grounding. 
        Detecta patrones comunes de alucinación que contradicen el contexto.
        """
        # Heurística: Si la respuesta menciona "páginas" o "cobro por hoja" 
        # y el contexto tiene la regla estricta de "acto completo", invalidar.
        if "página" in answer.lower() or "hoja" in answer.lower():
            if "regla estricta" in context.lower() or "acto íntegro" in context.lower():
                return False
                
        # Heurística: Si se mencionan costos específicos no presentes en el contexto.
        # (Esto es más complejo, se delega al LLM verifier en el blindaje de segundo nivel).
        
        return True

heuristics = HeuristicsEngine()
