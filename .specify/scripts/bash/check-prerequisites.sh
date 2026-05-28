#!/usr/bin/env bash
#
# check-prerequisites.sh — resolve feature paths + list available design docs.
#
# Flags:
#   --json            Output JSON (default: human-readable lines)
#   --paths-only      Only output FEATURE_DIR / FEATURE_SPEC / BRANCH (skip AVAILABLE_DOCS scan)
#   --require-tasks   Fail with non-zero exit if tasks.md does not exist
#   --include-tasks   Include tasks.md in AVAILABLE_DOCS / TASKS output (default: excluded)
#   -h, --help        Show this help
#
# Used by: speckit-clarify, speckit-analyze, speckit-checklist, speckit-implement,
# speckit-tasks, speckit-taskstoissues, speckit-git-pr-create, speckit-atlassian-sync-push.

set -e

JSON_MODE=false
PATHS_ONLY=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false

for arg in "$@"; do
    case "$arg" in
        --json)           JSON_MODE=true ;;
        --paths-only)     PATHS_ONLY=true ;;
        --require-tasks)  REQUIRE_TASKS=true ;;
        --include-tasks)  INCLUDE_TASKS=true ;;
        --help|-h)
            sed -n '2,15p' "$0"
            exit 0
            ;;
        *) ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

_paths_output=$(get_feature_paths) || {
    echo "ERROR: Failed to resolve feature paths" >&2
    exit 1
}
eval "$_paths_output"
unset _paths_output

# If feature.json pins an existing feature dir, branch naming is not required.
if ! feature_json_matches_feature_dir "$REPO_ROOT" "$FEATURE_DIR"; then
    check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1
fi

if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /speckit-specify first." >&2
    exit 1
fi

if [[ ! -f "$FEATURE_SPEC" ]]; then
    echo "ERROR: spec.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit-specify first." >&2
    exit 1
fi

TASKS_FILE="$FEATURE_DIR/tasks.md"
if $REQUIRE_TASKS && [[ ! -f "$TASKS_FILE" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit-tasks first." >&2
    exit 1
fi

# Build AVAILABLE_DOCS list (unless --paths-only)
AVAILABLE_DOCS=()
if ! $PATHS_ONLY; then
    [[ -f "$FEATURE_DIR/plan.md" ]]        && AVAILABLE_DOCS+=("plan.md")
    [[ -f "$FEATURE_DIR/research.md" ]]    && AVAILABLE_DOCS+=("research.md")
    [[ -f "$FEATURE_DIR/data-model.md" ]]  && AVAILABLE_DOCS+=("data-model.md")
    [[ -f "$FEATURE_DIR/quickstart.md" ]]  && AVAILABLE_DOCS+=("quickstart.md")
    if [[ -d "$FEATURE_DIR/contracts" ]] && [[ -n "$(ls -A "$FEATURE_DIR/contracts" 2>/dev/null)" ]]; then
        AVAILABLE_DOCS+=("contracts/")
    fi
    if [[ -d "$FEATURE_DIR/checklists" ]] && [[ -n "$(ls -A "$FEATURE_DIR/checklists" 2>/dev/null)" ]]; then
        AVAILABLE_DOCS+=("checklists/")
    fi
    if $INCLUDE_TASKS && [[ -f "$TASKS_FILE" ]]; then
        AVAILABLE_DOCS+=("tasks.md")
    fi
fi

if $JSON_MODE; then
    if has_jq; then
        jq_args=(
            --arg feature_spec "$FEATURE_SPEC"
            --arg feature_dir  "$FEATURE_DIR"
            --arg impl_plan    "$FEATURE_DIR/plan.md"
            --arg tasks        "$TASKS_FILE"
            --arg branch       "$CURRENT_BRANCH"
            --arg has_git      "$HAS_GIT"
        )
        if $PATHS_ONLY; then
            jq -cn "${jq_args[@]}" \
                '{FEATURE_DIR:$feature_dir,FEATURE_SPEC:$feature_spec,IMPL_PLAN:$impl_plan,TASKS:$tasks,BRANCH:$branch,HAS_GIT:$has_git}'
        else
            docs_json=$(printf '%s\n' "${AVAILABLE_DOCS[@]}" | jq -R . | jq -cs .)
            jq -cn --argjson docs "$docs_json" "${jq_args[@]}" \
                '{FEATURE_DIR:$feature_dir,FEATURE_SPEC:$feature_spec,IMPL_PLAN:$impl_plan,TASKS:$tasks,BRANCH:$branch,HAS_GIT:$has_git,AVAILABLE_DOCS:$docs}'
        fi
    else
        # jq fallback
        esc() { json_escape "$1"; }
        if $PATHS_ONLY; then
            printf '{"FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
                "$(esc "$FEATURE_DIR")" "$(esc "$FEATURE_SPEC")" "$(esc "$FEATURE_DIR/plan.md")" "$(esc "$TASKS_FILE")" "$(esc "$CURRENT_BRANCH")" "$(esc "$HAS_GIT")"
        else
            docs_csv=""
            for d in "${AVAILABLE_DOCS[@]}"; do
                docs_csv+="\"$(esc "$d")\","
            done
            docs_csv="[${docs_csv%,}]"
            printf '{"FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s","BRANCH":"%s","HAS_GIT":"%s","AVAILABLE_DOCS":%s}\n' \
                "$(esc "$FEATURE_DIR")" "$(esc "$FEATURE_SPEC")" "$(esc "$FEATURE_DIR/plan.md")" "$(esc "$TASKS_FILE")" "$(esc "$CURRENT_BRANCH")" "$(esc "$HAS_GIT")" "$docs_csv"
        fi
    fi
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $FEATURE_DIR/plan.md"
    echo "TASKS: $TASKS_FILE"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
    if ! $PATHS_ONLY; then
        echo "AVAILABLE_DOCS:"
        for d in "${AVAILABLE_DOCS[@]}"; do echo "  - $d"; done
    fi
fi
