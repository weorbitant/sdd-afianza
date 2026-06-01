# Mensaje a PO — Seguimiento sesión 2026-06-01

> Tras tu feedback post-meeting, las preguntas 2 (validación bloqueante), 3 (nombre de equipo) y 4 (bajas largas) ya quedaron respondidas verbalmente o reformuladas. Queda **1 punto** que aún necesita confirmación explícita del PO antes de codificar el constraint de BD.

---

Hola, una última aclaración tras la sesión de ayer:

## Una persona en más de un equipo a la vez

Dijiste que *"una persona no puede ocupar simultáneamente más de un equipo/rol en el mismo periodo"*. Lo necesitamos cerrar antes de añadir el constraint a la BD:

- (a) **No más de un ROL dentro del mismo equipo** — ej. Pedro no puede ser coordinador y asesor del mismo equipo Fiscal del cliente X. *(Esto es lo que ya teníamos asumido.)*
- (b) **No en más de un EQUIPO, punto** — ej. Pedro no puede ser asesor del equipo Fiscal del cliente X **y a la vez** asesor del equipo Laboral del mismo cliente X. *(Más restrictivo: cambia el modelo de datos.)*

**Importante en relación con la regla del 100% por departamento que confirmaste**: si la respuesta es (a), un mismo asesor PODRÍA estar en dos equipos del mismo departamento (ej. Pedro Asesor en Equipo 1 Fiscal al 25% + Pedro Asesor en Equipo 2 Fiscal al 25% → suma 50% suya, dentro del 100% Fiscal). Si la respuesta es (b), eso queda prohibido y cada equipo del departamento tiene asesores disjuntos.

¿(a) o (b)?

Gracias 🙌

---

## Resueltas ya (no preguntar más)

- **Suma 100% por departamento, dos buckets**: Asesores Fiscal 100% + Técnicos Fiscal 100%, agregando entre todos los equipos del departamento. Confirmado con frame `08-multi-equipo/01`.
- **Validación bloqueante**: solo composición mínima (1 responsable + 1+ asesor por equipo) bloquea Guardar. La suma 100% se queda como advisory.
- **Nombres de equipo**: descartados de scope. No hay campo `name` en BD. UI muestra `Equipo 1`, `Equipo 2` por orden.
- **Bajas largas**: gestión estándar (fecha fin + sustitución manteniendo el 100% por departamento). No se construye entidad de suplencia temporal.
