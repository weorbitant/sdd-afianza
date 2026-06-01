# Mensaje a PO — Seguimiento sesión 2026-06-01

> Para mandar por Slack / mail / comentario en Epic DEVPT-518.
> Tono: gracias por la sesión + 4 dudas concretas que necesitamos confirmar antes de empezar a tocar código.

---

Hola, muchas gracias por la sesión de hoy — cerramos un montón de cosas. Antes de ponernos a implementar, hay **4 puntos** en los que necesitamos confirmación o aclaración porque pueden ir en direcciones contrarias y queremos no equivocarnos:

## 1 · Una persona en más de un equipo a la vez

Dijiste que *"una persona no puede ocupar simultáneamente más de un equipo/rol en el mismo periodo"*. Necesitamos confirmar qué significa exactamente:

- (a) **No más de un ROL dentro del mismo equipo** — ej. Pedro no puede ser coordinador y asesor del mismo equipo Fiscal del cliente X. *(Esto es lo que ya teníamos asumido).*
- (b) **No en más de un EQUIPO, punto** — ej. Pedro no puede ser asesor del equipo Fiscal del cliente X **y a la vez** asesor del equipo Laboral del mismo cliente X. *(Esto sería más restrictivo y cambia el modelo de datos).*

¿Cuál de las dos? La respuesta afecta a un constraint de base de datos que tenemos que añadir antes de codificar nada.

## 2 · Validación bloqueante: composición mínima vs suma 100%

Confirmaste que el botón **Guardar** debe estar bloqueado mientras falten roles obligatorios (1 responsable + 1+ asesor). Necesitamos saber si **el mismo bloqueo aplica también cuando la suma de asesores+técnicos ≠ 100%**, o si en ese caso vale con el banner amarillo advisory (que es lo que muestra el diseño).

- (a) Bloquear guardado también si suma ≠ 100% — coherente y estricto.
- (b) Sólo bloquear por composición mínima, dejar el 100% como advisory — lo que el diseño actual ya muestra (banner amarillo + permite guardar a medias).

## 3 · Nombres de equipo (Libros, Cuota, Larsa, Costa)

Nos dijiste que ignoráramos esos nombres porque no representan regla de negocio. **¿Eso significa que los equipos no tienen nombre en absoluto, o que sí lo tienen pero es texto libre del responsable?** El diseño actual muestra los equipos con etiqueta (*"Equipo Libros"*, etc.), así que algún campo nombre parece haber. Solo necesitamos saber si:

- (a) No hay nombre — los equipos se identifican por su composición y fechas.
- (b) Hay un campo `nombre` libre que el responsable rellena — sin reglas de validación más allá de unicidad por cliente+departamento.

## 4 · Bajas largas: cómo escalar exactamente

Dijiste que la prioridad es reasignar a otro asesor y, si no hay, escalar hacia coordinador o responsable. ¿Cómo prefieres que funcione el escalado?

- (a) **Manual**: cuando un asesor causa baja sin sucesor, el sistema avisa al coordinador (o responsable si no hay coord) y este decide qué hacer.
- (b) **Automático**: el sistema reasigna las tareas directamente al coordinador (si existe) o al responsable.
- (c) **Híbrido**: automático con una ventana de "X días para que un humano lo cambie" antes de cerrar.

---

Con estas 4 respuestas podemos arrancar el diseño técnico. Las demás cosas que quedaron pendientes (qué rol hace cada tarea, TaxDown, vista de anomalías) no bloquean este sprint — las tratamos en otro momento.

Gracias 🙌
