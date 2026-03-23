#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bootstrap_task_driven_project.sh TARGET_DIR [options]

Options:
  --project-name NAME       Override project name shown in generated docs
  --plan-path PATH          Plan file path written into generated docs
  --progress-file NAME      Progress filename to create (default: PROGRESS.md)
  --tasks-file NAME         Tasks filename to create (default: tasks.md)
  --dev-command CMD         Dev command written into AGENTS.md
  --build-command CMD       Build/verification command written into AGENTS.md
  --e2e-command CMD         Optional E2E command written into AGENTS.md
  --review-command CMD      Optional review command written into AGENTS.md
  --thesis TEXT             One-line product thesis
  --next-batch TEXT         Initial next batch text
  --force                   Overwrite existing files
  --help                    Show this help

Example:
  bootstrap_task_driven_project.sh /path/to/project \
    --project-name "My Project" \
    --plan-path "plans/mvp.md" \
    --progress-file "PROGRESS.md" \
    --tasks-file "tasks.md" \
    --dev-command "pnpm dev" \
    --build-command "pnpm build" \
    --e2e-command "pnpm exec playwright test" \
    --review-command "use review skill or manual review" \
    --thesis "One-line product thesis." \
    --next-batch "Highest-priority next implementation batch."
EOF
}

escape_replacement() {
  printf '%s' "$1" | sed -e 's/[\/&|]/\\&/g'
}

render_template() {
  local input_path="$1"
  local output_path="$2"

  local project_name_escaped
  local progress_file_escaped
  local tasks_file_escaped
  local plan_path_escaped
  local dev_command_escaped
  local build_command_escaped
  local e2e_command_escaped
  local review_command_escaped
  local thesis_escaped
  local next_batch_escaped
  local date_escaped

  project_name_escaped="$(escape_replacement "$PROJECT_NAME")"
  progress_file_escaped="$(escape_replacement "$PROGRESS_FILE")"
  tasks_file_escaped="$(escape_replacement "$TASKS_FILE")"
  plan_path_escaped="$(escape_replacement "$PLAN_PATH")"
  dev_command_escaped="$(escape_replacement "$DEV_COMMAND")"
  build_command_escaped="$(escape_replacement "$BUILD_COMMAND")"
  e2e_command_escaped="$(escape_replacement "$E2E_COMMAND")"
  review_command_escaped="$(escape_replacement "$REVIEW_COMMAND")"
  thesis_escaped="$(escape_replacement "$PROJECT_THESIS")"
  next_batch_escaped="$(escape_replacement "$NEXT_BATCH")"
  date_escaped="$(escape_replacement "$TODAY")"

  sed \
    -e "s|__PROJECT_NAME__|$project_name_escaped|g" \
    -e "s|__PROGRESS_FILE__|$progress_file_escaped|g" \
    -e "s|__TASKS_FILE__|$tasks_file_escaped|g" \
    -e "s|__PLAN_PATH__|$plan_path_escaped|g" \
    -e "s|__DEV_COMMAND__|$dev_command_escaped|g" \
    -e "s|__BUILD_COMMAND__|$build_command_escaped|g" \
    -e "s|__E2E_COMMAND__|$e2e_command_escaped|g" \
    -e "s|__REVIEW_COMMAND__|$review_command_escaped|g" \
    -e "s|__PROJECT_THESIS__|$thesis_escaped|g" \
    -e "s|__NEXT_BATCH__|$next_batch_escaped|g" \
    -e "s|__DATE__|$date_escaped|g" \
    "$input_path" > "$output_path"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

TARGET_DIR="$1"
shift

PROJECT_NAME=""
PROGRESS_FILE="PROGRESS.md"
TASKS_FILE="tasks.md"
PLAN_PATH="plans/mvp-architecture.md"
DEV_COMMAND="npm run dev"
BUILD_COMMAND="npm run build"
E2E_COMMAND="pnpm exec playwright test"
REVIEW_COMMAND="use review skill or manual review"
PROJECT_THESIS="Describe the product in one sentence."
NEXT_BATCH="Describe the highest-priority next implementation batch."
FORCE=0
TODAY="$(date +%F)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-name)
      PROJECT_NAME="${2:-}"
      shift 2
      ;;
    --plan-path)
      PLAN_PATH="${2:-}"
      shift 2
      ;;
    --progress-file)
      PROGRESS_FILE="${2:-}"
      shift 2
      ;;
    --tasks-file)
      TASKS_FILE="${2:-}"
      shift 2
      ;;
    --dev-command)
      DEV_COMMAND="${2:-}"
      shift 2
      ;;
    --build-command)
      BUILD_COMMAND="${2:-}"
      shift 2
      ;;
    --e2e-command)
      E2E_COMMAND="${2:-}"
      shift 2
      ;;
    --review-command)
      REVIEW_COMMAND="${2:-}"
      shift 2
      ;;
    --thesis)
      PROJECT_THESIS="${2:-}"
      shift 2
      ;;
    --next-batch)
      NEXT_BATCH="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$PROJECT_NAME" ]]; then
  PROJECT_NAME="$(basename "$TARGET_DIR")"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/../templates"

AGENTS_TEMPLATE="$TEMPLATE_DIR/AGENTS.md.tpl"
PROGRESS_TEMPLATE="$TEMPLATE_DIR/PROGRESS.md.tpl"
TASKS_TEMPLATE="$TEMPLATE_DIR/tasks.md.tpl"

if [[ ! -f "$AGENTS_TEMPLATE" || ! -f "$PROGRESS_TEMPLATE" || ! -f "$TASKS_TEMPLATE" ]]; then
  echo "Template files not found under $TEMPLATE_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

AGENTS_PATH="$TARGET_DIR/AGENTS.md"
PROGRESS_PATH="$TARGET_DIR/$PROGRESS_FILE"
TASKS_PATH="$TARGET_DIR/$TASKS_FILE"

if [[ "$FORCE" -ne 1 ]]; then
  for path in "$AGENTS_PATH" "$PROGRESS_PATH" "$TASKS_PATH"; do
    if [[ -e "$path" ]]; then
      echo "Refusing to overwrite existing $path. Re-run with --force if intended." >&2
      exit 1
    fi
  done
fi

render_template "$AGENTS_TEMPLATE" "$AGENTS_PATH"
render_template "$PROGRESS_TEMPLATE" "$PROGRESS_PATH"
render_template "$TASKS_TEMPLATE" "$TASKS_PATH"

echo "Created:"
echo "- $AGENTS_PATH"
echo "- $PROGRESS_PATH"
echo "- $TASKS_PATH"
