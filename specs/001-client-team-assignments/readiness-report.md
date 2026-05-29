# Readiness Report — 001-client-team-assignments

**Verdict**: ❌ NOT-READY
**Generated**: 2026-05-28T23:20:48Z
**Rubric version**: 1.0
**Spec evaluated**: spec.md (last modified 2026-05-28T20:11:09+0200)

## Summary

| ID                  | Criterion                          | Status |
|---------------------|------------------------------------|--------|
| C1-problem-scope    | Problem & scope boundaries         | ✅ |
| C2-testable-ac      | User stories con AC testables      | ✅ |
| C3-domain-model     | Domain model esbozado              | ✅ |
| C4-cross-service    | Cross-service touchpoints          | ⚠️ |
| C5-nfrs             | NFRs explícitos                    | ⚠️ |
| C6-open-questions   | Open questions resueltas/diferidas | ❌ |
| C7-success-metrics  | Métricas de éxito                  | ✅ |
| C8-edge-cases       | Edge cases catalogados             | ✅ |

**Totals**: 5 ✅ · 2 ⚠️ · 1 ❌

## Findings

### ⚠️ C4-cross-service — Cross-service touchpoints

**Evidence**: Servicios cross-service detectados en spec.md: `pd-service-azuread-adapter` (L333, contexto B1/B2), `pd-service-data-factory` (L370, B3 y B10), `pc-app-portalcliente-web` (L444, B8). FR-014 declara la integración AMQP: *"sincronizar los datos de asignación (empleado, rol, porcentaje, período) con la Plataforma del Dato publicando un evento en el bus de mensajería interno (RabbitMQ, exchange `internal`)"* (spec.md:L217-220). Sin embargo, **no se especifica el routing key concreto** siguiendo el patrón `<service>.v1.<entity>.<event>` exigido por la convención del polyrepo. Tampoco hay sección que liste los contratos del evento (qué campos publica, qué consume `pd-service-data-factory`).

**Remediation**: Edición manual de spec.md (o `/speckit-clarify` con foco explícito). `/speckit-challenge functional` ya se ejecutó (challenge-report.md presente) y surfaceó B1/B2/B3/B8/B10 pero esos hallazgos quedaron como Open Questions y no se promovieron a un contrato AMQP explícito en FR-014.

---

### ⚠️ C5-nfrs — NFRs explícitos

**Evidence**: Cubiertos:
- **Auth scope**: FR-004 + permiso `CLIENT_ASSIGNMENT_EDIT` mencionado en US1-AC3 (spec.md:L44-46).
- **Performance**: FR-014 propagación AMQP <5min (L220-221); SC-003 histórico visible <1s (L256-257); SC-001 UX <3min (L250-251).

No cubiertos pese a ser relevantes para el scope:
- **Retención / privacidad**: la feature persiste datos personales de empleados (nombre, rol, período, porcentaje de carga) y trazabilidad histórica indefinida (SC-005: *"sin limitación temporal"*, L260-261). No hay mención de GDPR, anonimización tras baja del empleado, o política de retención del histórico.
- **Disponibilidad**: OQ-004 abre exactamente esta dimensión (qué hacer si Plataforma del Dato no está disponible al guardar) y queda sin resolver. El comportamiento degradado de FR-014 no está definido.

**Remediation**: `/speckit-clarify` — el objetivo está claro y el gap es de concreción puntual sobre dos dimensiones (retención + degradación AMQP).

---

### ❌ C6-open-questions — Open questions resueltas/diferidas

**Evidence**: La sección "Open Questions — Pending PO Decision" contiene **4 preguntas originales + 7 nuevas del challenge funcional**, todas con `_Estado_: pending`. De ellas, dos están **explícitamente etiquetadas como impacto Alto**:
- OQ-001 (baja sin sucesor) — *"Alto — define el comportamiento de US4 en el escenario de baja"* (spec.md:L319).
- OQ-002 (asesor de referencia) — *"Alto — afecta cómo se reparten las tareas automáticas y quién aparece en los informes"* (spec.md:L320).

Adicionalmente, B4 (reasignación tras baja con múltiples sucesores) y B6 (corrección de cierre por error humano) bloquean comportamientos de US4/FR-009. Ninguna pregunta está marcada como "Deferred to <fase>" con motivo escrito; todas están abiertas sin gestión explícita.

Per rubric C6-open-questions Fail: *"≥1 Open Question abierta marcada como bloqueante o etiquetada con criticidad alta"* → cumple los dos triggers.

**Remediation**: `/speckit-atlassian-sync-push` para escalar al PO las preguntas Alto-impacto (OQ-001, OQ-002, B4, B6) o resolver inline y registrar la decisión en `decisions.md`. Las preguntas de menor impacto (B3, B7, B8, B10) pueden marcarse explícitamente como "Deferred to fase X" con justificación.

---

## Action Plan

To reach READY, run in this order:

1. `/speckit-atlassian-sync-push` — escalar al PO las OQ Alto-impacto (OQ-001, OQ-002, B4, B6) **o** resolver inline en `decisions.md` y marcar el resto como diferidas con motivo. Resuelve **C6-open-questions**.
2. `/speckit-clarify` — concretar retención de datos personales del histórico y comportamiento degradado de FR-014 si Plataforma del Dato no está disponible. Resuelve **C5-nfrs**.
3. Edición manual de FR-014 (o `/speckit-clarify` con foco explícito) — añadir routing key concreto `<service>.v1.<entity>.<event>` y lista de campos del evento publicado. Resuelve **C4-cross-service**.
4. `/speckit-ready` — re-evaluar.

## Notes

- **C1-problem-scope juzgado como ✅ con margen**: la spec no tiene una sección "Problem" formal; el problema se infiere del título y del `Input` line (L13). El usuario tipo (responsable, coordinador, asesor, técnico) sí está identificado por rol concreto. El "Out of scope" se materializa en FR-015 (no es sección dedicada pero es explícito y testable). Si el rubric se endurece en el futuro, este criterio podría caer a ⚠️ por falta de sección Problem dedicada.

- **C4-cross-service juzgado como ⚠️ y no ❌**: la integración AMQP está declarada con exchange concreto (`internal`), por lo que no cae en el supuesto "menciona ≥2 servicios pero no lista eventos AMQP ni contratos". Cae en el supuesto de risk: "eventos mencionados pero sin routing key concreta".

- **C5-nfrs — retención**: la feature persiste el histórico inmutable de períodos de asignación de empleados sin política de retención. Esto es típicamente un punto de fricción con compliance. Si el equipo legal del proyecto ya tiene una política transversal aplicable a histórico de empleados, basta con referenciarla en NFRs y el criterio sube a ✅. Validar con el humano.

- **El `challenge-report.md` ya existente (2026-05-28) cubrió bien C8-edge-cases y parte de C4-cross-service**, pero los hallazgos B1-B10 quedaron como Open Questions sin promoverse a FRs o NFRs. Es decir, ejecutar `/speckit-challenge functional` otra vez no añadiría valor — los gaps están identificados, falta resolverlos.
