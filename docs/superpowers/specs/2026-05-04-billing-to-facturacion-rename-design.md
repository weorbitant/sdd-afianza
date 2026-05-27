# Design: Rename erpType value 'billing' → 'facturacion'

**Jira:** DEVPT-258  
**Date:** 2026-05-04  
**Services affected:** `pgi-service-pgi-api`, `pgi-app-pgi-web`

## Context

The `erpType` field on `client_erp_ref` records can hold the string value `'billing'`, produced by `getErpType()` in `@afianza-ac/lib-core-definitions` when the ERP application is `SAGE_GESTION`. This English technical identifier leaks into the domain. The ticket asks to store `'facturacion'` instead, aligning with the Spanish business domain.

`pd-service-data-factory` is the publisher and is not changing. The value `'billing'` will keep arriving in RabbitMQ messages. `pgi-service-pgi-api` owns the transformation at ingest time.

## Data Flow

```
data-factory → RabbitMQ (erpType: 'billing')
  → client-subscriber.ts (TRANSFORM: 'billing' → 'facturacion')
    → clients.service.ts (persists 'facturacion')
      → DB: client_erp_ref.erp_type = 'facturacion'
```

## Changes

### 1. Transform at subscriber boundary — `pgi-service-pgi-api`

**File:** `src/application/amqp/client-subscriber/client-subscriber.ts`

In both `handleClientPersisted` calls (create and update), map the `erpRef` array before passing to the domain service:

```typescript
erpRef: (clientDto.erpRef || []).map(ref => ({
  ...ref,
  erpType: ref.erpType === 'billing' ? 'facturacion' : ref.erpType,
})),
```

This sits at the application→domain boundary, consistent with the architecture rule that DTOs are mapped before reaching domain services.

### 2. DB migration — `pgi-service-pgi-api`

A MikroORM raw migration to update existing rows:

```sql
UPDATE client_erp_ref SET erp_type = 'facturacion' WHERE erp_type = 'billing';
```

Safety net for existing data regardless of whether data-factory re-syncs clients.

### 3. Frontend display mapping — `pgi-app-pgi-web`

**File:** `src/shared/mappings/erp-values.ts` line 9

```typescript
// Before
{ value: 'billing', displayName: 'Facturador' }

// After
{ value: 'facturacion', displayName: 'Facturador' }
```

### 4. Tests

**`client-subscriber.spec.ts`:**
- Input data keeps `erpType: 'billing'` (reflects what RabbitMQ sends)
- Assertions on persisted value change to `erpType: 'facturacion'` (verifies the transform)

**`clients.controller.spec.ts`:**
- Mock data updated to `erpType: 'facturacion'` (reflects post-migration stored value)

## What does NOT change

- `pd-service-data-factory` — no changes
- `@afianza-ac/lib-core-definitions` — no changes
- `ContactType 'billing'` in the frontend (`client-contact.ts`) — unrelated concept
- Contact sorting utility (`sort-client-contacts-info.utils.ts`) — unrelated concept
