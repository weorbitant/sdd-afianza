---
name: k8s-services
description: Use when the user asks to "ver servicios", "check services", "pod status", "estado del cluster", "qué está corriendo", "ver pods", or "cluster status" in the Afianza Kubernetes clusters. SKIP for log analysis (use ops-suite:service-logs) or database queries.
allowed-tools: Bash AskUserQuestion
metadata:
  argument-hint: "[namespace] [service-name]"
---

# Afianza Cluster — Service Status

## Clusters and namespaces

| Context | Cluster | Namespaces |
|---|---|---|
| `k8s-afianza-dev` | Azure dev (new) | `pgi`, `plataforma-datos`, `portal-cliente`, `broker` |
| `dev` | vCluster dev (old) | `plataformadato` |
| `afianza-prod` | Production | `pgi`, `plataforma-datos`, `portal-cliente`, `broker` |

## Step 1 — Determine target

If `$ARGUMENTS` contains a context or environment name, use it. Otherwise default to current context (`kubectl config current-context`).

If `$ARGUMENTS` contains a namespace or service name, scope to it. Otherwise show all relevant namespaces.

## Step 2 — Show overview

Run in order:

```bash
# Resolve context (use $ARGUMENTS value if specified, else current)
KCTX=$(kubectl config current-context)

# Pods across relevant namespaces
kubectl --context "$KCTX" get pods -n pgi
kubectl --context "$KCTX" get pods -n plataforma-datos
kubectl --context "$KCTX" get pods -n portal-cliente
kubectl --context "$KCTX" get pods -n broker
```

If a specific namespace or service was requested, only run that query.

## Step 3 — Highlight issues

Identify pods that are NOT in `Running` or `Completed` state:
- `CrashLoopBackOff` — application error, suggest checking logs with `ops-suite:service-logs`
- `ImagePullBackOff` — wrong image tag or registry auth issue
- `Pending` — scheduling problem (node resources or tolerations)
- `OOMKilled` — memory limit exceeded
- High restart count (>3) — instability warning

## Step 4 — Output format

```
Context: k8s-afianza-dev

namespace: pgi
NAME                                    READY   STATUS    RESTARTS   AGE
pgi-service-pgi-api-xxxx-yyyy           1/1     Running   0          2d
...

namespace: plataforma-datos
...

Issues:
  - pod X in namespace Y: CrashLoopBackOff — run /ops-suite:service-logs X dev
```

If no issues found, print "All pods healthy ✓".
