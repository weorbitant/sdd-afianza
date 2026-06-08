export const meta = {
  name: 'extract-use-cases',
  description: 'Extract detailed use cases from a User Story / spec.md (actor, preconditions, main flow, alternative flows, postconditions, edge cases) and write use-cases.md next to the spec.',
  whenToUse: 'Run after a spec.md exists for a feature and you need a use-case-level decomposition (richer than user stories, ready for test design or POC scoping).',
  phases: [
    { title: 'Discover', detail: 'Read spec.md and enumerate candidate use cases (actor + goal)' },
    { title: 'Develop', detail: 'For each UC: develop in full detail in parallel' },
    { title: 'Review', detail: 'Adversarial completeness review per UC (missing edges, ambiguous steps)' },
    { title: 'Synthesize', detail: 'Merge into a single use-cases.md alongside the spec' },
  ],
}

// ---------- args ----------
const specPath = (args && args.specPath) || 'specs/001-client-team-assignments/spec.md'
const outputPath = (args && args.outputPath) || specPath.replace(/spec\.md$/, 'use-cases.md')

// ---------- schemas ----------
const CANDIDATES_SCHEMA = {
  type: 'object',
  required: ['featureSummary', 'useCases'],
  properties: {
    featureSummary: { type: 'string' },
    useCases: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'object',
        required: ['id', 'name', 'actor', 'goal'],
        properties: {
          id: { type: 'string', description: 'UC-01, UC-02, ...' },
          name: { type: 'string' },
          actor: { type: 'string' },
          goal: { type: 'string' },
          trigger: { type: 'string' },
          priority: { type: 'string', enum: ['must', 'should', 'could'] },
        },
      },
    },
  },
}

const UC_DETAIL_SCHEMA = {
  type: 'object',
  required: ['id', 'name', 'actor', 'goal', 'preconditions', 'mainFlow', 'alternativeFlows', 'postconditions', 'edgeCases'],
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    actor: { type: 'string' },
    secondaryActors: { type: 'array', items: { type: 'string' } },
    goal: { type: 'string' },
    trigger: { type: 'string' },
    preconditions: { type: 'array', items: { type: 'string' } },
    mainFlow: {
      type: 'array',
      minItems: 2,
      items: {
        type: 'object',
        required: ['step', 'action'],
        properties: {
          step: { type: 'integer' },
          action: { type: 'string' },
        },
      },
    },
    alternativeFlows: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'trigger', 'steps'],
        properties: {
          id: { type: 'string', description: 'e.g. 3a, 3b' },
          trigger: { type: 'string' },
          steps: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    postconditions: { type: 'array', items: { type: 'string' } },
    edgeCases: {
      type: 'array',
      items: {
        type: 'object',
        required: ['title', 'description'],
        properties: {
          title: { type: 'string' },
          description: { type: 'string' },
          expected: { type: 'string' },
        },
      },
    },
    openQuestions: { type: 'array', items: { type: 'string' } },
    relatedRequirements: { type: 'array', items: { type: 'string' }, description: 'FR-IDs or section refs from spec.md' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['complete', 'gaps'],
  properties: {
    complete: { type: 'boolean' },
    gaps: { type: 'array', items: { type: 'string' } },
    suggestedAdditions: {
      type: 'object',
      properties: {
        edgeCases: { type: 'array', items: { type: 'string' } },
        alternativeFlows: { type: 'array', items: { type: 'string' } },
        preconditions: { type: 'array', items: { type: 'string' } },
      },
    },
  },
}

// ---------- phase 1: discover ----------
phase('Discover')
log(`Reading spec at ${specPath}`)

const candidates = await agent(
  `Read the spec at \`${specPath}\` (use the Read tool on the absolute path if needed). Enumerate ALL distinct use cases implied by the user stories, functional requirements, and acceptance criteria.

A use case = a goal an actor wants to achieve through one interaction with the system. Be exhaustive:
- One UC per (actor, goal) pair. Same actor with different goals = separate UCs.
- Include cross-service / AMQP-triggered UCs if the spec mentions event propagation.
- Include admin / configuration UCs, not just happy-path user flows.
- Number them UC-01, UC-02, ...

IMPORTANT: You MUST call the StructuredOutput tool with your result. Do NOT write JSON as plain text.`,
  { schema: CANDIDATES_SCHEMA, label: 'discover-ucs', model: 'sonnet' }
)

log(`Found ${candidates.useCases.length} candidate use cases`)

// ---------- phases 2 + 3: develop each UC, then verify, in a pipeline ----------
const developed = await pipeline(
  candidates.useCases,
  (uc) =>
    agent(
      `Develop use case ${uc.id} "${uc.name}" in full detail. Source spec: \`${specPath}\` — re-read whatever sections you need.

Use case seed:
- Actor: ${uc.actor}
- Goal: ${uc.goal}
- Trigger: ${uc.trigger || '(infer from spec)'}

Produce:
- preconditions (system + data state required before the UC starts)
- mainFlow (numbered steps, actor↔system alternating; be concrete, not abstract)
- alternativeFlows (named 3a, 5b, ... — each tied to a step in mainFlow)
- postconditions (what is true after success; include side effects like events published)
- edgeCases (concurrency, partial failures, permission edges, data drift across services per polyrepo-cross-service rule)
- openQuestions (anything the spec doesn't pin down)
- relatedRequirements (FR-IDs from spec.md if visible)

Keep id="${uc.id}" and name="${uc.name}".

IMPORTANT: You MUST call the StructuredOutput tool with your result. Do NOT write JSON as plain text.`,
      { schema: UC_DETAIL_SCHEMA, label: `develop:${uc.id}`, phase: 'Develop', model: 'sonnet' }
    ),
  (detail, _orig, idx) =>
    agent(
      `Adversarially review this use case for completeness. Default to complete=false if you find ANY meaningful gap.

Use case:
\`\`\`json
${JSON.stringify(detail, null, 2)}
\`\`\`

Check for:
- Missing alternative flows (auth failure, validation failure, concurrent edit, network partition)
- Missing edge cases (cross-service propagation, AMQP delivery failure, partial state)
- Vague steps ("system processes the request" — too abstract)
- Postconditions that don't mention side effects (events, audit logs)
- Preconditions that assume undocumented state

IMPORTANT: You MUST call the StructuredOutput tool with your result. Do NOT write JSON as plain text.`,
      { schema: VERDICT_SCHEMA, label: `review:${detail.id}`, phase: 'Review', model: 'sonnet' }
    ).then((verdict) => ({ ...detail, _review: verdict, _index: idx }))
)

const clean = developed.filter(Boolean)
log(`Developed and reviewed ${clean.length}/${candidates.useCases.length} use cases`)

// ---------- phase 4: synthesize markdown ----------
phase('Synthesize')

const renderUC = (uc) => {
  const lines = []
  lines.push(`## ${uc.id} · ${uc.name}`)
  lines.push('')
  lines.push(`- **Actor primario:** ${uc.actor}`)
  if (uc.secondaryActors?.length) lines.push(`- **Actores secundarios:** ${uc.secondaryActors.join(', ')}`)
  lines.push(`- **Objetivo:** ${uc.goal}`)
  if (uc.trigger) lines.push(`- **Trigger:** ${uc.trigger}`)
  if (uc.relatedRequirements?.length) lines.push(`- **Requisitos relacionados:** ${uc.relatedRequirements.join(', ')}`)
  lines.push('')
  lines.push('### Precondiciones')
  uc.preconditions.forEach((p) => lines.push(`- ${p}`))
  lines.push('')
  lines.push('### Flujo principal')
  uc.mainFlow.forEach((s) => lines.push(`${s.step}. ${s.action}`))
  lines.push('')
  if (uc.alternativeFlows?.length) {
    lines.push('### Flujos alternativos')
    uc.alternativeFlows.forEach((af) => {
      lines.push(`**${af.id}** — ${af.trigger}`)
      af.steps.forEach((st, i) => lines.push(`  ${i + 1}. ${st}`))
      lines.push('')
    })
  }
  lines.push('### Postcondiciones')
  uc.postconditions.forEach((p) => lines.push(`- ${p}`))
  lines.push('')
  if (uc.edgeCases?.length) {
    lines.push('### Edge cases')
    uc.edgeCases.forEach((e) => {
      lines.push(`- **${e.title}** — ${e.description}${e.expected ? ` _(esperado: ${e.expected})_` : ''}`)
    })
    lines.push('')
  }
  if (uc.openQuestions?.length) {
    lines.push('### Preguntas abiertas')
    uc.openQuestions.forEach((q) => lines.push(`- ${q}`))
    lines.push('')
  }
  if (uc._review && !uc._review.complete && uc._review.gaps?.length) {
    lines.push('> **Revisión adversarial — gaps detectados:**')
    uc._review.gaps.forEach((g) => lines.push(`> - ${g}`))
    lines.push('')
  }
  return lines.join('\n')
}

const tocLines = clean.map((uc) => `- [${uc.id} · ${uc.name}](#${uc.id.toLowerCase()}-${uc.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')})`)

const markdown = [
  '# Use Cases',
  '',
  `**Spec fuente:** \`${specPath}\``,
  '',
  '## Resumen',
  '',
  candidates.featureSummary,
  '',
  '## Índice',
  '',
  ...tocLines,
  '',
  '---',
  '',
  ...clean.map(renderUC),
].join('\n')

const writer = await agent(
  `Write the following markdown to the absolute path \`${outputPath}\`. Use the Write tool. Then return the JSON {"written": true, "path": "${outputPath}", "useCaseCount": ${clean.length}}.

---BEGIN MARKDOWN---
${markdown}
---END MARKDOWN---`,
  {
    schema: {
      type: 'object',
      required: ['written', 'path', 'useCaseCount'],
      properties: {
        written: { type: 'boolean' },
        path: { type: 'string' },
        useCaseCount: { type: 'integer' },
      },
    },
    label: 'write-output',
    model: 'sonnet',
  }
)

return {
  spec: specPath,
  output: writer.path,
  useCaseCount: clean.length,
  gapsFound: clean.filter((u) => u._review && !u._review.complete).length,
}
