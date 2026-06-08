# Spec — [FEATURE NAME]

**Feature**: `[###-feature-name]`
**Created**: [DATE]
**Status**: `draft` | `in-review` | `approved`
**Phase**: `SPECIFY`
**Owner**: [Name]
**Jira**: [EPIC-KEY]

> **Discovery**: `specs/[###-feature-name]/discovery.md` *(read before editing this spec)*
> **ADRs**: `specs/[###-feature-name]/adrs/` *(decisions made during design)*

---

## 1. Executive summary

[2-4 sentences. What problem does this feature solve for the user? What is the core mechanism (not implementation)?]

---

## 2. Scope

### In scope
- [What this feature covers]

### Out of scope (explicit)
- [What this feature deliberately does NOT cover — be precise]

---

## 3. User Stories

<!--
  One US = one end-to-end testable slice. NOT split by layer (BE / FE).
  Priority: P1 = must-have MVP, P2 = important, P3 = nice-to-have.
  Each US must be independently deployable and demonstrable.
-->

#### US-01 — [Title] (P1)

**Tracker**: [JIRA-KEY]

**Context**: [2-3 sentences. Why does this US exist? What problem does it solve?]

**Goal**: As a [role], I want [action], so that [outcome].

**Acceptance criteria**:
1. Given [state], when [action], then [outcome]
2. Given [state], when [action], then [outcome]

**Example**: [Optional — concrete scenario with names/dates that illustrates the AC]

<!-- internal-only -->
**Technical notes**:
- **FRs covered**: FR-001, FR-002
- **Out of scope for this US**: [...]
<!-- /internal-only -->

---

#### US-02 — [Title] (P2)

**Tracker**: [JIRA-KEY]

**Context**: [...]

**Goal**: As a [role], I want [action], so that [outcome].

**Acceptance criteria**:
1. Given [state], when [action], then [outcome]

<!-- internal-only -->
**Technical notes**:
- **FRs covered**: FR-003
- **Blocked by**: US-01
<!-- /internal-only -->

---

## 4. Functional requirements

- **FR-001**: [System MUST / Users MUST BE ABLE TO — testable, no implementation detail]
- **FR-002**: [...]
- **FR-003**: [...]

*Mark unclear requirements: `[NEEDS CLARIFICATION: specific question]` — max 3 total.*

## 5. Key entities

<!-- Only if feature involves data. Conceptual, not schema. -->

| Entity | Represents | Key attributes | Lifecycle |
|--------|-----------|----------------|-----------|
| [Name] | [What it models] | [fields] | [created/closed/archived...] |

## 6. Edge cases & error handling

- When [boundary condition] → [expected behavior]
- When [error condition] → [user-visible outcome, not HTTP status]

## 7. Non-functional requirements

| Attribute | Requirement | Notes |
|-----------|------------|-------|
| Performance | [e.g., "List loads in < 2s for 10k records"] | |
| Availability | [e.g., "Same SLA as parent service"] | |
| Security | [Auth required, roles] | |

## 8. Success criteria

- **SC-001**: [Measurable, technology-agnostic outcome]
- **SC-002**: [...]

## 9. Compliance & data (Afianza)

### 9.1 Personal data (PII / RGPD)

- **Fields entering/leaving**: [specific fields — e.g., NIF, email — or "none"]
- **RGPD category**: [basic / fiscal / financial / special Art.9 / none]
- **Legal basis**: [contract / legal obligation / legitimate interest / consent]
- **Retention**: [how long and why]
- **Access**: [which roles can read this data]

### 9.2 Auth surface

- **Emits, validates, or consumes tokens?**: [yes/no]
- **IDP**: [Entra External / Entra Internal / IDP adapter / N/A]
- **New or modified scopes/claims**: [list or N/A]
- **Endpoints changing auth status**: [list or N/A]

### 9.3 Cross-service data (RabbitMQ)

- **Messages published**: [routing key + payload summary — N/A if none]
- **Messages consumed**: [routing key + source service — N/A if none]
- **PII in payload**: [yes/no — if yes, justify why not referencing by ID]

### 9.4 External integrations

- [ ] **AEAT** — [operations]
- [ ] **Sage** — [operations]
- [ ] **Microsoft Graph / Azure AD** — [scopes]
- [ ] **HubSpot** — [operations]
- [ ] **Jira** — [projects / issue types]
- [ ] **None**

## 10. Assumptions

- [Assumption 1 — state what we're assuming and its implication]
- [Assumption 2]

## 11. Open questions

<!-- Unresolved items for PO or team. Remove when answered. -->

| # | Question | Owner | Status |
|---|----------|-------|--------|
| OQ-01 | [Question] | [PO/Tech] | open |

## 12. Clarifications log

<!-- Auto-populated by /prism-clarify. Do not edit manually. -->

### Session [DATE]

- Q: [...] → A: [...]
