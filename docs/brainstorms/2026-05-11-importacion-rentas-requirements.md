---
date: 2026-05-11
topic: importacion-rentas
---

# Importación de Rentas (IRPF) desde Excel

## Summary

Script de importación en `pgi-service-pgi-api` que lee ficheros Excel de declaraciones de Renta (IRPF, Modelo 100) — uno por asesor responsable — y crea registros `TaxReturn` en la base de datos, mapeando campo a campo desde la hoja "Renta" al modelo ya existente.

---

## Problem Frame

El equipo gestiona campañas de Renta anualmente. Hasta ahora, los asesores responsables mantienen los datos de cada declaración en ficheros Excel individuales (un fichero por responsable, ~600 filas cada uno). El sistema ya tiene la entidad `TaxReturn` con todos los campos necesarios y una API REST para crearlos manualmente, pero no existe ningún mecanismo para cargar en bloque los datos históricos acumulados en los Excels.

Sin el import, los registros del ejercicio 2025 solo pueden crearse uno a uno vía backoffice, lo que hace inviable la carga inicial del histórico.

---

## Actors

- A1. **Developer**: ejecuta el script desde la terminal, una vez por fichero Excel.
- A2. **TaxReturn DB (pgi-service-pgi-api)**: destino de los registros creados.

---

## Key Flows

- F1. **Importación de un fichero Excel**
  - **Trigger:** Developer ejecuta `npx ts-node scripts/import-rentas.ts <ruta-fichero.xlsx>`
  - **Actors:** A1, A2
  - **Steps:**
    1. El script lee la hoja activa del Excel (nombre contiene "Renta").
    2. Para cada fila, busca el `Client` correspondiente por `CIF` (trim + uppercase).
    3. Si no encuentra cliente, registra la fila en el log de errores y continúa.
    4. Comprueba si ya existe un `TaxReturn` con el mismo `declarantNif + fiscalYear`; si existe, salta la fila (idempotencia).
    5. Normaliza los valores de `Rendimientos` (texto libre → `TaxReturnIncome[]`).
    6. Busca `Employee` por nombre para `advisor` y `responsible`; si no encuentra, deja el campo nulo y lo registra en el log de advertencias.
    7. Crea el registro `TaxReturn` con todos los campos mapeados.
  - **Outcome:** Todos los registros válidos existen en la BD; las filas con errores están documentadas en el log de salida.
  - **Covered by:** R1, R2, R3, R4, R5, R6, R7, R9

---

## Requirements

**Ejecución**

- R1. El script recibe la ruta al fichero `.xlsx` como argumento posicional. Si no se proporciona o el fichero no existe, termina con error claro antes de tocar la BD.
- R2. El script imprime al finalizar un resumen: filas procesadas, registros creados, filas omitidas (ya existentes), filas con error (cliente no encontrado u otro fallo).

**Identificación de entidades**

- R3. El cliente (`billingClient`) se busca por `Client.nif = Excel.CIF` (trim + uppercase). Si no se encuentra, la fila se omite con log de error; no se crean clientes nuevos.
- R4. El `invoiceRecipient` es el mismo cliente que `billingClient` salvo que `Excel.CIF` sea distinto de `Excel.DNI1 Declarante`, en cuyo caso se intenta buscar también un `Client` con `nif = DNI1 Declarante`; si no existe, se usa `billingClient` como fallback.
- R5. `advisor` y `responsible` se buscan en `Employee` por nombre completo (nombre + apellido). Si no se encuentra coincidencia exacta, el campo queda nulo y se registra un aviso en el log. El import no falla por empleados no encontrados.

**Idempotencia y calidad de datos**

- R6. Una fila se considera duplicada si ya existe un `TaxReturn` con el mismo `declarantNif + fiscalYear`. Las filas duplicadas se saltan sin error.
- R7. `fiscalYear` se toma de la columna `Ejercicio` del Excel. Si la columna está vacía, se extrae del nombre de la hoja (patrón `YYYY Renta`). Si no se puede determinar en ninguno de los dos sitios, la fila se omite con log de error.

**Normalización de rendimientos**

- R8. El campo `Rendimientos` del Excel es texto libre con separadores variables (espacio, coma). El script lo normaliza a `TaxReturnIncome[]` usando el siguiente mapeo explícito. Valores no reconocidos se registran como advertencia y se omiten del array.

  | Valor Excel (case-insensitive, parcial) | `TaxReturnIncome` |
  |---|---|
  | `RT` | `RT` |
  | `RAE`, `actividades económicas`, `actividades economicas` | `RAE` |
  | `RCI`, `arrendamiento` | `RCI` |
  | `RCM` | `RCM` |
  | `GP`, `PP` | `GP_PP` |
  | `DC`, `DEC`, `deducción cine`, `deduccion cine` | `DC` |
  | `DDI`, `doble imposición` | `DDI` |
  | `CRIPTO`, `criptomoneda` | `CRIPTO` |

**Empresa asociada**

- R9. `hasAssociatedCompany` se establece a `true` cuando `Excel.CIF` es distinto de `Excel.DNI1 Declarante` (empresa distinta al declarante). En caso contrario, `false`.

**Estado y facturación**

- R10. `TaxReturn.status` se inicializa a `NEW` para todas las filas importadas, independientemente del valor de la columna `Finalizada`.
- R11. `isBillable` se mapea desde la columna `Facturable` (`SI` → `true`, cualquier otro valor → `false`).
- R12. Si `isBillable = true`, `amount` se toma de `Importe honorarios sin IVA`. Si la columna está vacía con `isBillable = true`, `amount` queda a `0` y se registra advertencia.
- R13. `nonBillingReason` se mapea desde `Motivo no facturación` según el enum `NonBillingReason` existente. Valores no mapeables dejan el campo nulo con advertencia en log.

---

## Acceptance Examples

- AE1. **Covers R3.** Dado un Excel donde la fila tiene `CIF = B09890245` y existe un `Client` con `nif = 'B09890245'`, cuando el script procesa esa fila, se crea el `TaxReturn` con `billingClient.nif = 'B09890245'`.

- AE2. **Covers R3.** Dado un Excel donde la fila tiene `CIF = X9999999Z` y no existe ningún `Client` con ese NIF, cuando el script procesa esa fila, no se crea ningún `TaxReturn` y la fila aparece en el log de errores.

- AE3. **Covers R6.** Dado que ya existe un `TaxReturn` con `declarantNif = '53412111Q'` y `fiscalYear = 2025`, cuando el script procesa una fila con los mismos valores, no crea un registro adicional y lo reporta como "omitido (ya existe)".

- AE4. **Covers R7.** Dado un Excel con columna `Ejercicio` vacía y nombre de hoja `"2025 Renta (2)"`, cuando el script procesa las filas, el `fiscalYear` de todos los registros creados es `2025`.

- AE5. **Covers R8.** Dado una fila con `Rendimientos = "RT RAE"`, cuando el script normaliza el campo, `income = ['RT', 'RAE']`. Dado `Rendimientos = "Actividades económicas"`, `income = ['RAE']`.

- AE6. **Covers R9.** Dado `CIF = 'B09890245'` y `DNI1 Declarante = '53412111Q'` (distintos), cuando se crea el `TaxReturn`, `hasAssociatedCompany = true`. Dado `CIF = '52369517N'` y `DNI1 Declarante = '52369517N'` (iguales), `hasAssociatedCompany = false`.

- AE7. **Covers R11, R12.** Dado `Facturable = "SI"` y `Importe honorarios sin IVA = 160`, cuando se crea el `TaxReturn`, `isBillable = true` y `amount = 160`.

- AE8. **Covers R11, R13.** Dado `Facturable = "NO"` y `Motivo no facturación = "Cuota PJ"`, cuando se crea el `TaxReturn`, `isBillable = false` y `nonBillingReason = 'CORPORATE_FEE'`.

- AE9. **Covers R1.** Dado que el script se ejecuta sin argumentos, termina con un mensaje de error legible y código de salida no-cero, sin conectar a la BD.

---

## Success Criteria

- Todos los ficheros Excel del ejercicio 2025 están importados en la BD sin intervención manual fila a fila.
- Re-ejecutar el script con el mismo fichero no crea duplicados.
- El log de salida identifica exactamente qué filas fallaron y por qué, de forma accionable (qué CIF no se encontró, qué valor de Rendimientos no se reconoció, etc.).
- Los registros importados aparecen correctamente en la vista de búsqueda de `GET /v1/tax-returns/search` del backoffice.

---

## Scope Boundaries

- No crea clientes ni empleados nuevos — solo linkea con los que ya existen.
- No actualiza `TaxReturn` existentes — solo crea los que no existen.
- No hay UI de carga de ficheros; el trigger es siempre el script de terminal.
- No integra con PGI (sistema externo de IRPF) — ese es alcance separado.
- `Código Renta A3`, `Facturado` y `Mes factura` no se importan (marcados "NADA" en el documento de mapeo).
- El script no valida la coherencia fiscal del contenido (casillas, importes) — solo mapea y persiste.

---

## Key Decisions

- **Servicio destino: `pgi-service-pgi-api`** — la entidad `TaxReturn` ya existe aquí con exactamente los campos del Excel. Data-factory no es necesario.
- **Idempotencia por `declarantNif + fiscalYear`** — combinación suficientemente única dentro de una campaña anual; evita re-imports accidentales sin necesitar un ID externo.
- **`status = NEW` para todos los imports** — la columna `Finalizada` refleja estado operativo en A3, no en nuestro sistema. El estado real se gestionará desde el backoffice tras la importación.
- **Employee matching por nombre exacto** — campo no crítico para el import; fallo silencioso con advertencia es preferible a bloquear la fila.

---

## Dependencies / Assumptions

- Los clientes (empresas) deben existir en la BD de `pgi-service-pgi-api` antes de ejecutar el import. Si un CIF no está, esa fila no se importa.
- El `invoiceRecipient` es en la mayoría de los casos el mismo cliente que `billingClient`. Para declarantes personas físicas cuyo NIF no coincida con el CIF de empresa, el campo `invoiceRecipient` quedará igual a `billingClient` si el declarante no existe como `Client`.
- Se asume que el mapeo `NonBillingReason` es: `"Cuota PJ"` → `CORPORATE_FEE`, `"Cuota PF"` → `INDIVIDUAL_FEE`. Los demás valores del Excel no están presentes en los datos actuales; se registrarán como advertencia si aparecen.
- El paquete `xlsx` (o equivalente) no está instalado en `pgi-service-pgi-api`. Habrá que añadirlo como dev-dependency o en scripts.

---

## Outstanding Questions

### Resolve Before Planning

- [Afecta R12] ¿Cuál es el mapeo completo de `Motivo no facturación` → `NonBillingReason`? Solo se observan "Cuota PJ" y "Cuota PF" en los datos actuales. Confirmar si hay más valores posibles.

### Deferred to Planning

- [Afecta R4][Needs research] ¿Existen en la BD clientes persona física (con DNI como NIF) que puedan ser `invoiceRecipient` distintos del `billingClient`? Verificar con una query antes de implementar el fallback.
- [Afecta R5][Needs research] ¿El modelo `Employee` en `pgi-service-pgi-api` tiene `name` + `surname` como campos separados? Confirmar la query de match más fiable (nombre completo vs búsqueda por `orgEmail` si está disponible).
- [Técnico] Decidir si el script llama al `TaxReturnService` (bootstrap completo de NestJS) o escribe directo vía `EntityManager` (más ligero, patrón de los scripts existentes `apply-migrations.ts`).
