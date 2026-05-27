---
title: "feat: Importación de declaraciones de Renta desde Excel vía data-migration endpoint"
type: feat
status: active
date: 2026-05-11
origin: docs/brainstorms/2026-05-11-importacion-rentas-requirements.md
---

# feat: Importación de declaraciones de Renta desde Excel vía data-migration endpoint

## Summary

Nuevo endpoint `POST /v1/data-migration/tax-returns` en `pgi-service-pgi-api` que recibe un fichero `.xlsx`, normaliza los datos de cada fila y crea registros `TaxReturn` en la BD. Sigue exactamente el mismo patrón que los imports existentes de clientes y empleados (`DataMigrationController` → `DataMigrationService` → `OperationTaxReturns`). Solo accesible para el equipo técnico mediante permiso `BackofficePermissions.TAX_RETURN_IMPORT`.

---

## PO Feedback Applied (2026-05-11)

Cambios respecto al diseño original (script CLI):

1. **Arquitectura**: No es un script CLI. Debe seguir el patrón de `data-migration` existente (controller → service → operation), igual que clientes y empleados.
2. **Status**: Todos los registros importados con `status = TaxReturnStatus.NEW`. El frontend muestra `NEW` como "Pendiente" — no se añade nuevo valor al enum ni se genera migración.
3. **Importe pendiente**: Si el campo `Importe` contiene texto "pendiente" (u otro no-numérico), `amount = 0` sin warning. Es un caso esperado y válido.
4. **Número de soporte en fechas**: Si un campo de fecha contiene un número de soporte (código no-fecha, ej. `C01160794`), el valor se omite (`null`). La fila SÍ se importa; solo se descarta ese campo de fecha.
5. **Acceso**: Solo equipo técnico. No UI. El trigger es siempre el endpoint REST con autenticación.
6. **FINALIZADA**: Campo ignorado completamente. No afecta el status importado.

---

## Problem Frame

Los asesores mantienen las declaraciones de Renta 2025 en ficheros Excel individuales (~600 filas cada uno). La entidad `TaxReturn` ya existe con todos los campos necesarios pero no hay mecanismo para carga en bloque, haciendo inviable el volcado del histórico sin este endpoint.

---

## Requirements

- R1. El endpoint recibe un fichero `.xlsx` via `multipart/form-data`. Si el fichero falta o no es válido, devuelve 400 antes de tocar la BD.
- R2. La respuesta incluye: `success: boolean`, `errors: string[]` (igual que otros endpoints de data-migration).
- R3. `billingClient` se busca por `Client.nif = Excel.CIF` (trim + uppercase). Si no existe, la fila se omite y el error se acumula en `errors[]`; no se crean clientes.
- R4. `invoiceRecipient` es el mismo `billingClient` salvo que `CIF ≠ DNI1 Declarante`, en cuyo caso se intenta buscar `Client.nif = DNI1 Declarante`; si no existe se usa `billingClient` como fallback.
- R5. `advisor` y `responsible` se buscan por nombre completo (case-insensitive). Si no hay coincidencia exacta, queda nulo con aviso en `errors[]`.
- R6. Idempotencia: fila duplicada si ya existe `TaxReturn` con `declarantNif + fiscalYear`. Se salta sin error.
- R7. `fiscalYear` viene de la columna `Ejercicio`; si está vacía, se extrae del nombre de la hoja con patrón `(\d{4})\s*Renta`. Si no se puede determinar, la fila se omite.
- R8. `Rendimientos` es texto libre normalizado a `TaxReturnIncome[]` según tabla explícita (ver brainstorm origin).
- R9. `hasAssociatedCompany = true` cuando `CIF ≠ DNI1 Declarante`.
- R10. `status = TaxReturnStatus.NEW` para todos los registros importados. El frontend muestra este valor como "Pendiente" — no requiere cambio en enum ni migración.
- R11. `isBillable` desde `Facturable (SI/NO)` (`SI` → `true`, cualquier otro → `false`).
- R12. `amount` desde `Importe honorarios sin IVA`. Si el valor es no-numérico ("pendiente", "pte", etc.) → `amount = 0` (comportamiento esperado, sin warning). Si `isBillable = false` → `amount = 0`.
- R13. `nonBillingReason` desde `Motivo no facturación` según enum `NonBillingReason`. Valores no mapeables → `null` con aviso en `errors[]`.
- R14. Campos de fecha con número de soporte (código no-fecha, ej. `C01160794`, `EX-123456`) → `null`. La fila sigue importándose.
- R15. El campo `Finalizada` del Excel se ignora completamente.
- R16. El endpoint está protegido por `BackofficePermissions.TAX_RETURN_IMPORT` (nueva constante a añadir en `lib-core-definitions`).

**Origin actors:** A1 (Developer/Técnico), A2 (TaxReturn DB)
**Origin flows:** F1 (Importación de un fichero Excel via endpoint)

---

## Scope Boundaries

- No crea clientes ni empleados nuevos.
- No actualiza `TaxReturn` existentes.
- No hay UI de carga; trigger siempre es el endpoint REST autenticado.
- No integra con PGI ni valida coherencia fiscal.
- `Código Renta A3`, `Facturado`, `Mes factura`, `Finalizada` no se importan.
- `paymentMethod`, `companyRole`, `kinship`, `clientDeliveryDate` y `accountNumber` se mapean si existen pero no son requeridos.

---

## Context & Research

### Relevant Code and Patterns

- `src/application/rest/data-migration/data-migration.controller.ts` — añadir endpoint `POST /tax-returns` siguiendo el patrón existente.
- `src/domain/services/data-migration/data-migration.service.ts` — añadir `processTaxReturnsFile()`.
- `src/domain/services/data-migration/operations/clients-employment-profile.operation.ts` — patrón de referencia para la nueva `OperationTaxReturns`.
- `src/domain/services/data-migration/common/extract-rows-from-excel.ts` — ya usado en todas las operaciones; usar directamente.
- `src/domain/services/data-migration/mappers/` — reutilizar `mapExcelDate`, `mapBooleanFromExcel`, `mapOptionalNumber`. Añadir mappers específicos de Renta.
- `src/domain/models/tax-return.ts` — todos los enums a importar. No requiere cambios en `TaxReturnStatus`.

### Institutional Learnings

- MikroORM: escrituras siempre con `em.fork()`. Lecturas con `disableIdentityMap: true`.
- `xlsx` ya instalado como production dependency.
- Las operaciones de data-migration reciben `File` (Multer) y llaman a `extractRowsFromExcel` para obtener las filas.
- Permisos: cada operación tiene su propio `BackofficePermissions` constant definido en `lib-core-definitions`.

---

## Key Technical Decisions

- **`DataMigrationController/Service/Operation`, no script CLI**: sigue el patrón establecido en el codebase para que el import sea accesible de forma controlada y auditable (autenticado, con permiso específico).
- **`status = TaxReturnStatus.NEW`**: el frontend lo muestra como "Pendiente". No requiere nuevo valor en el enum ni migración.
- **EntityManager directo en la operación, no TaxReturnService**: `assertBillingInvariants` requiere `paymentMethod` cuando `isBillable=true`. Los datos históricos del Excel tienen esta columna vacía en varios registros. La operación usa `em.fork()` + `em.create()` + `em.persistAndFlush()` directamente.
- **Employee lookup por cache en memoria**: empleados son pocos (<100). Se cargan todos al inicio en `Map<fullNameLower, Employee>`. Evita N queries para ~600 filas.
- **Client lookup con cache local**: `Map<string, Client>` por sesión (patrón de `clients-employment-profile.operation.ts`). Evita queries repetidas para mismo NIF.
- **`BackofficePermissions.TAX_RETURN_IMPORT`**: nueva constante a añadir en `@afianza-ac/lib-core-definitions`. Coordinar con quien gestione ese paquete.

---

## Open Questions

### Resolved During Planning

- **¿TaxReturnService o EntityManager directo?** → EntityManager directo. `assertBillingInvariants` demasiado estricto para datos históricos.
- **¿Employee.name + surname son campos separados?** → Sí. Cache en memoria con key `${name} ${surname}`.trim().toLowerCase().
- **¿Mapeo completo de `NonBillingReason`?** → "Cuota PJ" → `CORPORATE_FEE`, "Cuota PF" → `INDIVIDUAL_FEE`, "Familiar cliente" → `FAMILY_MEMBER`. Otros → `null` + warning.
- **¿Script o endpoint?** → Endpoint. La PO requiere que siga el modelo de data-migration existente.
- **¿Status NEW o PENDING?** → `TaxReturnStatus.NEW`. El frontend ya lo muestra como "Pendiente". Sin cambios en el enum ni migración.

### Deferred to Implementation

- **Valores de `Forma de pago`**: columna mayoritariamente vacía en billables. El mapper mapea si existe, no bloquea si vacío.
- **`Kinship.SOCIO`**: "Socio" aparece en `Parentesco` pero no existe en el enum. Queda `null` + warning.
- **`BackofficePermissions.TAX_RETURN_IMPORT`**: confirmar con responsable de `lib-core-definitions` cómo añadirlo (podría requerir PR en otro repo o bump de versión).

---

## High-Level Technical Design

```
POST /v1/data-migration/tax-returns (multipart/form-data)
  │
  ├── DataMigrationController.uploadTaxReturns()
  │     @PermissionsRequired(BackofficePermissions.TAX_RETURN_IMPORT)
  │
  ├── DataMigrationService.processTaxReturnsFile(file, config, user)
  │
  └── OperationTaxReturns.importFromFile(file, config, user)
        │
        ├── extractRowsFromExcel(file) → rows[]
        ├── XLSX sheet lookup: busca sheet con "Renta" en nombre
        ├── [Cache] carga todos los Employee → Map<fullNameLower, Employee>
        ├── [Cache] Map<nif, Client> vacío para cache local
        │
        └── para cada fila:
              ├── extractFiscalYear(row, sheetName) → number | null (skip si null)
              ├── normalizeRendimientos(raw) → TaxReturnIncome[]
              ├── parseDate(raw) → Date | null (null si número de soporte)
              ├── parseAmount(raw) → number (0 si no-numérico)
              ├── lookup Client por CIF → billingClient (acumula error si no existe)
              ├── lookup Client por DNI1 → invoiceRecipient (fallback billingClient)
              ├── lookup Employee por nombre → advisor, responsible
              ├── idempotency: em.findOne(TaxReturn, { declarantNif, fiscalYear })
              └── em.fork().create(TaxReturn, { status: TaxReturnStatus.NEW, ... }) + flush()
        │
        └── return { ok, errors[] }
```

---

## Implementation Units

### U0. Prerequisite: BackofficePermissions.TAX_RETURN_IMPORT en lib-core-definitions

**Goal:** Añadir el permiso `TAX_RETURN_IMPORT` a `BackofficePermissions`. No requiere cambios en `TaxReturnStatus` ni migración.

**Requirements:** R16

**Dependencies:** Ninguna

**Files:**
- Coordinar: añadir `TAX_RETURN_IMPORT` a `BackofficePermissions` en `lib-core-definitions` (puede requerir bump de versión del paquete)

**Verification:**
- `BackofficePermissions.TAX_RETURN_IMPORT` resolvible en el controller sin error de TypeScript.

---

### U1. Mappers específicos de Renta

**Goal:** Funciones puras de transformación de datos del Excel a tipos del dominio. Testables en aislamiento.

**Requirements:** R7, R8, R12, R13, R14

**Dependencies:** Ninguna (no requiere U0)

**Files:**
- Create: `src/domain/services/data-migration/mappers/tax-return-income.mapper.ts`
- Create: `src/domain/services/data-migration/mappers/tax-return-non-billing-reason.mapper.ts`
- Create: `src/domain/services/data-migration/mappers/tax-return-fiscal-year.mapper.ts`
- Edit: `src/domain/services/data-migration/mappers/index.ts` — exportar los nuevos mappers
- Test: `src/domain/services/data-migration/mappers/tax-return-income.mapper.spec.ts`

**Approach:**
- `mapTaxReturnIncome(raw: string): { values: TaxReturnIncome[]; warnings: string[] }` — tabla de mapeo del brainstorm, case-insensitive, partial match.
- `mapNonBillingReason(raw: string): NonBillingReason | null` — "Cuota PJ" → `CORPORATE_FEE`, "Cuota PF" → `INDIVIDUAL_FEE`, "Familiar cliente" → `FAMILY_MEMBER`. Resto → `null`.
- `extractFiscalYear(ejercicioCell: unknown, sheetName: string): number | null` — columna primero, fallback a regex `/(\d{4})\s*Renta/i` contra nombre de hoja.
- Reutilizar `mapExcelDate` existente para fechas (ya maneja códigos no-fecha → `null`).
- `parseAmount(raw: unknown): number` — `parseFloat` con normalización de coma decimal; no-numérico → `0`.

**Patterns to follow:**
- `src/domain/services/data-migration/mappers/excel-date.mapper.ts` — retorno `value | null`.
- `src/domain/services/data-migration/mappers/number-float.mapper.ts` — retorno numérico.

**Test scenarios (income mapper):**
- `mapTaxReturnIncome('RT')` → `{ values: ['RT'], warnings: [] }`
- `mapTaxReturnIncome('RT RAE')` → `{ values: ['RT', 'RAE'], warnings: [] }`
- `mapTaxReturnIncome('Actividades económicas')` → `{ values: ['RAE'], warnings: [] }`
- `mapTaxReturnIncome('')` → `{ values: [], warnings: [] }`
- `mapTaxReturnIncome('UNKNOWN')` → `{ values: [], warnings: ['...'] }`

**Verification:**
- `npx jest --testPathPattern=tax-return-income` pasa todos los casos.
- No importa NestJS ni MikroORM.

---

### U2. OperationTaxReturns

**Goal:** Lógica de importación: lee Excel, resuelve entidades, crea `TaxReturn` con idempotencia.

**Requirements:** R1, R2, R3, R4, R5, R6, R7, R9, R10, R11, R12, R13, R14, R15

**Dependencies:** U0, U1

**Files:**
- Create: `src/domain/services/data-migration/operations/tax-returns.operation.ts`

**Approach:**
- Clase `OperationTaxReturns` con constructor que recibe `EntityManager`, `ClientsService`, `EmployeesService`.
- `importFromFile(file: File, config: { skipErrors: boolean }, user: BackofficeUser): Promise<OperationResult>`
- Patrón `extractRowsFromExcel` + sheet lookup por nombre con "Renta".
- Cache de empleados al inicio: `em.findAll(Employee, { disableIdentityMap: true })`.
- Cache local de clientes: `Map<string, Client>` por sesión.
- Por fila: normalizar → resolver entidades → idempotencia → `em.fork().create(TaxReturn, { status: TaxReturnStatus.PENDING, ... })` + `emFork.persistAndFlush()`.
- Acumular errores en `errors[]`; respetar `config.skipErrors`.

**Patterns to follow:**
- `clients-employment-profile.operation.ts` — estructura general, clientCache, acumulación de errores.

---

### U3. DataMigrationService + Controller

**Goal:** Exponer el endpoint REST y conectar con la operación.

**Requirements:** R1, R2, R16

**Dependencies:** U2

**Files:**
- Edit: `src/domain/services/data-migration/data-migration.service.ts` — añadir `processTaxReturnsFile()` + inyectar `EntityManager`, `ClientsService`, `EmployeesService` si no están ya inyectados; instanciar `OperationTaxReturns`.
- Edit: `src/application/rest/data-migration/data-migration.controller.ts` — añadir `POST /tax-returns` con `@PermissionsRequired(BackofficePermissions.TAX_RETURN_IMPORT)`.
- Test: `src/application/rest/data-migration/data-migration.controller.spec.ts` (o crear si no existe) — caso success + caso 401/403.

---

## System-Wide Impact

- **Sin cambios en `TaxReturnStatus`**: se usa `NEW` existente. No hay migración de enum.
- **Nuevo permiso `TAX_RETURN_IMPORT`**: requiere asignación en los roles del sistema antes de poder usarse.
- **Sin eventos RabbitMQ**: la operación no publica eventos.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `BackofficePermissions.TAX_RETURN_IMPORT` en lib-core-definitions | Coordinar antes de empezar U3. Puede requerir bump de versión del paquete. |
| `assertBillingInvariants` si alguien cambia la operación a usar el Service | Documentado explícitamente: usar EM directo. No cambiar sin revisar este riesgo. |
| Empleados no encontrados por variación de nombre | Log de warnings; el asesor asigna manualmente en el backoffice. |

---

## Sources & References

- **Origin document:** [docs/brainstorms/2026-05-11-importacion-rentas-requirements.md](docs/brainstorms/2026-05-11-importacion-rentas-requirements.md)
- Patrón de referencia: `pgi-service-pgi-api/src/domain/services/data-migration/operations/clients-employment-profile.operation.ts`
- Controlador existente: `pgi-service-pgi-api/src/application/rest/data-migration/data-migration.controller.ts`
- Entidad destino: `pgi-service-pgi-api/src/domain/models/tax-return.ts`
- Servicio (referencia, no usado): `pgi-service-pgi-api/src/domain/services/tax-return/tax-return.service.ts`
