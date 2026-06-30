# Polyrepo · flujos cross-service

Este workspace es un polyrepo con múltiples servicios que se comunican vía AMQP (RabbitMQ) y, en algunos casos, comparten modelos parecidos pero desacoplados (ej. `ClientAssignment` vive en `pgi-service-pgi-api`, `pd-service-data-factory` y `pd-service-jira-adapter` con definiciones distintas).

## Regla

Antes de redactar preguntas, decisiones o spec sobre **flujos de datos que cruzan servicios** (eventos AMQP, mensajes, modelos compartidos, sincronización con Jira Assets, etc.), **verifica primero en código** con `grep` / `find` sobre los servicios implicados. No presentes opciones especulativas cuando hay código que despeja la duda.

## Servicios principales a comprobar

Clonados en este workspace (grep directo):

- `pgi-service-pgi-api` — backoffice (clientes, asignaciones, equipos).
- `pgi-app-pgi-web` — frontend backoffice.
- `pc-service-portalcliente-api` — portal del cliente.
- `pd-service-data-factory` — hub de agregación; consume de Jira, Sage, AzureAD; publica a backoffice y otros.
- `pd-service-obligations-api` — obligaciones fiscales.

Desplegados pero **no clonados en local** (clónalos desde `github.com/afianza-ac` si necesitas verificar su lado):

- `pd-service-jira-adapter` — sync con Jira Assets y eventos `issueClientServicePersisted`. Mantiene su propio `ClientAssignment`.
- `pd-service-azuread-adapter` — Microsoft Graph.

## Patrones útiles

- AMQP subscribers viven en `src/application/amqp/<topic>-subscriber/`.
- Modelos compartidos pero desacoplados — buscar el mismo nombre de entidad en varios servicios (`grep -rli "ClientAssignment"`) para detectar drift.
- Eventos publicados — buscar `publish`, `emit`, `rabbitmq` en `src/application/amqp/`.

## Por qué

Especular sobre flujos cross-service cuando el código está a un grep de distancia desperdicia tiempo y produce specs con opciones falsas. En la sesión de refinamiento de DEVPT-518 (asignaciones con porcentajes) se descubrió tarde que `pd-service-data-factory` y `pd-service-jira-adapter` ya consumían y mantenían sus propios `ClientAssignment` — esa información cambió la spec (añadió FR-032..FR-035 sobre propagación AMQP) y debía haberse comprobado en el primer pase.
