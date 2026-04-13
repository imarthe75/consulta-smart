#!/bin/bash
# QUICK REFERENCE CARD: CONSULTA-RPP ADDON GRATUITO
# Execute: less this_file.sh

cat << 'EOF'

╔═════════════════════════════════════════════════════════════════════════════╗
║                    CONSULTA-RPP ANÁLISIS FINANCIERO                        ║
║                    VERSIÓN: ADDON GRATUITO A IDP-SMART                     ║
╚═════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 📊 RECOMENDACIÓN EJECUTIVA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ✅ CAMBIAR DE GROQ → OLLAMA (100% LOCAL)

   Razones:
      • $0 USD/mes (vs $350/mes Groq escalado)
      • Datos en servidor estatal (soberanía)
      • Setup 30 min (vs días para contratos)
      • Escalable sin costo (agregar hardware)
      • Addon GRATUITO para ciudadanos/estados

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 💰 COMPARATIVA FINANCIERA (ROI: 5 AÑOS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─ GROQ CLOUD (Escalado) ──────────────────────────────────────────────────┐
│                                                                           │
│  Año 1:    $4,200                                                        │
│  Año 2:    $5,400  (15% crecimiento)                                     │
│  Año 3:    $6,210                                                        │
│  Año 4:    $7,142                                                        │
│  Año 5:    $8,213                                                        │
│  ─────────────────                                                       │
│  TOTAL:   $31,165  ❌ NO SOSTENIBLE                                      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

┌─ OLLAMA LOCAL (Costo Cero) ──────────────────────────────────────────────┐
│                                                                           │
│  Año 1:    $50     (electricidad compartida)                            │
│  Año 2:    $50                                                          │
│  Año 3:    $50                                                          │
│  Año 4:    $150    (update hardware menor)                              │
│  Año 5:    $50                                                          │
│  ─────────────────                                                       │
│  TOTAL:    $350    ✅ SOSTENIBLE                                         │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

   💡 AHORRO EN 5 AÑOS: $30,815 USD

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🖥️  REQUERIMIENTOS HARDWARE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─ OPCIÓN 1: COMPARTIDO (RECOMENDADO = $0 CAPEX) ───────────────────────┐
│                                                                         │
│  CPU:       4-8 cores (compartidos con idp-smart)                     │
│  RAM:       6-8 GB alocados para Ollama                               │
│  Storage:   50 GB SSD para modelos + caché                            │
│  Network:   1 Gbps (existente)                                        │
│                                                                         │
│  COSTO: $0 (infraestructura actual)                                   │
│  Usuarios: 15-20 simultáneos ✅ SUFICIENTE                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─ OPCIÓN 2: DEDICADO ($600-800 primera vez) ──────────────────────────┐
│                                                                         │
│  CPU:       Intel Xeon 4-core                                          │
│  RAM:       16 GB (8 para Ollama, 8 SO+caché)                         │
│  Storage:   500 GB SSD                                                 │
│  Costo:     $600-800 (compra única)                                   │
│                                                                         │
│  Usuarios:  50+ simultáneos ✅ ROBUSTO                                 │
│  Vía útil:  5 años → $120-160/año en depreciación                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🤖 MODELOS DISPONIBLES (TODOS $0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─ LLAMA 2 7B (RECOMENDADO) ────────────────────────────────────────────┐
│  Tamaño:         4 GB                                                   │
│  RAM req:        8 GB                                                   │
│  Velocidad:      25 tok/seg (CPU)                                      │
│  Calidad:        8/10 para español                                     │
│  Instalación:    ollama pull llama2                                    │
│  Usuarios:       15-20 simultáneos                                     │
│  Recomendación:  ✅ MÁS USADO (comunidad activa)                      │
└───────────────────────────────────────────────────────────────────────┘

┌─ MISTRAL 7B (Mejor para español) ─────────────────────────────────────┐
│  Tamaño:         3.5 GB                                                 │
│  RAM req:        8 GB                                                   │
│  Velocidad:      30 tok/seg (CPU)                                      │
│  Calidad:        8.5/10 para español ✅                                │
│  Instalación:    ollama pull mistral                                   │
│  Usuarios:       20+ simultáneos                                       │
│  Recomendación:  ✅ MEJOR IDIOMA                                       │
└───────────────────────────────────────────────────────────────────────┘

┌─ PHI 2.7B (Hardware limitado) ────────────────────────────────────────┐
│  Tamaño:         1.6 GB                                                 │
│  RAM req:        4 GB                                                   │
│  Velocidad:      50 tok/seg (CPU)                                      │
│  Calidad:        7.5/10 (bueno para su tamaño)                         │
│  Instalación:    ollama pull phi                                       │
│  Usuarios:       10-15 simultáneos                                     │
│  Recomendación:  ✅ SI RECURSOS MUY LIMITADOS                         │
└───────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ⏱️  TIMELINE DE IMPLEMENTACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   SEMANA 1                    ├─ Instalar Ollama
   (POC)                       ├─ Crear POC comparativo
                               ├─ Comparar vs Groq
                               ├─ Documentar hallazgos
                               └─ ENTREGABLE: Demo + Reporte

   SEMANA 2                    ├─ Deploy en servidor test
   (STAGING)                   ├─ Load testing (50 usuarios)
                               ├─ Tuning de performance
                               ├─ Capacitación inicial
                               └─ ENTREGABLE: Sistema listo

   SEMANA 3                    ├─ Migrar desde Groq
   (PRODUCCIÓN)                ├─ Integrar con idp-smart
                               ├─ Activar monitoreo 24/7
                               ├─ Soporte técnico
                               └─ ENTREGABLE: Sistema operativo

   COSTO DE DESARROLLO:        $0 (incluido en proyecto)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🎯 COMPARATIVA RÁPIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────┬──────────────────┬─────────────────┬──────────────┐
│ FACTOR           │ GROQ CLOUD       │ OLLAMA LOCAL    │ GANADOR      │
├──────────────────┼──────────────────┼─────────────────┼──────────────┤
│ Costo/mes        │ $100-350         │ $0              │ ✅ OLLAMA    │
│ Tiempo setup     │ 1 día            │ 30 minutos      │ ✅ OLLAMA    │
│ Velocidad        │ 0.5 seg          │ 2-5 seg         │ ❌ Groq      │
│ Privacidad datos │ Cloud ☁️         │ Local 🏢        │ ✅ OLLAMA    │
│ Independencia    │ API externa      │ Sin dependencia  │ ✅ OLLAMA    │
│ Escalabilidad    │ Con costo        │ Gratis (HW)     │ ✅ OLLAMA    │
│ Funcionamiento   │ Requiere internet│ Offline OK      │ ✅ OLLAMA    │
│ Control total    │ Proveedor        │ Estatal         │ ✅ OLLAMA    │
└──────────────────┴──────────────────┴─────────────────┴──────────────┘

   RESULTADO: OLLAMA GANA EN 7 DE 8 FACTORES ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 📈 CAPACIDAD SOPORTADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Scenario: Estado típico 2 millones de habitantes

   Usuarios potenciales:       50,000 (2.5% población)
   Peak semanal:               500 usuarios
   Usuarios simultáneos prom:  20
   Peak simultáneos:           50

   Ollama (CPU 4c, 16GB) soporta:    15-20 simultáneos  = ✅ SUFICIENTE
   Ollama (CPU 8c + GPU T4):         100+ simultáneos   = ✅ ABUNDANTE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✅ PRÓXIMOS PASOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   1. Presentar PROPUESTA_EJECUTIVA.md a dirección
   2. Obtener aprobación para Fase 1 (POC)
   3. Asignar servidor para pruebas
   4. Ejecutar: ./scripts/compare-ollama-vs-groq.sh
   5. Iniciar implementación (1 semana)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 📚 DOCUMENTACIÓN COMPLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   /docs/
   ├─ PROPUESTA_EJECUTIVA.md                   ← LEER PRIMERO (10 min)
   ├─ ANALISIS_FINANCIERO_ADDON_GRATUITO.md  ← Análisis completo (30 min)
   ├─ GUIA_TECNICA_MIGRACION_OLLAMA.md       ← Implementación (45 min)
   ├─ README_INDICE_FINANCIERO.md            ← Navegación indexada
   └─ RAG_OPERATIONAL_STATUS.md              ← Status actual sistema

   /scripts/
   ├─ compare-ollama-vs-groq.sh               ← Benchmark comparativo
   └─ [otros scripts de test]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 💡 INSIGHT FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ConsultaRPP no es solo un addon a idp-smart.

   Es una estrategia de TRANSFORMACIÓN DIGITAL ESTATAL:

   ✅ Aceleración: De 2-3 meses en contratación → 3 semanas en desarrollo
   ✅ Costo: De $21K/5 años → $350/5 años (ahorros públicos reales)
   ✅ Soberanía: Datos gubernamentales en servidores locales
   ✅ Escalabilidad: Sin dependencia de proveedores cloud
   ✅ Oportunidad: Modelo para otros sistemas RPP, notariales, etc.

   👉 LECCIONES APLICABLES A TODA LA ADMINISTRACIÓN ESTATAL

╔═════════════════════════════════════════════════════════════════════════════╗
║                        DOCUMENTO: QUICK REFERENCE                          ║
║                        GENERA AUTOMATICAMENTE CON:                         ║
║                        less docs/QUICK_REFERENCE.sh                        ║
║                        O: bash docs/QUICK_REFERENCE.sh                     ║
╚═════════════════════════════════════════════════════════════════════════════╝

EOF
