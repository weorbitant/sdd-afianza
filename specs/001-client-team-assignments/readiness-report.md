# Readiness Report — 001-client-team-assignments

**Verdict**: ❌ NOT-READY
**Generated**: 2026-06-01T06:35:33Z
**Rubric version**: 1.0
**Spec evaluated**: spec.md (last modified 2026-05-29T15:32:45+0200)

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

**Evidence**: Servicios cross-service detectados: `pd-service-azuread-adapter` (L335, B1/B2), `pd-service-data-factory` (L372, B3/B10), `pc-app-portalcliente-web` (L446, B8). FR-014 declara la integración AMQP: *"publicando un evento en el bus de mensajería interno (RabbitMQ, exchange `internal`) **únicamente cuando el equipo esté en estado `active`**"* (spec.md:L218-225). Esta ronda de clarify ha **enriquecido la semántica** (eventos condicionados a `active`, transiciones explícitas) pero sigue sin nombrar el routing key concreto (`<service>.v1.<entity>.<event>`) ni listar el payload de los eventos.

**Remediation**: Edición manual de FR-014 (o `/speckit-clarify` con foco explícito). Alternativa razonable: diferir a `/speckit-plan` y registrarlo en `contracts/` — el routing key es habitualmente un detalle de planning más que de spec. Si decides diferirlo, marca C4 como "Deferred to planning" en una nota de la spec para que el rubric lo reconozca.

---

### ⚠️ C5-nfrs — NFRs explícitos

**Evidence**: Cubiertos:
- **Auth scope**: FR-004 + `CLIENT_ASSIGNMENT_EDIT` (spec.md:L44-46).
- **Performance**: FR-014 propagación AMQP <5min (L223-225); SC-003 histórico visible <1s (L258); SC-001 UX <3min (L252).

Sin cubrir pese a ser relevantes:
- **Retención / privacidad**: la spec persiste histórico inmutable de períodos de asignación de empleados sin política de retención. SC-005 dice *"sin limitación temporal"* (L262) — bandera roja GDPR sin mención explícita.
- **Disponibilidad / degradación AMQP**: OQ-004 (informes no disponibles al guardar) sigue abierta. El nuevo FR-014 condicionado a `active` no resuelve qué hacer si RabbitMQ está caído al transicionar a `active` — ¿se persiste sin publicar y se reintenta? ¿se bloquea la transición?

**Remediation**: `/speckit-clarify` con foco en estas dos dimensiones. Son 2 preguntas concretas; el siguiente clarify probablemente las cubre.

---

### ❌ C6-open-questions — Open questions resueltas/diferidas

**Evidence**: Mejora sustancial respecto a la ronda anterior — de **4 Alto-impacto** pasamos a **1 Alto + 1 parcial**:

**Cerradas en esta sesión**:
- ✅ **OQ-002** (asesor de referencia) → resuelta via Clarifications 2026-05-29 (asesor principal `isPrimary`).
- ✅ **B6** (corrección de cierre por error) → resuelta via doble confirmación en cierre.

**Siguen abiertas con criticidad alta**:
- ❌ **OQ-001** (baja de asesor sin sucesor) — *"Alto — define el comportamiento de US4 en el escenario de baja"* (spec.md:L321). **Bloqueante**.
- 🟡 **B4** (reasignación con múltiples sucesores) — parcialmente resuelta porque ahora el asesor principal hereda por defecto; queda definir qué pasa con tareas que NO estaban asignadas al principal. _Estado_ todavía `pending` en spec.md:L398.

Otras pending de impacto medio/bajo (B1, B2, B3, B7, B8, B10) siguen abiertas pero diferibles.

Per rubric C6-open-questions Fail: *"≥1 Open Question abierta marcada como bloqueante o etiquetada con criticidad alta"* → OQ-001 cumple el trigger.

**Remediation**: `/speckit-atlassian-sync-push` para escalar OQ-001 + B4 al PO (Paula). La épica DEVPT-518 ya está en estado "Blocked" desde el 26/5 esperando estas respuestas — el siguiente push las añadirá como comentarios individuales.

---

## Action Plan

To reach READY, run in this order:

1. `/speckit-atlassian-sync-push` — escalar OQ-001 + B4 al PO **o** resolver inline en `decisions.md` si tienes criterio. Marcar el resto de pending de impacto bajo (B1/B2/B3/B7/B8/B10) como "Deferred to phase 2" con motivo. Resuelve **C6-open-questions**.
2. `/speckit-clarify` — concretar (a) política de retención del histórico de empleados y (b) comportamiento degradado de FR-014 si RabbitMQ no está disponible al transicionar a `active`. Resuelve **C5-nfrs**.
3. Decidir si C4 (routing key concreto) se resuelve en spec o se difiere a `/speckit-plan`. Si se difiere, añadir nota explícita en FR-014 ("routing key concreto se define en plan.md") — el rubric debería reconocerlo. Si se resuelve, edición manual de FR-014 añadiendo `pgi-api.v1.team.activated` / `pgi-api.v1.team.closed` y campos del payload.
4. `/speckit-ready` — re-evaluar.

## Notes

- **Progreso real desde el último report (2026-05-28)**: de 11 Open Questions pendientes (4 Alto) bajamos a 8 (1 Alto + 1 parcial). 6 decisiones de diseño se han integrado como Clarifications + FRs reescritas (FR-003 estado calculado, FR-005 multi-equipo, FR-009 UX cierre, FR-014 condicionado a `active`, FR-012 mes-only, Key Entities `isPrimary`).
- **C4 podría justificadamente marcarse ⚠️→✅ con una nota** del estilo *"el routing key concreto se define durante `/speckit-plan` en `contracts/team-events.md`"*. Es una decisión de proyecto sobre dónde vive cada artefacto. Lo dejo en ⚠️ por estricta aplicación del rubric, pero si esa nota se añade a FR-014 el criterio sube a ✅ en la siguiente ronda.
- **C5 retención de datos personales** es la dimensión más cara políticamente — si hay política transversal de compliance ya aprobada en la organización, basta con referenciarla en NFRs. Si no, requiere decisión de legal.
- **OQ-001** está marcada explícitamente como bloqueante y lleva 6 días esperando en DEVPT-518. La épica de Jira está en estado "Blocked". El siguiente paso natural es un ping a Paula sobre las 2 preguntas que ya tiene + escalar las nuevas que han surgido.
- **ADR-0007** (draft+commit) está marcada como "requires revisitation" en Clarifications 2026-05-29 — no es un finding del rubric pero el equipo debe procesarla con `/speckit-decisions-extract` antes de planificar.
