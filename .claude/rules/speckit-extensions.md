---
paths:
  - ".specify/extensions/**"
  - ".claude/skills/speckit-**"
---

# Trabajar con extensiones de Spec-Kit

Las extensiones locales viven en **`.specify/extensions/<name>/`** (in-place, versionadas en git). Cada una tiene:

```
.specify/extensions/<name>/
├── extension.yml                 # manifiesto (id, version, commands)
├── commands/speckit.<name>.md    # comando real (lo que ejecuta el LLM)
└── agents/*.md                   # opcional — prompts para sub-agents que invoque el comando
```

Cuando Spec-Kit instala una extensión genera **dos artefactos adicionales** que NO se editan a mano:

1. **Binding skill** en `.claude/skills/speckit-<command>/SKILL.md` — Claude Code descubre el slash command leyendo esto.
2. **Entrada en `.specify/extensions/.registry`** — el CLI de Spec-Kit la usa para `list/update/remove`.

## Crear una extensión nueva

1. **Editar in-place** en `.specify/extensions/<new-name>/` siguiendo el layout. Mira `atlassian-sync/` como referencia.
2. **NUNCA** ejecutar `specify extension add .specify/extensions/<new-name> --dev` — el CLI hace `rmtree(dest)` antes del copytree y borra los ficheros cuando source == dest. Bug conocido.
3. **Registrar manualmente** (lo que el CLI haría):
   ```bash
   # 1. Generar el binding skill
   mkdir -p .claude/skills/speckit-<command>
   cat > .claude/skills/speckit-<command>/SKILL.md <<HEADER
   ---
   name: speckit-<command>
   description: "<copy from extension.yml>"
   argument-hint: "<args hint>"
   compatibility: Requires spec-kit project structure with .specify/ directory
   metadata:
     author: afianza-local
     source: <name>:commands/speckit.<command>.md
   user-invocable: true
   ---
   HEADER
   tail -n +6 .specify/extensions/<name>/commands/speckit.<command>.md >> .claude/skills/speckit-<command>/SKILL.md

   # 2. Calcular manifest_hash y añadir entrada a .specify/extensions/.registry
   shasum -a 256 .specify/extensions/<name>/extension.yml

   # 3. Añadir <name> a .specify/extensions.yml > installed:
   ```

## Editar una extensión existente

- **Edita directamente** los ficheros en `.specify/extensions/<name>/`.
- **Si el cambio es solo en `commands/speckit.<command>.md`**: regenera el binding (paso 1 de arriba — `tail` + heredoc).
- **Si el cambio es en `extension.yml`**: regenera `manifest_hash` (paso 2) y actualiza la entrada en `.registry`.
- **Si el cambio es solo en `agents/*.md`**: el comando los lee en runtime, no requiere regeneración del binding.

## Comandos útiles del CLI

```bash
specify extension list                   # ver instaladas — útil para verificar manifest_hash
specify extension info <name>            # detalle de una extensión
specify extension disable <name>         # desactivar sin borrar (útil para A/B testing)
specify extension enable <name>          # re-activar
# Evitar: `add`, `update`, `remove` sobre extensiones in-place — el CLI no espera ese layout
```

## Diferencia entre commands, skills y presets

- **Spec-Kit command** (`.specify/extensions/<ext>/commands/*.md`) — fuente de verdad del slash command.
- **Claude Code skill** (`.claude/skills/<name>/SKILL.md`) — binding que Claude Code lee para exponer el `/<name>`. Auto-generado por el CLI, regenerable a mano.
- **Spec-Kit preset** (`.specify/presets/<name>/`) — paquete que **sobrescribe templates** base (`spec-template.md`, `plan-template.md`, etc.). NO contiene lógica ejecutable, solo modifica el formato de los artefactos generados.

Regla: nuevo comportamiento ejecutable → extensión. Cambio de formato en spec/plan/tasks → preset.
