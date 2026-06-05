---
paths:
  - "specs/**/contracts/**"
  - "**/application/rest/**"
---

# REST API design — Afianza

Convenciones para diseñar endpoints REST en los servicios NestJS del polirepo y para redactar contratos en `specs/<feature>/contracts/`.

> **Aviso de honestidad** (2026-06-04): este documento mezcla **convenciones reales en uso** (lo que el código de pgi-api hace hoy) con **convenciones aspiracionales** (RFC 7807, `If-Match`, etc.) que NO están enforce en el código actual. Lee primero "Convenciones reales en uso" — eso es lo que mandan en cualquier feature nueva que aterrice en un servicio existente. La sección "Aspiracional" describe el destino y se adopta por contacto, no de golpe.

---

## Convenciones reales en uso (pgi-api, vinculantes)

Estas son las que ves en `pgi-service-pgi-api/src/application/rest/`. Si tu feature aterriza ahí, **alinea a esto**, no a la sección aspiracional.

### Estructura de controller

```ts
@ApiTags('Resource Name')
@Controller({ path: 'resource-name', version: '1' })
export class ResourceController {
  constructor(private readonly resourceService: ResourceService) {}

  @PermissionsRequired(BackofficePermissions.RESOURCE_VIEW)
  @ApiOperation({ summary: '...' })
  @ApiResponse({ status: HttpStatus.OK, description: '...' })
  @Get('/:id')
  async getById(@Param('id', new ParseUUIDPipe()) id: string): Promise<ResourceDto> { ... }
}
```

Requisitos no negociables (los enforce `application-rest.md` rule del servicio):
- **Path versioning** con `@Controller({ path, version: '1' })`. Nest expone `/api/v1/...` automáticamente.
- **Permission decorator obligatorio**: `@PermissionsRequired(BackofficePermissions.X_VIEW | X_EDIT)` por endpoint. No hay endpoints sin auth.
- **Swagger decorators** (`@ApiTags`, `@ApiOperation`, `@ApiResponse`) en todos los endpoints.
- **Controllers devuelven DTOs**, nunca entities MikroORM. Mapper `to<Name>Dto(entity)` en el folder `dto/`.
- **Zero `this.em.*`** en controllers — eso es domain layer.

### Forma de response — lista

```json
{
  "data": [ { ...resource }, ... ],
  "total": <integer>,
  "<extra1>": <value>,
  "<extra2>": <value>
}
```

- **`data`**: array del recurso. NO `items`, NO el nombre del recurso (`assignments`), NO `results`.
- **`total`**: número total. En paginación, total de la query (no de la página).
- **Extras opcionales** como siblings: `coverage`, `hasAssignments`, `mainAsesorPresent`, `status`, etc. Solo se incluyen cuando aplican a la lista; si no, se omiten (no se devuelven en `null`).
- **Sin `aggregate` wrapper**. Los campos derivados van como siblings directos de `data`/`total`.
- **El recurso individual** (`GET /:id`) NO usa wrapper — devuelve el DTO plano.
- **POST de creación** devuelve `{ id }` o `void` (status 201 sin body si no aporta info).

Ejemplo real (`clients/search`):

```json
{ "data": [...], "total": 42, "hasAssignments": true }
```

Ejemplo para US-01 (`client-team-assignments/:clientId?department=fiscal`):

```json
{
  "data": [
    { "id": "...", "role": "responsable", "percentage": 100, "isMain": false, ... },
    { "id": "...", "role": "asesor",       "percentage": 100, "isMain": true,  ... }
  ],
  "total": 2,
  "coverage": { "asesores": 100, "tecnicos": null },
  "mainAsesorPresent": true,
  "status": "complete"
}
```

### Errores — NestJS exception filters built-in

Throw the appropriate NestJS exception desde el controller. El filter global serializa a:

```json
{ "statusCode": 422, "message": "...", "error": "Unprocessable Entity" }
```

- `NotFoundException` → 404
- `ConflictException` → 409 (duplicados, optimistic concurrency, estado conflictivo)
- `UnprocessableEntityException` → 422 (reglas de negocio violadas)
- `BadRequestException` → 400 (validation pipe lo hace solo cuando falla class-validator)
- `ForbiddenException` → 403 (cuando `@PermissionsRequired` no se cumple)
- `InternalServerErrorException` → 500 (último recurso — lo lanza el catch genérico)

El `message` lleva texto en lenguaje natural (a veces en español, ver código existente). **NO** usamos un campo `code` SCREAMING_SNAKE_CASE separado — el frontend discrimina con HTTP status + matching parcial del message cuando hace falta.

> **Honestidad sobre i18n**: hoy los mensajes mezclan inglés y español. Cuando creas un endpoint nuevo, prefiere español si el mensaje es accionable por el usuario final (UI lo muestra tal cual) — los devs pueden vivir con mensajes mezclados, pero el usuario no debería leer "Client not found".

### Optimistic concurrency

- Columna `version: smallint` en la entity con `@Property({ version: true })` de MikroORM.
- Cliente envía `version` en el body del request de update.
- Servidor compara con el actual; si difiere, lanza `ConflictException` con mensaje claro ("La asignación ha sido modificada por otro usuario.").
- Response 409. **No usamos `If-Match` header ni 412 todavía** (sección aspiracional).

### Validación

- `class-validator` + `class-transformer` en los DTOs (`@IsUUID`, `@IsEnum`, `@Min`, etc.).
- `ValidationPipe({ transform: true })` global → mensajes de validación llegan como array en `message` del `BadRequestException`.

### Permissions

- Definidas en `BackofficePermissions` (parte de `@afianza-ac/lib-core-definitions`). Para añadir una nueva, PR a esa lib.
- Granularidad típica: `<RESOURCE>_VIEW` + `<RESOURCE>_EDIT` (a veces más finas).
- Reuse antes de añadir: para `ClientTeamAssignment` reutilizamos `CLIENT_ASSIGNMENT_VIEW/EDIT`.

---

## Aspiracional — destino al que queremos llegar, no enforce hoy

Esto describe el "ought to be" del API design. **No lo apliques sin más en una feature nueva** si el servicio en el que aterriza no lo cumple. Migración por contacto: cuando ya haya N features alineadas, promovemos a obligatorio.

### Principios de URL

1. **URLs son recursos, no acciones**. Cada segmento un sustantivo en plural.
   - ❌ `POST /teams/{id}/close` · ✅ `PATCH /teams/{id}` con `endDate` en body.
   - **Estado actual**: existen `/bulk-delete`, `/publish` en `client-assignments` legacy. Aspiracional: removerlos o reescribirlos cuando se toquen.

2. **Max 2 niveles de nesting**.
   - ❌ `/clients/{c}/teams/{t}/members/{m}` · ✅ `/clients/{c}/assignments/{a}` con `teamId` en body.
   - **Estado actual**: el legacy `client-assignments` tiene 4 niveles. No replicar.

3. **Filters vía query params, no path**.
   - ❌ `/clients/{c}/department/{d}/...` · ✅ `/clients/{c}/...?department=...`
   - **Estado actual**: legacy `GET /client-assignments/:clientId/department/:department` viola. No replicar — usa query en código nuevo.

4. **Path = nombre del recurso real** (igual que la entity en BD).
   - ❌ `/members/{memberId}` si la entity es `ClientAssignment` · ✅ `/assignments/{assignmentId}`.

5. **Errores en `application/problem+json`** (RFC 7807) con `code` SCREAMING_SNAKE_CASE.
   - **Estado actual**: NestJS exception filter built-in. Aspiracional cuando todos los services adopten un filter custom unificado.

6. **Optimistic concurrency vía `If-Match: <version>`** header → 412 Precondition Failed (RFC 7232).
   - **Estado actual**: campo `version` en body, 409 ConflictException. Migración necesitaría aceptar ambas formas durante un período de transición y luego deprecar la del body.

### Status codes — tabla aspiracional

| Caso | Aspiracional | Hoy en pgi-api |
|---|---|---|
| Concurrencia | 412 (RFC 7232) | 409 (`ConflictException`) |
| Conflicto de estado | 409 | 409 |
| Regla de negocio violada | 422 | 422 |
| Validación de tipos | 400 | 400 (`ValidationPipe`) |
| Sin permiso | 403 | 403 (`@PermissionsRequired`) |
| No existe | 404 | 404 (`NotFoundException`) |
| Creación correcta | 201 | 201 |
| Update/read correcto | 200 | 200 |

### Forma de response — aspiracional (no usar todavía en pgi-api)

```json
{
  "items": [ ... ],
  "aggregate": { "<metric>": <value>, "status": "<enum>" }
}
```

Esta forma se propuso el 2026-06-04 durante DEVPT-518. **No se adopta** porque rompería el patrón establecido en pgi-api (`{ data, total }`). Se queda como destino si en algún momento se hace una migración coordinada de todos los services del polirepo a un wrapper unificado.

---

## Versionado (vinculante)

- `@Controller({ version: '1' })` → URI `/api/v1/...`. Configurado via `app.enableVersioning({ type: VersioningType.URI })`.
- Bump a `v2` solo en breaking change real. Métodos v2 conviven con v1 en el mismo controller usando `@Version('2')` (ejemplo en `clients.controller.ts`).
- Cambios aditivos (campos opcionales nuevos) NO requieren bump.

## Nombres de campos (vinculante)

- `camelCase` en JSON (no `snake_case`).
- Inglés en código. Evita Spanglish (ej. `causesBaja` → `dueToTermination`).
- Excepción: enums congelados del dominio (`department: 'fiscal' | 'laboral'`) por compat con `@afianza-ac/lib-core-definitions`.
- Mensajes de error: español si el usuario final los va a leer (FR-018 obliga a mostrarlos en toast). Inglés si son técnicos y solo los ven devs.

---

## Por qué este documento mezcla "real" y "aspiracional"

Durante DEVPT-518 (2026-06-04) propuse un contract que seguía la sección aspiracional (RFC 7807, `If-Match`, `{ items, aggregate }`) sin auditar lo que pgi-api hace en realidad. El resultado: un endpoint inconsistente con los otros 20 controllers del servicio.

Para evitar repetirlo, este documento ahora distingue explícitamente las dos secciones. La regla:

- **Empieza por "Convenciones reales en uso"** cuando diseñes un endpoint que aterriza en pgi-api (o cualquier servicio existente).
- **Solo aplica "Aspiracional"** si: (a) el servicio es nuevo y empieza desde cero, o (b) hay decisión arquitectónica explícita de migrar y la PR lo cita.
- **Cuando toques un endpoint existente que viola "Aspiracional"** y el cambio es pequeño, alinea solo lo barato (renombrar un field, mover un filter a query). Las migraciones grandes (RFC 7807, `If-Match`) se posponen.
