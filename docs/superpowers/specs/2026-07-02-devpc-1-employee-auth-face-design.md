# DEVPC-1 — Cara de autenticación de empleados en `af-nest-module-auth-v2`

- **Jira:** [DEVPC-1](https://afianza-ac.atlassian.net/browse/DEVPC-1) (Story, Epic padre [DEVPC-7](https://afianza-ac.atlassian.net/browse/DEVPC-7))
- **Fecha:** 2026-07-02
- **Estado:** Diseño para refinamiento
- **Paquete objetivo:** `@afianza-ac/nest-module-auth-v2` (hoy `v0.0.1`, sin consumidores)

## Contexto

Los servicios internos de Afianza (backoffice, `pgi-service-pgi-api`) los usan empleados
que ya se autentican con su cuenta corporativa en Entra ID (Azure AD). No existe una forma
común y reutilizable de que esos servicios validen ese acceso, y no se quiere que cada uno
monte su propio login.

En el código ya existe `af-nest-module-auth` (v1, `v0.3.5`, estable) que valida tokens
corporativos vía JWKS (`AzureADStrategy` + `AzureADGuard`) y que `pgi-api` consume hoy.
La decisión de producto para DEVPC-1 **no** es reutilizar v1 ni extenderlo, sino construir
la capacidad de nuevo **dentro de `af-nest-module-auth-v2`**, unificando el stack de
autenticación (`@nestjs/config`, `openid-client`, validación *fail-fast* en `onModuleInit`,
tests sólidos) en un único paquete.

`af-nest-module-auth-v2` ya implementa la cara **cliente** (Entra External ID / CIAM: flujo
OIDC + JWT interno). DEVPC-1 añade la cara **empleado** a ese mismo módulo.

## Objetivo

Que un servicio interno acepte únicamente las peticiones que llegan con un token corporativo
válido de Azure AD, y rechace el resto, sin montar una pantalla de login propia — usando un
único módulo compartido en el que la cara empleado se enciende de forma independiente de la
cara cliente.

## Alcance

**Incluye:**

- La cara empleado en `af-nest-module-auth-v2`: estrategia de validación de token corporativo
  (JWKS) y su guard.
- Reestructurar la configuración del módulo para que cada cara (empleado / cliente) se encienda
  de forma independiente, sin arrastrar la config de la otra.
- Validación *fail-fast* de la config en arranque.
- Documentación / ejemplo de integración de la cara empleado.
- Tests de la cara empleado y de la nueva estructura de config.

**No incluye:**

- Migrar `pgi-api` (u otro servicio) a la cara empleado de v2 — será otra story. `pgi-api`
  sigue con v1 por ahora.
- Resolver el usuario interno del empleado y aplicar permisos — es
  [DEVPC-3](https://afianza-ac.atlassian.net/browse/DEVPC-3), que esta story bloquea. Aquí solo
  se **valida** el token y se adjuntan los claims crudos.
- Cambiar el comportamiento de la cara cliente ya existente en v2 (solo se reorganiza su
  configuración para que deje de ser obligatoria cuando no se enciende).
- Cualquier flujo de login/callback/logout o JWT interno para empleados. El empleado llega
  ya autenticado con su token corporativo.

## Arquitectura

Un **único módulo** con **dos caras seleccionables por configuración**. Se importa y se
configura un solo `AuthModule`; no hay módulos separados de empleado y cliente.

```
af-nest-module-auth-v2   (@afianza-ac/nest-module-auth-v2)
│
└── AuthModule.forAsyncRoot({ ... })          ← un solo módulo, un solo import
     │
     ├── cara EMPLEADO  (nueva, DEVPC-1)
     │     valida token corporativo Azure AD vía JWKS  → EmployeeAuthGuard
     │
     └── cara CLIENTE   (ya en v2, sin cambios de comportamiento)
           flujo OIDC/CIAM + JWT interno            → JwtAuthGuard
```

Principios:

- **Un solo import.** Internamente cada cara tiene su estrategia y su guard (clases distintas),
  pero para el consumidor es un módulo.
- **Cada cara se enciende de forma independiente por config.** Encender una cara equivale a
  aportar su bloque de configuración.
- **La cara empleado no reutiliza el flujo de login del cliente.** Solo valida el token entrante.
- **La cara cliente no cambia de comportamiento**; solo su config deja de ser obligatoria cuando
  no se enciende.

## Configuración y arranque

Encender una cara = aportar su bloque de config. Debe haber **al menos una**.

```ts
AuthModule.forAsyncRoot({
  useFactory: (cfg: ConfigService) => ({
    // Cara EMPLEADO (DEVPC-1) — solo lo mínimo para validar el token corporativo
    employee: {
      tenantId: cfg.get('CORPORATE_TENANT_ID'),   // tenant corporativo de Afianza
      audience: cfg.get('CORPORATE_AUDIENCE'),     // aud/appId esperado en el token
      // issuer y jwksUri se derivan del tenantId — no se configuran a mano
    },

    // Cara CLIENTE (ya en v2) — solo si el servicio la necesita
    // client: { tenantId, clientId, clientSecret, jwtSecret,
    //           stateEncryptionKey, allowedRedirectOrigins, ... }
  }),
  inject: [ConfigService],
})
```

Un servicio interno como `pgi-api` pasaría **solo** el bloque `employee`: ni ve ni necesita
`clientSecret`, `stateEncryptionKey`, `allowedRedirectOrigins`, etc. Esa es la independencia
que exige el ticket.

### Fail-fast en arranque

Al inicializar el módulo, antes de aceptar ninguna petición, se valida:

- Que haya **al menos una cara** configurada; si no → error de arranque.
- Cara empleado: `tenantId` y `audience` presentes y no vacíos. Si falta alguno → el módulo
  lanza en el arranque con un mensaje que **nombra la clave que falta**.
- Cara cliente: sus campos obligatorios (ya cubierto por v2 hoy, que hace *discovery* OIDC en
  `onModuleInit` y falla si no puede).

**Decisión (fail-fast solo de config):** la validación de arranque comprueba que la config
está completa y bien formada. Las claves de firma (JWKS) se descargan de forma **perezosa y
cacheada** en la primera petición. Se descarta verificar en arranque la disponibilidad del
endpoint de metadatos del tenant corporativo, porque acoplaría el arranque del servicio a que
Microsoft esté disponible en ese instante (un corte breve impediría levantar el servicio).

**Compatibilidad:** `af-nest-module-auth-v2` está en `v0.0.1` y **ningún servicio lo consume
todavía**, así que reestructurar las options no rompe a ningún consumidor.

## Cara empleado — comportamiento

Estrategia de validación de token corporativo, equivalente en comportamiento a la
`AzureADStrategy` de v1 pero reescrita en el stack de v2.

### Qué valida (todo o nada; cualquier fallo → 401)

- **Firma** contra las claves públicas del tenant corporativo (JWKS, RS256). Cubre el token
  manipulado.
- **Issuer** — que provenga del tenant corporativo de Afianza y no de otro. Se aceptan las dos
  formas de issuer de Entra: `https://sts.windows.net/{tenantId}/` y
  `https://login.microsoftonline.com/{tenantId}/v2.0`. Cubre el token de otra organización.
- **Audience** — que el token esté emitido para este público (`audience`/appId configurado).
- **Expiración** — token caducado → rechazado.

### Qué adjunta a la petición cuando el token es válido

Los **claims crudos del token** y nada más: `oid`, `preferred_username`/`upn`, `name`, `tid`.
No busca al empleado en base de datos, no resuelve permisos, no hidrata un usuario interno.
La resolución de usuario y permisos es DEVPC-3, que se apoyará sobre estos claims.

Este es un cambio consciente respecto a v1, cuya `AzureADStrategy` sí llama a
`usersService.findByEmail` y monta permisos dentro de la propia estrategia. El diseño nuevo
separa **validar** (DEVPC-1) de **resolver usuario + permisos** (DEVPC-3): la cara empleado
queda más simple y testeable y no depende del modelo de usuarios de cada servicio.

### Qué NO incluye

Ningún endpoint de login, callback, logout ni JWT interno. El empleado ya trae su token
corporativo; el módulo solo lo valida y decide.

## Consumo desde un servicio

Cuando un servicio enciende la cara empleado, sus endpoints quedan **cerrados por defecto**
(token corporativo válido obligatorio) y los que deban ser abiertos se marcan explícitamente
como públicos. Es el mismo patrón que `pgi-api` usa hoy con v1, así que resulta familiar.

En términos del que escribe controllers:

- sin decorador → endpoint protegido,
- `@Public()` → endpoint abierto (p.ej. healthcheck).

El servicio enciende una sola cara y no elige estrategia en cada ruta salvo marcar lo público.

DEVPC-1 entrega, además del módulo, un **ejemplo/documentación** de integración de la cara
empleado. La integración real en un servicio concreto queda fuera de alcance.

## Manejo de errores

- **Token ausente, caducado, de otro issuer, con audience incorrecto o firma inválida** →
  `401 Unauthorized`. No se distingue el motivo hacia fuera (no se revela si fue "caducado" vs
  "otra org") para no dar pistas a un atacante; el detalle va al log interno.
- **Config incompleta al arrancar** → el proceso **no levanta**; lanza con un mensaje que nombra
  la clave que falta. Ninguna petición se ejecuta con config a medias.
- **JWKS no disponible en la primera petición** (Microsoft caído justo entonces) → esa petición
  se rechaza y se reintenta en la siguiente; no tira el servicio. Es la consecuencia esperada de
  haber elegido JWKS perezoso.

## Testing

Se replica la profundidad de test que ya tiene v2, centrada en la cara empleado:

- **Estrategia de validación:** token válido pasa; caducado, con issuer de otro tenant, con
  audience incorrecto y con firma inválida → rechazados. Se mockean las claves JWKS para no
  depender de red.
- **Fail-fast de arranque:** con `employee` sin `tenantId` o sin `audience`, el módulo lanza al
  inicializar; con config completa, arranca. Con **ninguna** cara configurada, lanza.
- **Independencia:** un servicio que enciende solo `employee` no requiere ni toca config de
  cliente; encender `client` no altera la validación de empleado.
- **Claims adjuntados:** tras validar, la petición expone los claims crudos esperados (`oid`,
  `upn`/`preferred_username`, `name`, `tid`) y nada de usuario/permisos.

## Criterios de aceptación (del ticket)

- **Dado** un empleado con sesión corporativa válida, **cuando** llama a un endpoint protegido,
  **entonces** accede correctamente.
- **Dado** un token caducado, de otra organización o manipulado, **cuando** se llama a un
  endpoint protegido, **entonces** se rechaza como no autorizado (401).
- **Dado** un servicio con la configuración de la cara empleado incompleta, **cuando** arranca,
  **entonces** falla en el arranque, no en la primera petición.
- *(restricción)* La cara empleado es independiente de la cara cliente: encender una no obliga
  a configurar la otra ni afecta a su comportamiento.

## Decisiones y notas de refinamiento

- **Greenfield en v2, no reutilizar v1:** decisión de producto. v1 queda como está para quien lo
  use; la capacidad se reconstruye en v2 para unificar el stack.
- **DEVPC-4 (guard global "mode-based") fue desestimada:** por eso no hay un interruptor global
  que adivine la estrategia. Cada servicio enciende explícitamente su cara.
- **PR abierto que contradice el ticket:** existe un PR sobre v1
  (`feat/devpc-1-external-id-strategy`, etiquetado DEVPC-1) que mete un `ExternalIDStrategy`
  (cliente) dentro de v1. Choca con la restricción de independencia y con la decisión de que la
  cara cliente vive en v2. **Acción pendiente fuera de esta spec:** decidir el cierre/redirección
  de ese PR.
```
