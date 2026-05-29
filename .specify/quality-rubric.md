---
rubric_version: "1.0"
updated: "2026-05-29"
applies_to: "spec.md readiness for /speckit-plan"
---

# Spec Quality Rubric — readiness para `/speckit-plan`

Una spec está "plan-ready" cuando supera los 8 criterios siguientes. Cada criterio recibe ✅ / ⚠️ / ❌ según las reglas de pass/risk/fail. El verdict global se calcula así:

- ✅ **READY** — los 8 criterios en verde.
- ⚠️ **READY-WITH-RISKS** — todos en verde salvo ≤2 en ámbar; ningún rojo.
- ❌ **NOT-READY** — al menos 1 rojo, o ≥3 ámbar.

`/speckit-ready` evalúa la spec activa contra estos criterios y produce `readiness-report.md`. Es **advisory** — no bloquea `/speckit-plan`, pero su recomendación se ignora bajo riesgo de un plan de baja calidad.

---

## C1-problem-scope — Problem & scope boundaries

**Qué evalúa**: el problema, el usuario afectado y el scope (in/out) están explícitos.

**Pass (✅)**:
- Hay frase clara del problema (no solo "the system" / "we want to add").
- Hay sección o lista "Out of scope" con ≥1 entry explícita.
- El usuario tipo está identificado por rol concreto (no genérico "user").

**Risk (⚠️)**: problema claro y usuario identificado, pero "Out of scope" ausente o vacío.

**Fail (❌)**: no hay statement de problema, **o** el usuario no está identificado por rol.

**Remediación**:
- Si falta problema o usuario → `/speckit-discover`.
- Si solo falta out-of-scope → `/speckit-clarify`.

---

## C2-testable-ac — User stories con AC testables

**Qué evalúa**: cada User Story tiene Acceptance Criteria observables y medibles, no aspiracionales.

**Pass (✅)**:
- ≥1 US redactada.
- 100% de las US tienen AC en formato Given/When/Then **o** checklist comprobable.
- Ningún AC contiene verbos vagos sin objeto concreto: "manage", "handle", "support", "process".

**Risk (⚠️)**: AC presentes en todas las US pero ≥1 AC contiene un verbo vago.

**Fail (❌)**: alguna US sin AC, **o** todos los AC son vagos.

**Remediación**: `/speckit-clarify` con foco explícito en concretar los AC señalados.

---

## C3-domain-model — Domain model esbozado

**Qué evalúa**: las entidades principales y sus relaciones se mencionan, aunque sea informal.

**Pass (✅)**:
- ≥1 entidad nombrada con sus atributos clave.
- Relaciones entre entidades clave declaradas (1:N, N:M, ownership).

**Risk (⚠️)**: entidades nombradas pero sin relaciones entre ellas.

**Fail (❌)**: ninguna entidad mencionada explícitamente.

**Remediación**: `/speckit-clarify` o edición manual de la spec añadiendo sección "Entities".

---

## C4-cross-service — Cross-service touchpoints

**Qué evalúa**: si la feature toca >1 servicio del polyrepo, los eventos AMQP y contratos están listados.

**Pass (✅)**:
- Single-service: explícitamente declarado en la spec ("This feature is scoped to `<service>`").
- Multi-service: lista de servicios afectados + eventos AMQP previstos (con routing key pattern `<service>.v1.<entity>.<event>`) + contratos a publicar/consumir.

**Risk (⚠️)**: servicios listados, eventos mencionados, pero falta el routing key concreto o el contrato.

**Fail (❌)**: la spec menciona ≥2 servicios pero no lista eventos AMQP ni contratos de integración.

**Remediación**: `/speckit-challenge functional` — el `business-logic-reviewer` detecta este gap explícitamente.

---

## C5-nfrs — NFRs explícitos

**Qué evalúa**: los constraints no-funcionales relevantes están declarados.

**Pass (✅)**: hay sección NFR (o equivalente) que cubre, en función del scope de la feature:
- Auth scope (¿quién puede invocar? roles, scopes JWT).
- Performance (latencia esperada, throughput previsto si aplica).
- Retención / privacidad (¿hay datos personales? ¿GDPR? ¿tiempo de retención?).
- Disponibilidad (¿síncrono crítico? ¿degrada bien si AMQP no está disponible?).

**Risk (⚠️)**: NFRs parciales — falta ≥1 dimensión claramente relevante para la feature.

**Fail (❌)**: no hay NFRs declarados **y** la feature toca auth o datos personales.

**Remediación**: `/speckit-clarify` o `/speckit-challenge functional`.

---

## C6-open-questions — Open questions resueltas o diferidas

**Qué evalúa**: las QUESTION-PO (u otras Open Questions) no resueltas están explícitamente diferidas con justificación, no abiertas en silencio.

**Pass (✅)**:
- 0 Open Questions en estado abierto sin asignar, **o**
- Las abiertas tienen marca explícita de "Deferred to <fase / sprint / iteration>" con motivo escrito.

**Risk (⚠️)**: Open Questions abiertas sin marca de diferimiento explícita (pero no marcadas como bloqueantes).

**Fail (❌)**: ≥1 Open Question abierta marcada como bloqueante o etiquetada con criticidad alta.

**Remediación**:
- `/speckit-atlassian-sync-push` para escalar al PO si hace falta input externo.
- Resolver inline y registrar en `decisions.md` si la decisión es interna.

---

## C7-success-metrics — Métricas de éxito

**Qué evalúa**: hay forma observable de saber si la feature funciona en producción.

**Pass (✅)**: ≥1 métrica concreta y medible: KPI de negocio (conversión, retención), métrica técnica (latencia p95, error rate), o evento de adopción (% usuarios que usan X).

**Risk (⚠️)**: hay menciones de éxito pero no medibles ("better UX", "more efficient").

**Fail (❌)**: ninguna métrica de éxito mencionada.

**Remediación**:
- `/speckit-discover` si la spec entró desde idea cruda sin objetivo claro.
- `/speckit-clarify` si el objetivo está claro pero falta concretar la métrica.

---

## C8-edge-cases — Edge cases catalogados

**Qué evalúa**: la spec lista los caminos no-felices que el plan debe cubrir.

**Pass (✅)**: ≥3 edge cases concretos cubriendo al menos: errores de validación, concurrencia, estados límite (vacío, máximo), permisos denegados.

**Risk (⚠️)**: 1-2 edge cases listados.

**Fail (❌)**: 0 edge cases listados.

**Remediación**: `/speckit-challenge functional` — el `business-logic-reviewer` cubre edge cases como bucket explícito.

---

## Cálculo del verdict

Pseudocódigo:

```
reds   = count(criteria where status == ❌)
ambers = count(criteria where status == ⚠️)

if reds > 0:           verdict = NOT-READY
elif ambers >= 3:      verdict = NOT-READY
elif ambers >= 1:      verdict = READY-WITH-RISKS
else:                  verdict = READY
```

## Formato esperado del reporte

`/speckit-ready` debe producir `specs/<feature>/readiness-report.md` con esta estructura:

1. Header (verdict, fecha, versión de rubric).
2. Tabla resumen con los 8 criterios.
3. Findings: una entrada por cada criterio en ⚠️ o ❌, con evidencia (cita o pointer) y remediación.
4. Action plan: comandos a ejecutar en orden de prioridad para alcanzar READY.

Ver `commands/speckit.ready.md` para el template exacto.
