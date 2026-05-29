---
paths:
  - "**/src/application/amqp/**"
  - "**/src/domain/**/*.service.ts"
---

# Cross-service communication (RabbitMQ)

- **vhost**: `data_platform`
- **Exchange**: `internal` (topic-based)
- **Routing key pattern**: `<service>.v1.<entity>.<event>` (e.g., `backoffice-api.v1.employee.updated`)
- **Queue naming**: `<service>:<event>:process`
- Domain services publish via `this.rabbitMQService.publish('publicationName', data)`.
- AMQP subscribers live in `src/application/amqp/`.
